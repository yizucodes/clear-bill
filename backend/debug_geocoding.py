
import asyncio
from geocoding import GeocodingService

async def debug_address():
    geo = GeocodingService()
    address = "560 20th St, San Francisco, CA 94107, US"
    
    print(f"Testing address: '{address}'")
    lat, lon = await geo.geocode(address)
    print(f"Result: {lat}, {lon}")
    
    # Try cleaner version
    clean_address = "560 20th St, San Francisco, CA"
    print(f"Testing clean address: '{clean_address}'")
    lat2, lon2 = await geo.geocode(clean_address)
    print(f"Result: {lat2}, {lon2}")

    # Test Fallback Logic
    tricky_address = "99999 Nonexistent St, San Francisco, CA 94107, US"
    print(f"Testing tricky address (should fallback to ZIP): '{tricky_address}'")
    lat3, lon3 = await geo.geocode(tricky_address)
    print(f"Result: {lat3}, {lon3}")

if __name__ == "__main__":
    asyncio.run(debug_address())
