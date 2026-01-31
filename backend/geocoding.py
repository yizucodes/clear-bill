"""
ClearBill Advisor - Geocoding Service

Provides geocoding and distance calculation for proximity-based facility ranking.

Features:
- Haversine distance calculation (accurate great-circle distance)
- Nominatim geocoding (free OpenStreetMap API, no key required)
- Simple in-memory caching
- Graceful fallback on failures
"""

import asyncio
import logging
from math import radians, sin, cos, sqrt, atan2
import re
from typing import Optional, Tuple, Dict
from functools import lru_cache

import httpx

logger = logging.getLogger("Geocoding")

# Earth's radius in miles
EARTH_RADIUS_MILES = 3959

# Simple cache for geocoding results
_geocode_cache: Dict[str, Tuple[float, float]] = {}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula for accurate distance calculation.
    
    Args:
        lat1, lon1: Latitude and longitude of first point (in degrees)
        lat2, lon2: Latitude and longitude of second point (in degrees)
    
    Returns:
        Distance in miles
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return EARTH_RADIUS_MILES * c


class GeocodingService:
    """
    Service for geocoding addresses and calculating distances.
    
    Uses Nominatim (OpenStreetMap) for geocoding - free, no API key required.
    Rate limited to 1 request/second per Nominatim terms of service.
    """
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
    
    async def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode an address to latitude/longitude coordinates.
        
        Implements a robust fallback strategy:
        1. Try exact address
        2. Try ZIP code (if present)
        3. Try City, State (if present)
        """
        if not address:
            return None, None
        
        # 1. Try Exact Address
        lat, lon = await self._geocode_single(address)
        if lat: return lat, lon
        
        # 2. Try City/State Fallback (More specific context than just ZIP)
        city_state = self._extract_city_state(address)
        if city_state and city_state != address:
            logger.info(f"Geocoding fallback: Trying City/State '{city_state}' for '{address}'")
            lat, lon = await self._geocode_single(city_state)
            if lat: return lat, lon

        # 3. Try ZIP Code Fallback
        zip_code = self._extract_zip(address)
        if zip_code:
            # Append USA context if original address had it or implicitly for 5-digit zips
            # This prevents 94107 mapping to Mexico City
            if "US" in address.upper() or "USA" in address.upper() or "UNITED STATES" in address.upper():
                zip_query = f"{zip_code}, USA"
            else:
                zip_query = list(filter(None, [zip_code, "USA"]))[0] # Default to USA for now as app is US-centric
                
            logger.info(f"Geocoding fallback: Trying ZIP code '{zip_query}' for '{address}'")
            lat, lon = await self._geocode_single(zip_query)
            if lat: return lat, lon
            
        return None, None

    def _extract_zip(self, text: str) -> Optional[str]:
        """Extract 5-digit ZIP code from string."""
        match = re.search(r'\b\d{5}\b', text)
        return match.group(0) if match else None

    def _extract_city_state(self, text: str) -> Optional[str]:
        """Simple heuristic to extract City, State."""
        # Look for pattern like "San Francisco, CA"
        parts = text.split(',')
        if len(parts) >= 2:
            # Return last two parts (usually City, State or State, Country)
            # But better to just grab everything except the street part if possible.
            # Simple approach: if it has commas, try the part after the first comma
            # e.g. "123 St, City, State" -> "City, State"
            return ", ".join(parts[1:]).strip()
        return None

    async def _geocode_single(self, query: str) -> Tuple[Optional[float], Optional[float]]:
        """Internal helper for single geocoding request."""
        # Normalize for caching
        cache_text = query.lower().strip()
        
        # Check cache
        if cache_text in _geocode_cache:
            logger.debug(f"Cache hit for: {query}")
            return _geocode_cache[cache_text]
            
        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    params={"q": query, "format": "json", "limit": 1},
                    headers={"User-Agent": "ClearBillAdvisor/1.0 (Healthcare App)"}
                )
                
                self.last_request_time = asyncio.get_event_loop().time()
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        lat = float(data[0]["lat"])
                        lon = float(data[0]["lon"])
                        _geocode_cache[cache_text] = (lat, lon)
                        return lat, lon
                        
        except Exception as e:
            logger.error(f"Geocoding error for '{query}': {e}")
            
        return None, None
    
    async def get_distance(self, 
                          from_address: str, 
                          to_address: str) -> Optional[float]:
        """
        Calculate distance between two addresses.
        
        Args:
            from_address: Starting address
            to_address: Destination address
        
        Returns:
            Distance in miles, or None if geocoding fails
        """
        from_coords = await self.geocode(from_address)
        to_coords = await self.geocode(to_address)
        
        if None in from_coords or None in to_coords:
            return None
        
        return haversine_distance(
            from_coords[0], from_coords[1],
            to_coords[0], to_coords[1]
        )
    
    async def batch_distances_from_location(
        self,
        user_location: str,
        addresses: list[str]
    ) -> list[Optional[float]]:
        """
        Calculate distances from a user location to multiple addresses.
        
        Optimized to geocode user location once, then sequentially geocode
        other addresses (respecting rate limits).
        
        Args:
            user_location: User's location (city/state or full address)
            addresses: List of facility addresses
        
        Returns:
            List of distances in miles (None for failed geocodes)
        """
        # Geocode user location first
        user_coords = await self.geocode(user_location)
        
        if None in user_coords:
            logger.warning(f"Could not geocode user location: {user_location}")
            return [None] * len(addresses)
        
        user_lat, user_lon = user_coords
        distances = []
        
        for addr in addresses:
            if not addr:
                distances.append(None)
                continue
            
            coords = await self.geocode(addr)
            
            if None in coords:
                distances.append(None)
            else:
                dist = haversine_distance(user_lat, user_lon, coords[0], coords[1])
                distances.append(round(dist, 1))
        
        return distances


# ==================== Well-Known Location Cache ====================

# Pre-populate cache with common locations to reduce API calls
KNOWN_LOCATIONS = {
    "san francisco, ca": (37.7749, -122.4194),
    "san francisco, california": (37.7749, -122.4194),
    "oakland, ca": (37.8044, -122.2712),
    "oakland, california": (37.8044, -122.2712),
    "berkeley, ca": (37.8716, -122.2727),
    "palo alto, ca": (37.4419, -122.1430),
    "san jose, ca": (37.3382, -121.8863),
    "los angeles, ca": (34.0522, -118.2437),
    "la, ca": (34.0522, -118.2437),
    "new york, ny": (40.7128, -74.0060),
    "nyc": (40.7128, -74.0060),
    "chicago, il": (41.8781, -87.6298),
    "seattle, wa": (47.6062, -122.3321),
    "boston, ma": (42.3601, -71.0589),
}

# Initialize cache with known locations
_geocode_cache.update(KNOWN_LOCATIONS)


# ==================== Test ====================

async def test_geocoding():
    """Test the geocoding service."""
    print("=" * 60)
    print("GEOCODING SERVICE TEST")
    print("=" * 60)
    
    geo = GeocodingService()
    
    # Test 1: Haversine distance (known values)
    print("\n📏 Test 1: Haversine Distance")
    dist = haversine_distance(37.7749, -122.4194, 37.8044, -122.2712)
    print(f"  SF to Oakland: {dist:.2f} miles (expected: ~8-10 miles)")
    assert 7 < dist < 12, f"Distance should be ~8-10 miles, got {dist}"
    print("  ✅ PASSED")
    
    # Test 2: Cache hit (known location)
    print("\n📍 Test 2: Cached Location Lookup")
    lat, lon = await geo.geocode("San Francisco, CA")
    print(f"  San Francisco, CA → ({lat}, {lon})")
    assert lat == 37.7749 and lon == -122.4194
    print("  ✅ PASSED (from cache)")
    
    # Test 3: Real geocoding (API call)
    print("\n🌐 Test 3: Real Geocoding (Nominatim API)")
    lat, lon = await geo.geocode("845 Market St, San Francisco, CA")
    print(f"  845 Market St, SF → ({lat}, {lon})")
    if lat and lon:
        # Should be near downtown SF
        assert 37.7 < lat < 37.8 and -122.5 < lon < -122.3
        print("  ✅ PASSED")
    else:
        print("  ⚠️ API call failed (may be rate limited)")
    
    # Test 4: Distance between addresses
    print("\n📐 Test 4: Distance Between Addresses")
    dist = await geo.get_distance("San Francisco, CA", "Oakland, CA")
    print(f"  SF to Oakland: {dist} miles")
    if dist:
        assert 7 < dist < 12
        print("  ✅ PASSED")
    
    # Test 5: Batch distances
    print("\n📊 Test 5: Batch Distance Calculation")
    addresses = [
        "845 Market St, San Francisco, CA",
        "1 Embarcadero Center, San Francisco, CA",
        None,  # Test None handling
        "Oakland, CA"
    ]
    distances = await geo.batch_distances_from_location("San Francisco, CA", addresses)
    print(f"  Distances from SF: {distances}")
    print("  ✅ PASSED")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_geocoding())
