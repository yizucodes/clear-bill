# ClearBill Advisor - Simplified Blueprint

> **Goal**: Build a working demo in ~5 hours that wins OpenRouter + Firecrawl prizes

---

## Architecture Overview

```
USER INPUT                          BACKEND                           OUTPUT
┌──────────────────┐    ┌────────────────────────────────┐    ┌──────────────────┐
│ Symptoms (text)  │    │                                │    │ Recommended      │
│ Location (text)  │───▶│ OpenRouter → Firecrawl → Rank │───▶│ Facility + Cost  │
│ Insurance (drop) │    │                                │    │ + Reasoning      │
└──────────────────┘    └────────────────────────────────┘    └──────────────────┘
```

**Flow:**
1. User enters symptoms + location + selects insurance plan
2. **Agent 1 (OpenRouter)**: Enriches symptoms → urgency + search queries
3. **Firecrawl /search**: Fast discovery of 10 facilities (5s)
4. **Quick Ranking**: Narrow to top 3 candidates by distance/rating
5. **Firecrawl /agent**: Autonomous deep dive on top 3 for REAL pricing (30s)
6. **Agent 2 (OpenRouter)**: Final ranking with real data → recommendation with reasoning
7. Display: Recommended facility + verified cost + alternatives

---

## Progress Tracker

```
[x] Step 1: Project Foundation (DONE)
[x] Step 2: Backend API Server (DONE)
[x] Step 3: OpenRouter Symptom Enricher (DONE)
[x] Step 4: Firecrawl Multi-Tier Search (DONE)
[x] Step 5: Ranking Agent + Orchestrator (DONE)
[x] Step 6: Frontend Integration (DONE)
[ ] Step 7: End-to-End Testing (MEDIUM - 20 min)
[ ] Step 8: Deployment (MEDIUM - 30 min)
    🎉 DEMO READY
```

**Total remaining: ~1.5 hours**

---

## Step 3: OpenRouter Symptom Enricher

### Goal
Take raw user symptoms and enrich them for better Firecrawl searches.

### Create: `backend/openrouter_client.py`

**SymptomEnricherAgent:**
- **Model**: Claude Haiku via OpenRouter (fast + cheap)
- **Input**: symptoms, location
- **Output**:
  ```json
  {
    "urgency": "moderate",
    "care_level": "urgent_care",
    "search_queries": [
      "urgent care ankle injury San Francisco",
      "walk-in clinic X-ray San Francisco"
    ],
    "expected_procedures": ["X-ray", "exam", "splint"],
    "keywords": ["orthopedic", "walk-in", "X-ray available"]
  }
  ```

**Prompt Template:**
```
You are a medical triage assistant. Analyze the symptoms and return JSON.

Symptoms: {symptoms}
Location: {location}

Return JSON with:
- urgency: "low" | "moderate" | "high" | "emergency"
- care_level: "primary_care" | "urgent_care" | "emergency_room"
- search_queries: 2-3 search queries to find appropriate facilities
- expected_procedures: list of likely procedures
- keywords: facility qualities to look for

Be concise. Return ONLY valid JSON.
```

### Mock Fallback
If API fails, return hardcoded moderate urgency with standard urgent care queries.

### Verification
```bash
cd backend && python -c "
import asyncio
from openrouter_client import SymptomEnricherAgent

async def test():
    agent = SymptomEnricherAgent()
    result = await agent.enrich('Twisted ankle, swelling', 'San Francisco')
    print(result)
    
asyncio.run(test())
"
# Should return: urgency, search_queries, etc.
```

---

## Step 4: Firecrawl Multi-Tier Search

### Goal
Use Firecrawl's **both** `/search` AND `/agent` APIs to maximize data quality and showcase technical sophistication.

### Strategy: 3-Tier Data Quality Approach

```
Tier 1: Firecrawl /search  → Fast discovery (10 facilities in 5s)
   ↓
Tier 2: Firecrawl /agent   → Real pricing deep dive (top 3 in 30s)
   ↓
Tier 3: Estimated fallback → Industry averages (if agent fails)
```

