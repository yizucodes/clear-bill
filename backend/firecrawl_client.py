"""
ClearBill Advisor - Firecrawl Client
Multi-tier facility search using Firecrawl APIs.

Strategy:
1. Search for facilities AND pricing pages simultaneously
2. Match pricing data to facilities
3. Fall back to estimates with transparent confidence scores
"""

import os
import json
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

import httpx
from dotenv import load_dotenv

from geocoding import GeocodingService

# Load environment variables
load_dotenv()

logger = logging.getLogger("Firecrawl")
logging.basicConfig(level=logging.INFO)

# Configuration
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"

# Industry average pricing data (fallback)
INDUSTRY_AVERAGES = {
    "urgent_care_visit": 270,
    "xray": 180,
    "lab_work": 150,
    "stitches": 300,
    "splint": 200,
    "source": "Fair Health Consumer 2024 averages"
}

# Known pricing sources (pre-cached for demo speed)
KNOWN_PRICING = {
    "carbonhealth.com": {
        "urgent_care_visit": 225,
        "xray": 85,
        "virtual_visit": 99,
        "source": "Carbon Health website"
    },
    "onemedical.com": {
        "urgent_care_visit": 199,
        "xray": 150,
        "source": "One Medical website"
    }
}


class FirecrawlClient:
    """
    Multi-tier Firecrawl client for facility search and pricing extraction.
    
    Uses a smart approach:
    1. Search for facilities
    2. Search for pricing pages with scraping
    3. Extract pricing from scraped content
    4. Match pricing to facilities
    5. Fallback to estimates with transparency
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.base_url = FIRECRAWL_BASE_URL
        self.results_dir = Path(__file__).parent / "search_results"
        self.results_dir.mkdir(exist_ok=True)
        self.geocoding = GeocodingService()
        
        if not self.api_key:
            logger.warning("Firecrawl API key not configured, will use mock data")
    
    async def search_and_enrich(
        self,
        queries: List[str],
        location: str,
        expected_procedures: List[str],
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Multi-tier facility search with pricing enrichment.
        """
        timestamp = datetime.now().isoformat()
        result = {
            "timestamp": timestamp,
            "query": queries[0] if queries else "",
            "location": location,
            "phases": {},
            "facilities": [],
            "pricing_sources": [],
            "data_quality": "unknown",
            "data_quality": "unknown",
            "disclaimer": "",
            "verification_status": "skipped"
        }
        
        # CACHE CHECK: Look for existing file matching query/location
        cache_key = f"{queries[0]}_{location}".replace(" ", "_").lower()
        cached = self._get_cached_result(cache_key)
        if cached:
            logger.info(f"⚡️ CACHE HIT: Found existing results for {cache_key}")
            return cached

        # If no API key, return mock data
        if not self.api_key:
            logger.info("No API key, using mock facilities")
            result["facilities"] = self._mock_facilities(location)
            result["data_quality"] = "mock"
            self._save_results(result, "mock")
            return result
        
        # Run searches in parallel for speed
        logger.info(f"Starting parallel search for facilities and pricing in {location}")
        
        try:
            # Parallel execution: facility search + pricing page search
            facility_task = self._search_facilities(queries[0], location)
            pricing_task = self._search_pricing_pages(location)
            
            facility_results, pricing_results = await asyncio.gather(
                facility_task, 
                pricing_task,
                return_exceptions=True
            )
            
            # Handle facility search
            if isinstance(facility_results, Exception):
                logger.error(f"Facility search failed: {facility_results}")
                result["phases"]["facility_search"] = {"status": "failed", "error": str(facility_results)}
                facility_results = []
            else:
                result["phases"]["facility_search"] = {
                    "status": "success",
                    "count": len(facility_results)
                }
            
            # Handle pricing search
            if isinstance(pricing_results, Exception):
                logger.error(f"Pricing search failed: {pricing_results}")
                result["phases"]["pricing_search"] = {"status": "failed", "error": str(pricing_results)}
                pricing_results = []
            else:
                result["phases"]["pricing_search"] = {
                    "status": "success",
                    "count": len(pricing_results),
                    "sources": [p.get("url", "")[:50] for p in pricing_results]
                }
            
        except Exception as e:
            logger.error(f"Parallel search failed: {e}")
            result["facilities"] = self._mock_facilities(location)
            result["data_quality"] = "mock"
            self._save_results(result, "error")
            return result
        
        # If no facilities found, use mocks
        if not facility_results:
            logger.warning("No facilities found, using mocks")
            result["facilities"] = self._mock_facilities(location)
            result["data_quality"] = "mock"
            self._save_results(result, "no_facilities")
            return result
        
        # Rank and select top candidates
        ranked = await self._rank_by_heuristics(facility_results, location)
        top_candidates = ranked[:top_n]
        
        result["phases"]["ranking"] = {
            "total": len(facility_results),
            "selected": len(top_candidates)
        }
        
        # Build pricing lookup from scraped pricing pages
        pricing_lookup = self._build_pricing_lookup(pricing_results)
        result["pricing_sources"] = list(pricing_lookup.keys())
        
        # Enrich facilities with pricing
        enriched_facilities = []
        for candidate in top_candidates:
            enriched = self._enrich_with_pricing(candidate, pricing_lookup)
            enriched_facilities.append(enriched)
        
        
        # TIER 3: VERIFICATION
        # If the top candidate is good but lacks verified data, do a targeted extraction
        # This is the "High ROI" addition: Spending extra time/credits only on the winner
        if top_candidates and self.api_key:
            top = enriched_facilities[0]
            if top.get("confidence") != "high" and top.get("url"):
                logger.info(f"🔎 Verifying top candidate: {top['name']}")
                verified_data = await self._verify_top_candidate(top["url"])
                
                if verified_data:
                    # Update the top candidate with verified data
                    if verified_data.get("wait_time_minutes") is not None:
                        top["wait_time"] = f"{verified_data['wait_time_minutes']} min"
                        top["wait_time_source"] = "verified_live_agent"
                        top["wait_time_status"] = verified_data.get("wait_time_status")
                    
                    if verified_data.get("urgent_care_price"):
                        top["pricing"]["urgent_care_visit"] = verified_data["urgent_care_price"]
                        top["pricing_source"] = "verified_agent_extract"
                        top["confidence"] = "high"
                    
                    if verified_data.get("insurance_accepted"):
                        top["insurance_accepted"] = verified_data["insurance_accepted"]
                    
                    result["phases"]["verification"] = {"status": "success", "url": top["url"]}
                    logger.info(f"✅ Verified top candidate: {top['name']} - Wait: {top.get('wait_time')}")
                else:
                    result["phases"]["verification"] = {"status": "failed_or_empty"}
        
        result["facilities"] = enriched_facilities
        
        # Calculate data quality
        high_conf = sum(1 for f in enriched_facilities if f.get("confidence") == "high")
        if high_conf == len(enriched_facilities):
            result["data_quality"] = "high"
        elif high_conf > 0:
            result["data_quality"] = "mixed"
        else:
            result["data_quality"] = "estimated"
        
        result["disclaimer"] = self._get_disclaimer(result["data_quality"])
        
        # Save results
        self._save_results(result, "success")
        
        return result
    
    async def _search_facilities(self, query: str, location: str, limit: int = 10) -> List[Dict]:
        """Search for healthcare facilities, including known providers with pricing."""
        all_results = []
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Main query
            response = await client.post(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": f"{query} {location}",
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                all_results.extend(data.get("data", []))
            
            # Also search for known providers with pricing data
            known_providers = ["Carbon Health", "One Medical", "GoHealth"]
            for provider in known_providers:
                try:
                    resp = await client.post(
                        f"{self.base_url}/search",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "query": f"{provider} urgent care {location}",
                            "limit": 3
                        }
                    )
                    if resp.status_code == 200:
                        all_results.extend(resp.json().get("data", []))
                except:
                    pass  # Best effort
            
            # Deduplicate by URL
            seen_urls = set()
            unique_results = []
            for r in all_results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(r)
            
            logger.info(f"Facility search returned {len(unique_results)} unique results")
            
            # Transform to facility format
            facilities = []
            for r in unique_results:
                facility = {
                    "name": self._clean_title(r.get("title", "Unknown")),
                    "url": r.get("url", ""),
                    "snippet": r.get("description", "")[:300],
                    "address": self._extract_address(r.get("description", "")),
                }
                
                if self._is_valid_facility(facility):
                    facilities.append(facility)
            
            return facilities
    
    async def _search_pricing_pages(self, location: str, limit: int = 5) -> List[Dict]:
        """Search for pricing AND wait time pages and scrape their content."""
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": f"urgent care wait time current status price cost {location}",
                    "limit": limit,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Pricing search failed: {response.status_code}")
            
            data = response.json()
            results = data.get("data", [])
            
            logger.info(f"Pricing/wait-time search returned {len(results)} results with content")
            
            return [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "markdown": r.get("markdown", "")
                }
                for r in results
                if r.get("markdown")
            ]

    async def _verify_top_candidate(self, url: str) -> Optional[Dict]:
        """
        High-ROI Step: Perform targeted LLM extraction on the single best result.
        This gets us 'ground truth' data for the one facility that matters most.
        """
        schema = {
            "type": "object",
            "properties": {
                "wait_time_minutes": {"type": "integer", "description": "Current wait time in minutes if explicitly stated"},
                "wait_time_status": {"type": "string", "enum": ["Low", "Moderate", "High", "No Wait", "Unknown"]},
                "urgent_care_price": {"type": "integer", "description": "Cash price for a basic visit"},
                "insurance_accepted": {"type": "array", "items": {"type": "string"}},
                "services": {"type": "array", "items": {"type": "string"}}
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/scrape",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "url": url,
                        "formats": ["extract"],
                        "extract": {
                            "schema": schema,
                            "prompt": "Extract the current wait time, cash prices for visits, and insurance accepted. Look for 'Wait Time', 'Self-Pay', 'Pricing'. If no specific wait time, infer status."
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("extract")
                else:
                    logger.warning(f"Verification failed for {url}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return None
    
    def _build_pricing_lookup(self, pricing_pages: List[Dict]) -> Dict[str, Dict]:
        """Build a domain -> pricing + wait time lookup from scraped pages."""
        lookup = {}
        
        # Start with known pricing
        lookup.update(KNOWN_PRICING)
        
        # Extract pricing AND wait time from scraped pages
        for page in pricing_pages:
            url = page.get("url", "")
            domain = self._extract_domain(url)
            markdown = page.get("markdown", "")
            
            if not domain or not markdown:
                continue
            
            # Skip if we already have this domain
            if domain in lookup:
                continue
            
            facility_data = self._extract_facility_data(markdown)
            if facility_data:
                facility_data["source"] = f"Scraped from {domain}"
                facility_data["source_url"] = url
                lookup[domain] = facility_data
                logger.info(f"Extracted facility data from {domain}: {facility_data}")
        
        return lookup
    
    def _enrich_with_pricing(self, facility: Dict, pricing_lookup: Dict) -> Dict:
        """Add pricing AND wait time info to a facility based on lookup or estimates."""
        url = facility.get("url", "")
        domain = self._extract_domain(url)
        
        # Check if we have data for this domain
        if domain and domain in pricing_lookup:
            data = pricing_lookup[domain]
            enriched = {
                **facility,
                "pricing": {
                    "urgent_care_visit": data.get("urgent_care_visit"),
                    "xray": data.get("xray")
                },
                "pricing_source": data.get("source", "website"),
                "pricing_url": data.get("source_url"),
                "data_source": "scraped",
                "confidence": "high"
            }
            # Add wait time if found
            if data.get("wait_time_data"):
                enriched["wait_time"] = data["wait_time_data"].get("wait_time")
                enriched["wait_time_status"] = data["wait_time_data"].get("status")
                enriched["wait_time_source"] = "verified_live"
            else:
                enriched["wait_time"] = None
                enriched["wait_time_source"] = "not_found"
            return enriched
        
        # Check name-based matching (fuzzy)
        name_lower = facility.get("name", "").lower()
        for domain_key, data in pricing_lookup.items():
            # Carbon Health, One Medical, etc.
            brand = domain_key.replace(".com", "").replace(".org", "")
            if brand in name_lower or name_lower in brand:
                enriched = {
                    **facility,
                    "pricing": {
                        "urgent_care_visit": data.get("urgent_care_visit"),
                        "xray": data.get("xray")
                    },
                    "pricing_source": data.get("source", "matched"),
                    "data_source": "matched",
                    "confidence": "medium"
                }
                # Add wait time if found
                if data.get("wait_time_data"):
                    enriched["wait_time"] = data["wait_time_data"].get("wait_time")
                    enriched["wait_time_status"] = data["wait_time_data"].get("status")
                    enriched["wait_time_source"] = "verified_live"
                else:
                    enriched["wait_time"] = None
                    enriched["wait_time_source"] = "not_found"
                return enriched
        
        # Fallback to estimates
        return {
            **facility,
            "pricing": self._estimate_pricing(),
            "pricing_source": INDUSTRY_AVERAGES["source"],
            "data_source": "estimated",
            "confidence": "low",
            "wait_time": None,
            "wait_time_source": "not_available"
        }
    
    def _extract_facility_data(self, markdown: str) -> Optional[Dict]:
        """Extract pricing AND wait time data from markdown content."""
        result = {}
        
        # ===== PRICING PATTERNS =====
        pricing_patterns = [
            (r"(?:Urgent\s*Care\s*(?:Visit)?)[:\s]*\$(\d+)", "urgent_care_visit"),
            (r"(?:X-Ray|X Ray|Xray)[s]?[:\s]*\$(\d+)", "xray"),
            (r"(?:Virtual\s*(?:Urgent\s*Care|Visit))[:\s]*\$(\d+)", "virtual_visit"),
            (r"(?:Primary\s*Care\s*(?:Visit|Sick))[:\s]*\$(\d+)", "primary_care_visit"),
        ]
        
        for pattern, key in pricing_patterns:
            match = re.search(pattern, markdown, re.IGNORECASE)
            if match:
                try:
                    result[key] = int(match.group(1))
                except ValueError:
                    pass
        
        # ===== WAIT TIME PATTERNS =====
        wait_time_data = {}
        
        # Explicit wait times: "Wait time: 15 min", "Current wait: 30 minutes"
        wait_time_pattern = r"(?:wait\s*(?:time)?|current\s*wait)[:\s]*(\d+)\s*(?:min(?:utes?)?)"
        match = re.search(wait_time_pattern, markdown, re.IGNORECASE)
        if match:
            wait_time_data["wait_time"] = f"{match.group(1)} min"
            wait_time_data["wait_time_minutes"] = int(match.group(1))
        
        # Next available time: "Next available: 2:30 PM"
        next_available_pattern = r"(?:next\s*available)[:\s]*(\d{1,2}:\d{2}\s*[AP]M)"
        match = re.search(next_available_pattern, markdown, re.IGNORECASE)
        if match:
            wait_time_data["next_available"] = match.group(1)
        
        # Status indicators
        status_patterns = [
            (r"walk[\s-]*ins?\s+welcome", "Walk-ins welcome"),
            (r"on\s+schedule", "On schedule"),
            (r"high\s+volume", "High volume"),
            (r"no\s+wait", "No wait"),
            (r"short\s+wait", "Short wait"),
            (r"moderate\s+wait", "Moderate wait"),
            (r"long\s+wait", "Long wait"),
            (r"currently\s+busy", "Currently busy"),
            (r"low\s+wait", "Low wait"),
        ]
        
        for pattern, status_text in status_patterns:
            if re.search(pattern, markdown, re.IGNORECASE):
                wait_time_data["status"] = status_text
                break
        
        if wait_time_data:
            result["wait_time_data"] = wait_time_data
        
        return result if result else None
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain
        except:
            return None
    
    async def _rank_by_heuristics(self, facilities: List[Dict], location: str) -> List[Dict]:
        """Rank facilities by proximity and relevance."""
        logger.info(f"Ranking {len(facilities)} facilities for location: {location}")
        
        # 1. Calculate distances (batch)
        addresses = [f.get("address") for f in facilities]
        distances = await self.geocoding.batch_distances_from_location(location, addresses)
        
        scored = []
        for i, fac in enumerate(facilities):
            score = 0
            text = (fac.get("name", "") + " " + fac.get("snippet", "")).lower()
            
            # --- Distance Scoring ---
            dist = distances[i]
            fac["distance_miles"] = dist  # Add to facility object
            
            if dist is not None:
                if dist < 1.0: score += 15       # < 1 mile: Huge boost
                elif dist < 3.0: score += 10     # < 3 miles: Big boost
                elif dist < 5.0: score += 5      # < 5 miles: Moderate boost
                elif dist > 20.0: score -= 10    # > 20 miles: Penalty
            
            # --- Keyword Heuristics ---
            if "urgent care" in text: score += 5
            if "walk-in" in text: score += 3
            if "clinic" in text: score += 2
            if fac.get("address"): score += 3
            if "price" in text or "cost" in text: score += 2
            
            # Known quality providers
            url = fac.get("url", "").lower()
            if "carbonhealth" in url: score += 3
            if "onemedical" in url: score += 2
            
            # Negative
            if "article" in text or "blog" in text: score -= 10
            
            scored.append((score, fac))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [fac for _, fac in scored]
    
    def _is_valid_facility(self, facility: Dict) -> bool:
        """Check if result is a real facility."""
        url = facility.get("url", "").lower()
        name = facility.get("name", "").lower()
        
        skip = ["yelp", "healthgrades", "zocdoc", "news", "blog", "wiki", "reddit", "top 10", "best"]
        return not any(s in url or s in name for s in skip)
    
    def _clean_title(self, title: str) -> str:
        """Clean facility title."""
        title = re.sub(r'\s*[-|–]\s*(Yelp|Google|Reviews?).*$', '', title, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', title).strip()[:100]
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from text."""
        pattern = r'\d{1,5}\s+[A-Za-z0-9\s]+(?:St|Street|Ave|Avenue|Blvd|Dr|Way|Rd)[.,]?\s*[^,]+,\s*(?:CA|California)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).strip()[:150] if match else None
    
    def _estimate_pricing(self) -> Dict:
        """Return industry average pricing."""
        return {
            "urgent_care_visit": INDUSTRY_AVERAGES["urgent_care_visit"],
            "xray": INDUSTRY_AVERAGES["xray"],
            "source": INDUSTRY_AVERAGES["source"]
        }
    
    def _get_disclaimer(self, quality: str) -> str:
        """Generate disclaimer."""
        disclaimers = {
            "high": "Pricing from facility websites. Verify with your insurance.",
            "mixed": "Some prices from websites, some estimated. Call to verify.",
            "estimated": "Prices estimated from Fair Health 2024 averages. Call to verify."
        }
        return disclaimers.get(quality, disclaimers["estimated"])
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Check for most recent existing result matching the key."""
        try:
            # Look for files like search_20240131_..._success.json
            files = list(self.results_dir.glob("*.json"))
            
            # Filter for files possibly relevant to this query (simple heuristic)
            # In a real app we'd hash the query, but for hackathon this is fine
            matches = []
            for f in files:
                try:
                    data = json.loads(f.read_text())
                    # Check if query and location match loosely
                    if cache_key in f.name or (
                        data.get("location") and 
                        data.get("location").split(",")[0].lower() in cache_key
                    ):
                        matches.append((f.stat().st_mtime, data))
                except:
                    continue
            
            if matches:
                # Return most recent
                matches.sort(key=lambda x: x[0], reverse=True)
                return matches[0][1]
                
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        
        return None

    def _mock_facilities(self, location: str) -> List[Dict]:
        """Return mock facilities with realistic wait times."""
        return [
            {
                "name": "Carbon Health - Downtown SF",
                "address": "845 Market St, San Francisco, CA 94103",
                "url": "https://carbonhealth.com",
                "pricing": {"urgent_care_visit": 225, "xray": 85},
                "pricing_source": "Carbon Health website",
                "data_source": "mock",
                "confidence": "low",
                "wait_time": "15 min",
                "wait_time_status": "Walk-ins welcome",
                "wait_time_source": "mock"
            },
            {
                "name": "One Medical Urgent Care",
                "address": "1 Embarcadero Center, San Francisco, CA 94111",
                "url": "https://onemedical.com",
                "pricing": {"urgent_care_visit": 199, "xray": 150},
                "pricing_source": "One Medical website",
                "data_source": "mock",
                "confidence": "low",
                "wait_time": "No wait",
                "wait_time_status": "On schedule",
                "wait_time_source": "mock"
            },
            {
                "name": "GoHealth Urgent Care",
                "address": "2100 Van Ness Ave, San Francisco, CA 94109",
                "url": "https://gohealthuc.com",
                "pricing": {"urgent_care_visit": 280, "xray": 200},
                "pricing_source": "Estimated",
                "data_source": "mock",
                "confidence": "low",
                "wait_time": "45 min",
                "wait_time_status": "High volume",
                "wait_time_source": "mock"
            }
        ]
    
    def _save_results(self, result: Dict, tag: str = ""):
        """Save results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_{timestamp}_{tag}.json"
        filepath = self.results_dir / filename
        
        try:
            with open(filepath, "w") as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save: {e}")


# ==================== Convenience Functions ====================

async def search_facilities(query: str, location: str) -> Dict:
    """Simple interface for facility search."""
    client = FirecrawlClient()
    return await client.search_and_enrich(
        queries=[query],
        location=location,
        expected_procedures=["urgent care visit", "X-ray"]
    )


# ==================== Test ====================

async def test_firecrawl():
    """Test the Firecrawl client."""
    client = FirecrawlClient()
    
    print("=" * 60)
    print("FIRECRAWL MULTI-TIER SEARCH TEST")
    print("=" * 60)
    
    result = await client.search_and_enrich(
        queries=["urgent care ankle injury San Francisco"],
        location="San Francisco, CA",
        expected_procedures=["urgent care visit", "X-ray", "splint"]
    )
    
    print(f"\n📊 Data Quality: {result['data_quality']}")
    print(f"📝 Disclaimer: {result['disclaimer']}")
    print(f"💰 Pricing Sources Found: {len(result.get('pricing_sources', []))}")
    
    print("\n🏥 FACILITIES FOUND:")
    for i, f in enumerate(result["facilities"], 1):
        print(f"\n  {i}. {f['name']}")
        print(f"     URL: {f.get('url', 'N/A')[:60]}...")
        print(f"     📍 Distance: {f.get('distance_miles', 'N/A')} miles")
        print(f"     Pricing: ${f.get('pricing', {}).get('urgent_care_visit', '?')} visit, ${f.get('pricing', {}).get('xray', '?')} X-ray")
        print(f"     Source: {f.get('pricing_source', f.get('data_source', 'unknown'))}")
        print(f"     Confidence: {f.get('confidence', 'unknown')}")
    
    print("\n📁 Phases:")
    for phase, data in result.get("phases", {}).items():
        print(f"  - {phase}: {data.get('status', 'unknown')}")
    
    print(f"\n💾 Results saved to: backend/search_results/")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_firecrawl())