### Create: `backend/firecrawl_client.py`

**FirecrawlClient Class:**

```python
import os
import asyncio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class FirecrawlClient:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v1"
    
    async def search_and_enrich(self, 
                                queries: List[str], 
                                location: str,
                                expected_procedures: List[str],
                                top_n: int = 3) -> List[Dict]:
        """
        Multi-tier facility search:
        1. Fast search discovery
        2. Agent deep dive on top candidates
        3. Graceful fallback to estimates
        """
        
        # PHASE 1: Fast discovery with /search
        logger.info(f"Phase 1: Searching facilities with query: {queries[0]}")
        facilities = await self._fast_search(queries[0], location, limit=10)
        
        if not facilities:
            logger.warning("Search returned no results, using mock fallback")
            return self._mock_facilities(location)
        
        # PHASE 2: Quick local ranking by distance/rating
        logger.info(f"Phase 2: Ranking {len(facilities)} facilities")
        top_candidates = self._rank_by_heuristics(facilities, location)[:top_n]
        
        # PHASE 3: Agent deep dive for real pricing
        logger.info(f"Phase 3: Agent deep dive on top {len(top_candidates)}")
        enriched_facilities = []
        
        for candidate in top_candidates:
            try:
                pricing_data = await self._agent_deep_dive(
                    candidate["url"],
                    expected_procedures
                )
                enriched_facilities.append({
                    **candidate,
                    **pricing_data
                })
            except Exception as e:
                logger.warning(f"Agent failed for {candidate['name']}: {e}")
                # Fallback to estimates for this facility
                enriched_facilities.append({
                    **candidate,
                    "pricing": self._estimate_pricing(),
                    "data_source": "estimated",
                    "confidence": "low"
                })
        
        return enriched_facilities
    
    async def _fast_search(self, query: str, location: str, limit: int = 10):
        """Phase 1: Fast facility discovery using /search API"""
        
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": f"{query} {location}",
                    "limit": limit,
                    "sources": [{"type": "web"}]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Search failed: {response.status_code}")
                return []
            
            data = response.json()
            results = data.get("data", [])
            
            # Transform to our facility format
            facilities = []
            for result in results:
                facilities.append({
                    "name": result.get("title", "Unknown Facility"),
                    "url": result.get("url", ""),
                    "snippet": result.get("description", ""),
                    "address": self._extract_address(result.get("description", "")),
                })
            
            return facilities
    
    async def _agent_deep_dive(self, url: str, procedures: List[str]) -> Dict:
        """Phase 2: Use Firecrawl agent to find REAL pricing data"""
        
        import httpx
        
        # Start agent job
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/agent",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "prompt": f"""
                    Navigate to {url} and find pricing information for:
                    {', '.join(procedures)}
                    
                    Look for:
                    1. Base urgent care visit cost
                    2. X-ray or imaging costs
                    3. Insurance plans accepted
                    4. Wait times or appointment availability
                    
                    If you can't find exact pricing, note that in the response.
                    Return structured data with what you found.
                    """,
                    "urls": [url],
                    "schema": {
                        "type": "object",
                        "properties": {
                            "pricing": {
                                "type": "object",
                                "properties": {
                                    "urgent_care_visit": {"type": "number"},
                                    "xray": {"type": "number"}
                                }
                            },
                            "insurance_accepted": {"type": "array"},
                            "wait_time_estimate": {"type": "string"},
                            "data_found": {"type": "boolean"}
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Agent job failed to start: {response.status_code}")
            
            job_data = response.json()
            job_id = job_data.get("id")
            
            # Poll for completion (max 30 seconds)
            result = await self._poll_agent_status(job_id, timeout=30)
            
            if result.get("data_found"):
                return {
                    "pricing": result.get("pricing", {}),
                    "insurance_info": result.get("insurance_accepted", []),
                    "wait_time": result.get("wait_time_estimate"),
                    "data_source": "agent_scraped",
                    "confidence": "high"
                }
            else:
                # Agent couldn't find pricing
                raise Exception("Agent completed but found no pricing data")
    
    async def _poll_agent_status(self, job_id: str, timeout: int = 30) -> Dict:
        """Poll agent job status until completion"""
        
        import httpx
        
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            while True:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise Exception("Agent job timeout")
                
                response = await client.get(
                    f"{self.base_url}/agent/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data.get("data", {})
                elif status == "failed":
                    raise Exception(f"Agent job failed: {data.get('error')}")
                
                # Still processing, wait and retry
                await asyncio.sleep(2)
    
    def _rank_by_heuristics(self, facilities: List[Dict], location: str) -> List[Dict]:
        """Simple ranking by snippet quality and name recognition"""
        # For hackathon: prioritize facilities with addresses in snippet
        # In production: use geocoding + distance calculation
        
        scored = []
        for fac in facilities:
            score = 0
            snippet = fac.get("snippet", "").lower()
            
            # Heuristics
            if "urgent care" in snippet: score += 3
            if "walk-in" in snippet: score += 2
            if "insurance" in snippet: score += 1
            if fac.get("address"): score += 2
            
            scored.append((score, fac))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [fac for score, fac in scored]
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from snippet (basic regex)"""
        import re
        # Look for patterns like "123 Main St, City, CA 94102"
        match = re.search(r'\d+\s+[A-Za-z\s]+(?:St|Ave|Blvd|Dr|Way)[^,]*,\s*[A-Za-z\s]+,\s*[A-Z]{2}', text)
        return match.group(0) if match else None
    
    def _estimate_pricing(self) -> Dict:
        """Fallback: Industry average pricing"""
        return {
            "urgent_care_visit": 270,
            "xray": 180,
            "source": "Fair Health Consumer 2024 average"
        }
    
    def _mock_facilities(self, location: str) -> List[Dict]:
        """Final fallback: Hardcoded facilities"""
        return [
            {
                "name": "Carbon Health - Downtown SF",
                "address": "845 Market St, San Francisco, CA 94103",
                "url": "https://carbonhealth.com",
                "pricing": {"urgent_care_visit": 250, "xray": 150},
                "data_source": "mock",
                "confidence": "low"
            },
            {
                "name": "One Medical Urgent Care",
                "address": "55 Hawthorne St, San Francisco, CA 94105",
                "url": "https://onemedical.com",
                "pricing": {"urgent_care_visit": 300, "xray": 200},
                "data_source": "mock",
                "confidence": "low"
            }
        ]
```

### Why This Approach Wins

**Technical Complexity:**
- ✅ Uses BOTH Firecrawl APIs (`/search` + `/agent`)
- ✅ Async job orchestration with polling
- ✅ Multi-tier fallback strategy
- ✅ Real autonomous web navigation

**Data Quality:**
- ✅ Real facilities from `/search`
- ✅ Real pricing from `/agent` (when available)
- ✅ Transparent confidence scores
- ✅ Graceful degradation

**Prize Positioning:**
- 🏆 Firecrawl judges will notice `/agent` usage
- 🏆 Shows understanding of advanced features
- 🏆 Most teams won't attempt this

### Verification

```bash
cd backend && python -c "
import asyncio
from firecrawl_client import FirecrawlClient

async def test():
    client = FirecrawlClient()
    results = await client.search_and_enrich(
        queries=['urgent care ankle injury San Francisco'],
        location='San Francisco, CA',
        expected_procedures=['urgent care visit', 'X-ray']
    )
    
    for facility in results:
        print(f"\n{facility['name']}")
        print(f"  Data source: {facility.get('data_source')}")
        print(f"  Confidence: {facility.get('confidence')}")
        print(f"  Pricing: {facility.get('pricing')}")

asyncio.run(test())
"
# Should show 3 facilities with data sources and confidence levels
```

---

## Step 5: Ranking Agent + Orchestrator

### Goal
Rank facilities and generate recommendation with clear reasoning.

### Add to `openrouter_client.py`:

**RankingAgent:**
- **Model**: Claude Haiku via OpenRouter
- **Input**: facilities, insurance copay, urgency
- **Output**:
  ```json
  {
    "recommended": {
      "name": "Carbon Health Downtown",
      "your_cost": 145,
      "distance_miles": 0.8,
      "wait_time": "30 min"
    },
    "reasoning": [
      "Lowest total cost ($145 vs $430 alternatives)",
      "Closest location (0.8 miles)",
      "Shortest wait time (~30 min)"
    ],
    "why_not_er": "Your injury doesn't require emergency care. ER would cost $850+ with 2+ hour wait.",
    "alternatives": [...]
  }
  ```

### Create: `backend/advisor.py`

**ClearBillAdvisor Orchestrator:**
```python
class ClearBillAdvisor:
    def __init__(self):
        self.symptom_agent = SymptomEnricherAgent()
        self.firecrawl = FirecrawlClient()
        self.ranking_agent = RankingAgent()
    
    async def get_recommendation(self, symptoms, location, insurance_plan):
        # Step 1: Enrich symptoms
        enrichment = await self.symptom_agent.enrich(symptoms, location)
        
        # Step 2: Search facilities
        facilities = await self.firecrawl.search(
            enrichment.search_queries[0], 
            location
        )
        
        # Step 3: Get insurance copay
        copay = INSURANCE_COPAYS.get(insurance_plan, {}).get("urgent_care", 0)
        
        # Step 4: Rank and recommend
        recommendation = await self.ranking_agent.rank(
            facilities, copay, enrichment.urgency
        )
        
        return recommendation
```

### Insurance Copay Lookup
```python
INSURANCE_COPAYS = {
    "anthem_ppo": {"urgent_care": 55, "er": 250},
    "bcbs_hmo": {"urgent_care": 40, "er": 200},
    "aetna_ppo": {"urgent_care": 60, "er": 275},
    "medicare": {"urgent_care": 0, "er": 0},
    "uninsured": None  # Use cash prices
}
```

### Update: `backend/main.py`

Wire `/advisor/recommend` to use orchestrator:
```python
@app.post("/advisor/recommend")
async def get_recommendation(request: RecommendationRequest):
    advisor = ClearBillAdvisor()
    result = await advisor.get_recommendation(
        request.symptoms,
        request.location,
        request.insurance_plan
    )
    return result
```

### Verification
```bash
curl -X POST http://localhost:8000/advisor/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Twisted ankle running, swelling and pain",
    "location": "San Francisco, CA",
    "insurance_plan": "anthem_ppo"
  }'
# Should return full recommendation with reasoning
```

---

## Step 6: Frontend Integration

### Goal
Wire existing frontend to backend API with simplified input form.

### Update: `frontend/src/app/page.tsx`

**Input Form (3 fields):**
```tsx
<form>
  {/* Symptoms */}
  <textarea 
    placeholder="Describe your symptoms (e.g., Twisted ankle, swelling...)"
    value={symptoms}
    onChange={(e) => setSymptoms(e.target.value)}
  />
  
  {/* Location */}
  <input 
    placeholder="Your location (e.g., San Francisco, CA)"
    value={location}
    onChange={(e) => setLocation(e.target.value)}
  />
  
  {/* Insurance Dropdown */}
  <select value={insurance} onChange={(e) => setInsurance(e.target.value)}>
    <option value="anthem_ppo">Anthem PPO ($55 copay)</option>
    <option value="bcbs_hmo">Blue Shield HMO ($40 copay)</option>
    <option value="aetna_ppo">Aetna PPO ($60 copay)</option>
    <option value="medicare">Medicare ($0 copay)</option>
    <option value="uninsured">Uninsured (Cash Pay)</option>
  </select>
  
  <button type="submit">Get Recommendation</button>
</form>
```

**API Call:**
```tsx
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  
  const response = await fetch('http://localhost:8000/advisor/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symptoms,
      location,
      insurance_plan: insurance
    })
  });
  
  const data = await response.json();
  setResult(data);
  setLoading(false);
};
```

**Components to reuse:**
- Recommendation card (already exists)
- Agent stream visualization (already exists)
- Alternatives comparison (already exists)

### Verification
1. Run backend: `cd backend && uvicorn main:app --reload --port 8000`
2. Run frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000
4. Fill form, submit, see results

---

## Step 7: End-to-End Testing

### Test Scenarios

**Scenario 1: Ankle Injury (Primary Demo)**
```
Symptoms: "Twisted my ankle running, swelling and pain, can't walk"
Location: "San Francisco, CA"
Insurance: Anthem PPO

Expected:
- Urgency: Moderate
- Recommended: Urgent Care
- Your cost: $145 ($55 copay + estimated X-ray)
- Savings vs ER: $700+
```

**Scenario 2: Sore Throat**
```
Symptoms: "Sore throat for 3 days, fever 101°F"
Location: "San Francisco"
Insurance: Uninsured

Expected:
- Urgency: Low/Moderate
- Recommended: Urgent Care or Virtual
- Your cost: $150-200 (cash)
```

**Scenario 3: Chest Pain (Edge Case)**
```
Symptoms: "Chest pain, shortness of breath"
Location: "San Francisco"
Insurance: Any

Expected:
- Urgency: EMERGENCY
- Recommended: ER (not urgent care)
- Message: "Call 911 or go to ER immediately"
```

### Checklist
- [ ] Happy path works end-to-end
- [ ] Loading states show properly
- [ ] Recommendation displays with reasoning
- [ ] Alternatives show
- [ ] No console errors
- [ ] Mobile view acceptable

---

## Step 8: Deployment

### Backend (Railway or Render)

1. Push code to GitHub
2. Connect Railway to repo
3. Add environment variables:
   - `OPENROUTER_API_KEY`
   - `FIRECRAWL_API_KEY`
4. Deploy

### Frontend (Vercel)

```bash
cd frontend
vercel deploy --prod
```

Set environment variable:
- `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`

### Final Check
1. Visit deployed frontend URL
2. Run demo scenario
3. Verify all features work
4. Test on mobile

---

## Time Breakdown

| Step | Task | Time | Status |
|------|------|------|--------|
| 3 | OpenRouter Symptom Enricher | 45 min | DONE |
| 4 | Firecrawl Multi-Tier Search (/search + /agent) | 45 min | TODO |
| 5 | Ranking Agent + Orchestrator | 45 min | TODO |
| 6 | Frontend Integration | 30 min | TODO |
| 7 | Testing | 20 min | TODO |
| 8 | Deployment | 30 min | TODO |
| | **Total** | **3.5 hrs** | |

---

## Prize Positioning

| Prize | How We Win |
|-------|-----------|
| **OpenRouter ($1K)** | Two real agent calls (Symptom Enricher + Ranking) with visible reasoning |
| **Firecrawl ($5K)** | Advanced multi-tier approach: `/search` for discovery + `/agent` for autonomous pricing extraction. Shows mastery of both APIs with real-world data quality challenges. |
| **Reducto ($1K)** | ~~Removed~~ - Not pursuing this prize |
| **Supabase ($1K)** | Mention in pitch: "Architecture ready for Supabase caching at scale" |

---

## Demo Script (90 seconds)

**0-15s (Hook):**
> "I paid $850 for an ER visit when I should have paid $145 at urgent care. 45 million Americans face this same problem."

**15-45s (Input):**
- Type symptoms: "Twisted ankle running, swelling and pain"
- Type location: "San Francisco"
- Select: "Anthem PPO"
- Click "Get Recommendation"

**45-70s (AI in Action):**
> "Watch our multi-agent system work. OpenRouter enriches my symptoms... Firecrawl searches real facilities... Ranking agent finds my best option..."

**70-85s (Result):**
> "Carbon Health Downtown. My cost: $145. That's $705 saved vs the ER. Here's why: closest, cheapest, shortest wait."

**85-90s (Close):**
> "Multi-agent architecture. Real facility discovery. Life-changing savings."

---

**Start building. Clock is ticking. 🚀**