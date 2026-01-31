# ClearBill Advisor - Project Blueprint

> A step-by-step guide to building a healthcare vertical agent from scratch. No code, just concepts and decisions.

***

## How to Use This Blueprint

This guide is designed for **iterative development**. Each phase ends with a **checkpoint** that tells you:
- What you should have built
- How to verify it works
- What success looks like

**Development approach:**
1. Complete one phase at a time
2. Hit the checkpoint and verify everything works
3. Only move to the next phase after passing the checkpoint
4. If something breaks, you know exactly where to look

***

## Progress Tracker

Use this to track your progress through the build:

```
[ ] Checkpoint 1: Project Foundation
[x] Checkpoint 2: Backend API Server
[ ] Checkpoint 3: Reducto Insurance OCR
[ ] Checkpoint 4: OpenRouter Agent System
[ ] Checkpoint 5: Firecrawl Price Discovery
    ⭐ MILESTONE: Core Components Complete
[ ] Checkpoint 6: Agent Orchestration
    ⭐ MILESTONE: Backend Complete
[ ] Checkpoint 7: Frontend Dashboard
[ ] Checkpoint 8: Agent Visualization
    ⭐ MILESTONE: Full Application Working
[ ] Checkpoint 9: Demo Polish
[ ] Checkpoint 10: Pitch Ready
    🎉 PROJECT COMPLETE
```

**Tip:** You can develop checkpoints 3-5 in parallel since they're independent components. Checkpoint 6 requires all of them.

***

## Overview

**What We're Building:**  
A healthcare vertical agent that analyzes symptoms, extracts insurance information, discovers pricing across urgent care facilities, and recommends the best option—all using intelligent agent orchestration.

**The Core Flow:**
```
Insurance Card → OCR Extract → Symptom Analysis → Price Discovery → Rank Options → Recommendation
```

**Tech Stack:**
- Backend: Python + FastAPI
- Frontend: Next.js + React + TypeScript
- External Services: 
  - Reducto (insurance card OCR)
  - OpenRouter (multi-agent AI)
  - Firecrawl (price discovery)
  - Supabase (optional - caching)

**Target Prizes:**
- OpenRouter ($1,000 credits) - Vertical agent architecture
- Firecrawl ($5,000 + credits) - Web intelligence
- Reducto ($1,000 + credits) - Document intelligence
- Supabase ($1,000/person) - Scaling story

***

## Phase 1: Project Foundation

### Step 1.1: Create Project Structure

Create the following directory layout:

```
clearbill-advisor/
├── backend/              # Python FastAPI server
├── frontend/             # Next.js React app
├── .env                  # Environment variables (gitignored)
├── README.md             # Project documentation
└── docs/                 # Pitch deck and demo assets
```

### Step 1.2: Define Environment Variables

You'll need API keys for four services:
- `OPENROUTER_API_KEY` - For multi-agent orchestration
- `REDUCTO_API_KEY` - For insurance card OCR
- `FIRECRAWL_API_KEY` - For price discovery
- `SUPABASE_URL` - (Optional) For caching
- `SUPABASE_KEY` - (Optional) For caching

Store these in a `.env` file at the project root. Never commit this file.

### Step 1.3: Define Core Data Models

Plan your data structures:

**Insurance Information:**
- Provider name (e.g., "Anthem Blue Cross")
- Plan type (e.g., "PPO Silver")
- Member ID
- Copay amounts (urgent care, ER, specialist)
- Deductible information

**Facility Information:**
- Name (e.g., "Carbon Health Downtown")
- Address and distance from user
- Pricing for procedures
- Wait time estimate
- Quality rating
- Accepts insurance (yes/no)

**Recommendation:**
- Recommended facility
- Estimated out-of-pocket cost
- Reasoning for the choice
- Alternative options
- What to expect (procedures, timeline)

***

### ✅ CHECKPOINT 1: Project Foundation

**What you should have:**
- [ ] Directory structure: `clearbill-advisor/backend/`, `clearbill-advisor/frontend/`
- [ ] A `.env` file with placeholder API keys
- [ ] A basic `README.md` with project description
- [ ] Data model concepts documented

**How to verify:**
```bash
ls -la clearbill-advisor/
# Should show: backend/, frontend/, .env, README.md, docs/

cat .env
# Should show: OPENROUTER_API_KEY=..., REDUCTO_API_KEY=..., etc.
```

**Success criteria:** Project structure exists and .env has all required keys defined (even if placeholder values).

***

## Phase 2: Backend API Architecture

### Step 2.1: Set Up FastAPI Server

Create the main FastAPI application with:
- CORS middleware enabled for frontend communication
- Request/response logging for debugging
- Error handling middleware
- Session tracking for recommendations

**Key Design Decisions:**
- Use async/await throughout for non-blocking I/O
- Allow both real API calls and mock mode for testing
- Return detailed reasoning with every recommendation
- Stream agent progress for live UI updates

### Step 2.2: Define API Endpoints

Create these REST endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check, returns API status |
| `/ocr/insurance-card` | POST | Upload insurance card for OCR |
| `/advisor/recommend` | POST | Main endpoint - get facility recommendation |
| `/facilities/search` | GET | Search facilities by location |
| `/demo/scenarios` | GET | Return predefined test scenarios |
| `/agent/stream` | WebSocket | Real-time agent reasoning updates |

### Step 2.3: Define Request/Response Models

**Insurance OCR Request:**
- `image` (file upload): Insurance card image
- `return_benefits` (bool, default true): Extract copay amounts

**Insurance OCR Response:**
- `success` (bool): Whether OCR succeeded
- `provider` (string): Insurance provider name
- `plan_name` (string): Plan type
- `member_id` (string): Member ID
- `benefits` (object): Copay and deductible info
- `confidence` (float): OCR confidence score

**Recommendation Request:**
- `symptoms` (string, required): User's symptoms description
- `insurance` (object, optional): Insurance information (or from OCR)
- `location` (string, required): User location (ZIP or city)
- `urgency` (string, default "moderate"): "low", "moderate", "high", "emergency"
- `use_mock` (bool, default false): Whether to use mock data

**Recommendation Response:**
- `success` (bool): Whether recommendation generated
- `recommended_facility` (object): Primary recommendation
- `alternatives` (array): Other viable options
- `reasoning` (object): Agent analysis breakdown
- `triage` (object): Urgency classification
- `estimated_cost` (float): Your out-of-pocket cost
- `agent_steps` (array): Each agent's contribution
- `duration_seconds` (float): Total processing time

***

### ✅ CHECKPOINT 2: Backend API Server

**What you should have:**
- [ ] `backend/main.py` with FastAPI app
- [ ] `backend/requirements.txt` with dependencies (fastapi, uvicorn, openai, etc.)
- [ ] `backend/models.py` with Pydantic models
- [ ] Health endpoint working
- [ ] CORS configured

**How to verify:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# In another terminal:
curl http://localhost:8000/health
# Should return: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

**Success criteria:** Server starts without errors, health endpoint returns JSON response, CORS allows localhost:3000.

***

## Phase 3: Reducto Insurance OCR Integration

### Step 3.1: Understand the Purpose

Insurance card OCR eliminates manual data entry:
- User snaps photo of insurance card
- Reducto extracts structured data
- Auto-fills insurance form
- Faster onboarding = better UX

### Step 3.2: Create Reducto Client

Build a wrapper class that provides:

**OCR Operations:**
- `upload_image(file)` - Upload insurance card image
- `extract_fields()` - Extract provider, plan, member ID, benefits
- `parse_benefits()` - Extract copay amounts from text
- `validate_extraction()` - Check confidence scores

**Result Format:**
- `success` (bool): Whether extraction succeeded
- `data` (object): Extracted fields
- `confidence` (float): Overall confidence score
- `raw_text` (string): Raw OCR output for debugging
- `error` (string, optional): Error message if failed

### Step 3.3: Implement Mock Client

For testing without API credits:

**Mock Behavior:**
- Simulate realistic insurance card data
- Return common providers (Anthem, Aetna, Blue Shield, United)
- Generate realistic member IDs
- Include typical copay amounts ($25 PCP, $55 urgent care, $250 ER)
- Add slight randomness to confidence scores (0.85-0.95)

### Step 3.4: Handle Edge Cases

**Poor Image Quality:**
- Return lower confidence score
- Suggest user retake photo
- Fallback to manual entry

**Unrecognized Format:**
- Extract what's possible
- Flag fields as uncertain
- Allow user to correct

**Missing Benefits:**
- Still return provider and member ID
- Estimate copay based on plan type
- Note uncertainty in response

***

### ✅ CHECKPOINT 3: Reducto Insurance OCR

**What you should have:**
- [ ] `backend/reducto_client.py` with ReductoClient and MockReductoClient
- [ ] InsuranceData dataclass with all fields
- [ ] Factory function `get_reducto_client(use_mock)`
- [ ] `/ocr/insurance-card` endpoint implemented

**How to verify (Mock Mode):**
```bash
# Create a test image file (any image works for mock)
curl -X POST http://localhost:8000/ocr/insurance-card \
  -F "image=@test_card.jpg" \
  -F "use_mock=true"

# Should return:
# {
#   "success": true,
#   "provider": "Anthem Blue Cross",
#   "plan_name": "PPO Silver",
#   "member_id": "ABC123456789",
#   "benefits": {
#     "urgent_care_copay": 55,
#     "er_copay": 250
#   },
#   "confidence": 0.92
# }
```

**How to verify (Real Mode - if you have API key):**
```bash
# Use actual insurance card image
curl -X POST http://localhost:8000/ocr/insurance-card \
  -F "image=@real_insurance_card.jpg" \
  -F "use_mock=false"

# Should extract real data from image
```

**Success criteria:**
- Mock mode returns realistic insurance data
- Real mode (if tested) extracts text from images
- Error handling for invalid images
- Confidence scores included

***

## Phase 4: OpenRouter Multi-Agent System

### Step 4.1: Design Agent Architecture

Create four specialized agents, each optimized for specific tasks:

**Agent 1: Triage Agent** (Fast + Cheap)
- Model: DeepSeek V3 or Claude Haiku
- Purpose: Classify urgency level
- Input: Symptom description
- Output: Urgency (low/moderate/high/emergency), expected procedures, care level needed

**Agent 2: Insurance Analyzer** (Structured Extraction)
- Model: Claude Haiku
- Purpose: Analyze insurance coverage
- Input: Insurance data from OCR + procedure codes
- Output: Estimated copays, deductible status, coverage notes

**Agent 3: Ranking Agent** (Complex Reasoning)
- Model: Claude Sonnet
- Purpose: Rank facilities by total value
- Input: Facilities, pricing, insurance, urgency, distance
- Output: Ranked list with reasoning for each

**Agent 4: Explanation Agent** (Optional - User-Facing)
- Model: GPT-4o-mini
- Purpose: Generate clear explanations
- Input: Recommendation data
- Output: Human-friendly explanation of the choice

### Step 4.2: Create OpenRouter Client

Build a unified client that routes to different models:

```
get_openrouter_client() → Returns OpenRouter client instance

Methods:
- call_triage_agent(symptoms) → Urgency classification
- call_insurance_agent(insurance, procedures) → Cost estimate
- call_ranking_agent(facilities, context) → Ranked recommendations
- call_explanation_agent(recommendation) → User-friendly explanation
```

### Step 4.3: Define Agent Prompts

**Triage Agent Prompt:**
```
You are a medical triage assistant. Classify urgency and identify needed care.

Input: Patient symptoms
Output JSON:
{
  "urgency": "moderate",
  "care_level": "urgent_care",
  "expected_procedures": ["99283", "73610"],
  "reasoning": "...",
  "red_flags": []
}

Rules:
- EMERGENCY: life-threatening (chest pain, severe bleeding, stroke symptoms)
- HIGH: needs care within hours (possible fracture, severe pain)
- MODERATE: needs care within 24hrs (minor injuries, infections)
- LOW: can wait days (follow-ups, mild symptoms)
```

**Insurance Agent Prompt:**
```
You are an insurance benefits analyzer. Calculate out-of-pocket costs.

Input: Insurance plan + procedure codes
Output JSON:
{
  "urgent_care_visit": 55,
  "xray": 90,
  "total_estimated_oop": 145,
  "deductible_applies": false,
  "notes": "..."
}
```

**Ranking Agent Prompt:**
```
You are a healthcare advisor. Rank facilities by total value.

Consider:
1. Total out-of-pocket cost (most important)
2. Distance/travel time
3. Quality ratings
4. Current wait times
5. Insurance acceptance

Input: Array of facilities with pricing, distance, ratings
Output JSON:
{
  "ranked_facilities": [...],
  "primary_recommendation": {...},
  "reasoning": "...",
  "why_not_er": "..."
}
```

### Step 4.4: Implement Model Routing

**Cost Optimization Strategy:**
```
Fast Tasks (Triage, Classification):
→ Use DeepSeek V3 ($0.25/1M tokens)
→ Response time: 200-500ms

Structured Extraction (Insurance):
→ Use Claude Haiku ($0.25/1M tokens)
→ Reliable JSON parsing

Complex Reasoning (Ranking):
→ Use Claude Sonnet ($3/1M tokens)
→ Best multi-factor decision making

Cost per recommendation: ~$0.03
vs. GPT-4 everywhere: ~$0.45 (15x more expensive)
```

### Step 4.5: Create Mock Agents

For testing without API calls:

**Mock Triage:**
- Parse symptoms for keywords (ankle, chest, bleeding)
- Return appropriate urgency based on keywords
- Simulate realistic procedure codes

**Mock Insurance:**
- Use standard copay amounts from plan type
- Calculate totals based on procedure codes
- Return predictable estimates

**Mock Ranking:**
- Sort by total cost first
- Apply distance penalty
- Add realistic reasoning text

***

### ✅ CHECKPOINT 4: OpenRouter Agent System

**What you should have:**
- [ ] `backend/openrouter_agents.py` with all four agents
- [ ] Agent prompt templates
- [ ] Model routing logic
- [ ] Mock agent implementations
- [ ] TriageResult, InsuranceAnalysis, RankingResult dataclasses

**How to verify (Mock Mode):**
```python
import asyncio
from openrouter_agents import get_agent_orchestrator

async def test():
    orchestrator = get_agent_orchestrator(use_mock=True)
    
    # Test triage agent
    triage = await orchestrator.triage_agent(
        symptoms="Twisted my ankle running, can't put weight on it"
    )
    print(f"Urgency: {triage.urgency}")
    print(f"Care level: {triage.care_level}")
    print(f"Procedures: {triage.expected_procedures}")
    
    # Test insurance agent
    insurance = await orchestrator.insurance_agent(
        plan_type="PPO Silver",
        copays={"urgent_care": 55, "er": 250},
        procedures=["99283", "73610"]
    )
    print(f"Estimated OOP: ${insurance.total_oop}")
    
asyncio.run(test())
```

**How to verify (Real Mode - if you have API key):**
```python
# Set OPENROUTER_API_KEY in .env
orchestrator = get_agent_orchestrator(use_mock=False)
# Same tests - should call real OpenRouter API
```

**Success criteria:**
- Mock mode returns realistic agent responses
- Real mode calls appropriate models via OpenRouter
- JSON parsing handles both valid and invalid responses
- Each agent returns structured data
- Cost tracking shows per-agent token usage

**🎉 MILESTONE: Core AI System Complete!**

***

## Phase 5: Firecrawl Price Discovery Integration

### Step 5.1: Understand the Challenge

Healthcare pricing is hidden and fragmented:
- Buried in PDF price transparency files
- On obscure facility websites
- Often years out of date
- Different formats per provider
- Requires discovery + extraction + validation

Firecrawl solves this with web intelligence.

### Step 5.2: Create Firecrawl Client

Build a client that discovers and extracts pricing:

**Discovery Operations:**
- `search_facilities(location, care_type)` - Find urgent cares in area
- `scrape_pricing(url)` - Extract pricing from transparency files
- `detect_file_type(url)` - Identify PDFs vs HTML vs structured data
- `validate_freshness(data)` - Check if pricing is current

**Extraction Strategy:**
- Start with facility websites
- Look for "price transparency" or "billing" pages
- Download and parse PDFs if needed
- Extract CPT code → price mappings
- Score transparency (how easy was it to find?)

**Result Format:**
```
{
  "facility_name": "Carbon Health Downtown",
  "address": "123 Market St, SF, CA 94102",
  "distance_miles": 0.8,
  "pricing": {
    "99283": 270,  // Urgent care visit
    "73610": 180   // Ankle X-ray
  },
  "last_updated": "2026-01-15",
  "transparency_score": 8.5,
  "source_url": "...",
  "accepts_insurance": ["Anthem", "Aetna", "Blue Shield"]
}
```

### Step 5.3: Implement Search Strategy

**Multi-Source Approach:**

1. **Structured Sources** (Fast)
   - Check if facility has API
   - Look for JSON/CSV price lists
   - Parse structured data

2. **Website Scraping** (Medium)
   - Find pricing pages via Firecrawl
   - Extract tables and lists
   - Parse HTML for CPT codes

3. **PDF Extraction** (Slow)
   - Download transparency PDF
   - OCR if needed
   - Parse tables for pricing

4. **Estimation** (Fallback)
   - Use regional averages
   - Note as "estimated" not "actual"
   - Lower confidence score

### Step 5.4: Create Mock Pricing Data

For testing without API credits:

**Mock Facilities:**
```python
MOCK_FACILITIES = [
    {
        "name": "Carbon Health Downtown",
        "address": "123 Market St, SF",
        "distance": 0.8,
        "pricing": {"99283": 270, "73610": 180},
        "transparency_score": 9.2,
        "rating": 4.5,
        "wait_time": "30 min"
    },
    {
        "name": "Exer Urgent Care Mission",
        "address": "456 Mission St, SF",
        "distance": 1.2,
        "pricing": {"99283": 430, "73610": 220},
        "transparency_score": 6.5,
        "rating": 4.2,
        "wait_time": "45 min"
    },
    {
        "name": "SF General ER",
        "address": "789 General Ave, SF",
        "distance": 0.5,
        "pricing": {"99283": 2850, "73610": 950},  // ER is expensive!
        "transparency_score": 3.0,
        "rating": 4.7,
        "wait_time": "2+ hours"
    }
]
```

### Step 5.5: Implement Caching Strategy

**Why Cache:**
- Firecrawl credits are limited
- Pricing doesn't change hourly
- Multiple users in same area = duplicate lookups
- Demo needs fast responses

**Cache Structure (if using Supabase):**
```
facility_pricing table:
- facility_id (PK)
- name, address, location (coordinates)
- pricing_json (JSONB)
- last_updated (timestamp)
- transparency_score (int)
- source_url (text)

Index on: location (for geographic queries)
Refresh: Every 24 hours or on-demand
```

**Cache Strategy:**
```
1. Check cache for location + procedure codes
2. If found and fresh (< 24hrs): Return cached
3. If not found or stale: Call Firecrawl
4. Update cache with new data
5. Return result
```

***

### ✅ CHECKPOINT 5: Firecrawl Price Discovery

**What you should have:**
- [ ] `backend/firecrawl_client.py` with FirecrawlClient and MockFirecrawlClient
- [ ] FacilityPricing dataclass
- [ ] Mock facility data for SF Bay Area
- [ ] Factory function `get_firecrawl_client(use_mock)`
- [ ] `/facilities/search` endpoint implemented

**How to verify (Mock Mode):**
```bash
curl "http://localhost:8000/facilities/search?location=San+Francisco&procedures=99283,73610&use_mock=true"

# Should return array of facilities with pricing:
# [
#   {
#     "name": "Carbon Health Downtown",
#     "distance_miles": 0.8,
#     "pricing": {"99283": 270, "73610": 180},
#     "total_cost": 450,
#     "transparency_score": 9.2
#   },
#   ...
# ]
```

**How to verify (Real Mode - if you have API key):**
```bash
# Real Firecrawl search
curl "http://localhost:8000/facilities/search?location=San+Francisco&procedures=99283&use_mock=false"

# Should discover real urgent care facilities and pricing
```

**Success criteria:**
- Mock mode returns 3-5 facilities with realistic pricing
- Facilities sorted by distance by default
- Pricing includes CPT code breakdowns
- Transparency scores reflect data quality
- Real mode (if tested) discovers actual facilities

**🎉 MILESTONE: All Core Components Complete!**

You now have:
- Reducto OCR for insurance cards ✓
- OpenRouter agents for intelligence ✓
- Firecrawl for price discovery ✓

Next: Orchestrate them together.

***

## Phase 6: Agent Orchestration

### Step 6.1: Design the Orchestration Flow

```
User Input:
├─ Symptoms: "Twisted ankle, can't walk"
├─ Insurance: (from OCR or manual)
└─ Location: "San Francisco, CA"

Step 1: Parallel Processing (agents can run simultaneously)
├─ Triage Agent: Analyze symptoms → urgency + procedures
└─ Insurance Agent: Calculate coverage → copays

Step 2: Sequential Processing (depends on Step 1)
└─ Firecrawl: Search facilities with procedure codes from triage

Step 3: Final Processing (depends on Step 2)
└─ Ranking Agent: Compare all facilities → recommend best

Output:
├─ Recommended facility
├─ Your estimated cost
├─ Why this choice (reasoning)
├─ Alternative options
└─ What to expect
```

### Step 6.2: Create Advisor Orchestrator

Build the main orchestration class:

```
class ClearBillAdvisor:
    def __init__(self, use_mock=False):
        self.triage_agent = get_triage_agent(use_mock)
        self.insurance_agent = get_insurance_agent(use_mock)
        self.firecrawl = get_firecrawl_client(use_mock)
        self.ranking_agent = get_ranking_agent(use_mock)
    
    async def get_recommendation(self, request):
        # Step 1: Parallel analysis
        triage, insurance = await asyncio.gather(
            self.triage_agent.analyze(request.symptoms),
            self.insurance_agent.analyze(request.insurance)
        )
        
        # Step 2: Price discovery
        facilities = await self.firecrawl.search(
            location=request.location,
            procedures=triage.expected_procedures
        )
        
        # Step 3: Ranking
        recommendation = await self.ranking_agent.rank(
            facilities=facilities,
            insurance=insurance,
            triage=triage,
            location=request.location
        )
        
        return recommendation
```

### Step 6.3: Implement Live Updates

**WebSocket Stream:**
```
Connection opened
→ "🧠 Analyzing your symptoms..."
→ "💳 Checking your insurance coverage..."
→ "🏥 Finding nearby facilities..."
→ "🔍 Discovering current pricing..."
→ "📊 Ranking options by value..."
→ "✅ Recommendation ready!"
Connection closed
```

**Progress Tracking:**
```
{
  "step": "triage",
  "status": "in_progress",
  "message": "Analyzing symptoms...",
  "progress": 0.2
}

{
  "step": "triage",
  "status": "complete",
  "result": { "urgency": "moderate", ... },
  "progress": 0.4
}
```

### Step 6.4: Handle Errors Gracefully

**Failure Scenarios:**

**Triage Agent Fails:**
- Fall back to manual urgency input
- Estimate procedures based on symptoms keywords
- Continue with warning

**Insurance Agent Fails:**
- Use self-pay pricing instead
- Note "uninsured estimate" in result
- Continue

**Firecrawl Fails:**
- Fall back to cached pricing (if available)
- Use mock data as last resort
- Return degraded but working result

**Ranking Agent Fails:**
- Sort by price only (simple fallback)
- Still provide recommendation
- Note reduced confidence

### Step 6.5: Implement Reasoning Transparency

**For Each Recommendation, Include:**

```
{
  "recommended_facility": {
    "name": "Carbon Health Downtown",
    "your_cost": 145,
    "why_recommended": [
      "Lowest total cost ($145 vs $430 alternatives)",
      "Closest location (0.8 miles, 4 min drive)",
      "Shortest wait time (~30 minutes)",
      "High quality ratings (4.5/5 stars)",
      "Excellent price transparency (9.2/10)"
    ],
    "why_not_er": "Your injury doesn't require emergency care. ER would cost $850 (6x more) with 2+ hour wait.",
    "what_to_expect": {
      "procedures": ["Urgent care exam", "Ankle X-ray", "Possible splint"],
      "duration": "45-60 minutes total",
      "steps": ["Check-in", "Exam", "X-ray", "Treatment discussion"]
    }
  },
  "alternatives": [...]
}
```

***

### ✅ CHECKPOINT 6: Agent Orchestration

**What you should have:**
- [ ] `backend/advisor.py` with ClearBillAdvisor orchestrator
- [ ] `/advisor/recommend` endpoint implemented
- [ ] WebSocket `/agent/stream` for live updates
- [ ] Error fallback logic
- [ ] Full reasoning in responses

**How to verify (Mock Mode - Full Flow):**
```bash
curl -X POST http://localhost:8000/advisor/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "Twisted my ankle running, cannot put weight on it",
    "insurance": {
      "provider": "Anthem Blue Cross",
      "plan": "PPO Silver",
      "urgent_care_copay": 55
    },
    "location": "San Francisco, CA",
    "use_mock": true
  }'

# Should return full recommendation with:
# - Triage analysis (urgency: moderate)
# - Insurance calculation (copays)
# - 3-5 facility options with pricing
# - Primary recommendation with reasoning
# - Alternatives
# - What to expect
```

**How to verify (WebSocket):**
```javascript
// In browser console or Node.js:
const ws = new WebSocket('ws://localhost:8000/agent/stream');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`[${update.step}] ${update.message}`);
};

ws.send(JSON.stringify({
  symptoms: "Twisted ankle",
  insurance: {...},
  location: "San Francisco"
}));
```

**Success criteria:**
- Full flow completes in mock mode (< 5 seconds)
- Each agent's contribution visible in response
- Reasoning explains the recommendation
- Alternatives provided
- Errors handled gracefully (test by removing API keys)
- WebSocket sends progress updates

**🎉 MILESTONE: Backend Complete!**

The entire healthcare advisor works end-to-end:
- OCR extracts insurance
- Agents analyze situation
- Firecrawl finds pricing
- Orchestrator recommends best option

***

## Phase 7: Frontend Dashboard

### Step 7.1: Set Up Next.js Project

Create Next.js app with:
- TypeScript for type safety
- Tailwind CSS for styling
- Shadcn/ui for components (optional)
- Framer Motion for animations
- Lucide React for icons

### Step 7.2: Design the UI Layout

**Page Structure:**

```
┌─────────────────────────────────────┐
│ Header: "ClearBill Advisor"        │
│ "Know where to go and what you'll pay" │
├─────────────────────────────────────┤
│  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/116818212/c87a69f7-6c92-463a-bf38-4020e7b40cb5/Instructions.pdf) Insurance Upload                │
│     📷 Snap photo of card           │
│     OR enter manually               │
├─────────────────────────────────────┤
│  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/116818212/5206efc1-9635-4fb5-8299-76a9fd7e049f/image.jpg) Symptom Input                   │
│     📝 "What's wrong?"              │
│     💬 "Twisted my ankle..."        │
├─────────────────────────────────────┤
│  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/116818212/950c1e07-cf54-4b63-9ecc-d74e0c891819/image.jpg) Location                        │
│     📍 "San Francisco, CA"          │
├─────────────────────────────────────┤
│ [Get Recommendation] 🚀             │
├─────────────────────────────────────┤
│  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/116818212/41ea0a54-fdf1-4b00-9cce-123f6087cdfd/image.jpg) Live Agent Stream               │
│     🧠 Analyzing symptoms...        │
│     💳 Checking insurance...        │
│     🏥 Finding facilities...        │
├─────────────────────────────────────┤
│  [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/116818212/903507be-b450-4429-af6c-466b31170485/image.jpg) Recommendation Card             │
│     ✅ Go to Carbon Health          │
│     💰 Your Cost: $145              │
│     📍 0.8 miles (4 min)            │
│     ⏱️ Wait: ~30 min                │
│     WHY THIS CHOICE: (reasoning)    │
├─────────────────────────────────────┤
│ [6] Alternatives                    │
│     [Facility 2] [Facility 3]       │
└─────────────────────────────────────┘
```

### Step 7.3: Implement Insurance Upload Component

**Features:**
- Camera button for mobile (uses phone camera)
- Drag-and-drop for desktop
- Preview of uploaded image
- Loading state during OCR (3-5 seconds)
- Auto-fill form when OCR completes
- Manual override if OCR fails

**Flow:**
```
User clicks "📷 Snap photo"
→ Phone camera opens
→ User takes photo
→ Upload to /ocr/insurance-card
→ Show spinner: "Reading your card..."
→ 3 seconds later: Form auto-fills
→ "✅ Insurance info extracted!"
```

### Step 7.4: Build Symptom Input

**Design Considerations:**
- Large textarea for free-form description
- Placeholder examples:
  - "Twisted my ankle running, can't put weight on it"
  - "Sore throat for 3 days, fever of 101°F"
  - "Cut my hand while cooking, bleeding stopped"
- Character counter (optional)
- Urgency indicator (auto-detected, but user can override)

### Step 7.5: Create Agent Stream Visualization

**Live Progress Indicators:**

```
Current step: 🧠 Analyzing symptoms
├─ ✅ Triage complete (500ms)
├─ ⏳ Insurance analysis (in progress...)
├─ ⏸️ Price discovery (waiting)
└─ ⏸️ Ranking facilities (waiting)
```

**Visual Design:**
- Progress bar (0-100%)
- Step-by-step indicators
- Smooth animations between steps
- Each step shows icon + status + timing
- Terminal/console aesthetic (cyan text on dark)

### Step 7.6: Design Recommendation Card

**Primary Recommendation:**

```
┌────────────────────────────────────┐
│ ✅ RECOMMENDED: Carbon Health      │
│                                    │
│ 💰 Your Cost: $145                 │
│ 📍 Distance: 0.8 miles (4 min)    │
│ ⏱️ Wait Time: ~30 minutes         │
│ ⭐ Rating: 4.5/5 (287 reviews)     │
│                                    │
│ WHY THIS CHOICE:                   │
│ ✓ Lowest cost ($145 vs $430)      │
│ ✓ Closest location                │
│ ✓ Shortest wait time              │
│ ✓ High quality ratings            │
│                                    │
│ ❌ WHY NOT ER?                     │
│ Your injury doesn't require        │
│ emergency care. ER would cost      │
│ $850 (6x more) with 2+ hour wait. │
│                                    │
│ [Book Appointment] [Directions]    │
└────────────────────────────────────┘
```

**Color Scheme:**
- Green/emerald for recommended choice
- Cyan for information
- Red for warnings (ER comparison)
- Dark background with glowing borders

### Step 7.7: Add Alternative Options

**Comparison Table:**

| Facility | Cost | Distance | Wait | Rating | Transparency |
|----------|------|----------|------|--------|--------------|
| **Carbon Health** ⭐ | **$145** | **0.8 mi** | **30 min** | 4.5⭐ | 9.2/10 |
| Exer Urgent Care | $430 | 1.2 mi | 45 min | 4.2⭐ | 6.5/10 |
| SF General ER | $850 | 0.5 mi | 2+ hrs | 4.7⭐ | 3.0/10 |

**Interactive Elements:**
- Click any row to see details
- Expand to show full pricing breakdown
- Map view showing locations

***

### ✅ CHECKPOINT 7: Frontend Dashboard

**What you should have:**
- [ ] Next.js project in `frontend/`
- [ ] Insurance upload component with camera
- [ ] Symptom input textarea
- [ ] Location input
- [ ] Submit button
- [ ] Basic styling with dark theme

**How to verify (Static UI):**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

**Visual checklist:**
- [ ] Header with "ClearBill Advisor" title
- [ ] Insurance upload section with camera button
- [ ] Symptom textarea with placeholder
- [ ] Location input
- [ ] "Get Recommendation" button styled prominently
- [ ] Dark theme with cyan/emerald accents

**How to verify (With Backend):**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# In browser:
1. Upload insurance card (or use mock)
2. Enter symptoms
3. Enter location
4. Click "Get Recommendation"
5. See loading/progress indicators
6. See recommendation appear
```

**Success criteria:**
- Page loads without errors
- Forms accept input
- Button triggers API call
- Loading state shows during processing
- Results display when received
- Styling looks professional

***

## Phase 8: Agent Visualization & Polish

### Step 8.1: Implement Live Agent Stream

**WebSocket Integration:**

```typescript
const [agentSteps, setAgentSteps] = useState([]);

useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/agent/stream');
  
  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    setAgentSteps(prev => [...prev, update]);
  };
  
  return () => ws.close();
}, []);
```

**Visual Representation:**

```
🧠 Triage Agent         [████████████] Complete (0.5s)
   → Urgency: Moderate
   → Care level: Urgent Care
   → Procedures: Exam + X-ray

💳 Insurance Agent      [████████████] Complete (0.3s)
   → Urgent care copay: $55
   → X-ray copay: $90
   → Total estimated: $145

🔍 Price Discovery      [████████████] Complete (1.2s)
   → Found 5 facilities
   → Pricing transparency: 7.8/10 avg
   → Sources: Web scraping + PDFs

⭐ Ranking Agent        [████████████] Complete (0.8s)
   → Evaluated 5 options
   → Factors: Cost, distance, quality, wait time
   → Confidence: 92%
```

### Step 8.2: Add Reasoning Transparency

**Show the AI's Thinking:**

```
💡 DECISION PROCESS

1. Urgency Classification
   "Based on symptoms, this is a moderate urgency
   injury requiring urgent care within 4 hours.
   Not life-threatening, so ER is unnecessary."

2. Cost Calculation
   "With your Anthem PPO Silver plan:
   - Urgent care visit: $55 copay
   - X-ray: $90 copay
   - Total: $145 out-of-pocket"

3. Facility Comparison
   "Evaluated 5 options on 5 factors:
   
   Carbon Health scored highest because:
   ✓ Lowest total cost ($145)
   ✓ Closest location (0.8 mi)
   ✓ Shortest wait (30 min)
   ✓ High quality (4.5⭐)
   ✓ Excellent transparency (9.2/10)"

4. Alternative Consideration
   "Exer Urgent Care is closer but costs $430
   (3x more). The extra $285 isn't worth saving
   0.4 miles of travel."
```

### Step 8.3: Add Animations

**Entrance Animations:**
- Recommendation card slides up from bottom
- Agent steps fade in sequentially (100ms stagger)
- Progress bars fill smoothly
- Check marks pop in with bounce

**Micro-interactions:**
- Hover effects on facility cards
- Button press feedback
- Copy button success animation
- Smooth scrolling to results

### Step 8.4: Mobile Optimization

**Responsive Design:**
- Stack cards vertically on mobile
- Larger tap targets for buttons
- Camera button prominent on mobile
- Simplified table view (cards instead)
- Bottom navigation for actions

### Step 8.5: Add Error States

**Handle Failures Gracefully:**

**API Timeout:**
```
⚠️ Taking longer than usual...
We're still working on your recommendation.
[View Partial Results]
```

**No Facilities Found:**
```
❌ No urgent care facilities found nearby.

Consider:
- Expanding search radius
- Trying a nearby city
- Visiting ER if urgent
```

**Insurance OCR Failed:**
```
⚠️ Couldn't read insurance card

Please:
- Retake photo with better lighting
- Or enter insurance info manually
```

***

### ✅ CHECKPOINT 8: Agent Visualization

**What you should have:**
- [ ] Live agent stream with WebSocket
- [ ] Visual progress indicators for each agent
- [ ] Reasoning transparency panel
- [ ] Smooth animations
- [ ] Mobile-responsive design
- [ ] Error handling UI

**How to verify:**
```bash
# Full stack running
cd backend && python -m uvicorn main:app --reload &
cd frontend && npm run dev

# Test sequence:
1. Upload insurance card
   → See OCR progress
   → See extracted data fill form
   
2. Enter symptoms + location
   → Click "Get Recommendation"
   
3. Watch agent stream
   → See each agent complete
   → See progress bars fill
   → See results appear
   
4. View recommendation
   → See reasoning expanded
   → See alternatives
   → Test copy button
```

**Visual quality checklist:**
- [ ] Animations are smooth (60fps)
- [ ] Progress updates feel real-time
- [ ] Colors are consistent (dark theme + cyan/emerald)
- [ ] Typography is readable
- [ ] Mobile view works well
- [ ] Loading states prevent user confusion

**Success criteria:**
- Live updates show agent progress
- Reasoning is clear and transparent
- Animations enhance (not distract from) UX
- Mobile experience is solid
- Errors handled gracefully

**🎉 MILESTONE: Full Application Working!**

You now have a complete, polished healthcare vertical agent:
- Insurance OCR with live feedback
- Multi-agent orchestration with visible reasoning
- Real-time price discovery
- Clear recommendations with alternatives
- Professional UI/UX

***

## Phase 9: Demo Polish

### Step 9.1: Create Demo Scenarios

**Pre-load 3 compelling scenarios:**

**Scenario 1: Security Leak → Savings**
```
Symptoms: "Twisted ankle running, swelling and pain"
Insurance: Anthem PPO Silver
Result: Saves $705 by going to urgent care vs ER
```

**Scenario 2: Transparency Wins**
```
Symptoms: "Sore throat 3 days, fever 101°F"
Insurance: Aetna HMO
Result: Highlights facility with best price transparency
```

**Scenario 3: Complex Multi-Factor**
```
Symptoms: "Cut hand while cooking, bled for 10 min"
Insurance: Uninsured (self-pay)
Result: Balances cost + quality + distance for uninsured
```

### Step 9.2: Record Backup Demo Video

**In case live demo fails:**

Record 90-second screen capture showing:
- (0-10s) Insurance card upload → instant extraction
- (10-30s) Symptom input → agent stream visualization
- (30-60s) Recommendation appears with full reasoning
- (60-75s) Show alternatives comparison
- (75-90s) Final prompt copy + stats

### Step 9.3: Prepare Pitch Deck

**Slide Structure:**

1. **Hook (15s)**
   - Personal story: "I paid $850 when I should have paid $145"
   - The problem: Healthcare navigation is broken

2. **Demo (60s)**
   - Live: Run Scenario 1 end-to-end
   - Show: Agent stream, reasoning, recommendation

3. **Technical Depth (20s)**
   - Architecture diagram
   - Multi-agent orchestration
   - Model routing (cost optimization)

4. **Impact (10s)**
   - 45M uninsured Americans need this
   - $400 average savings per visit
   - Scales to millions

5. **Sponsors (5s)**
   - OpenRouter: Vertical agent ✓
   - Firecrawl: Price discovery ✓
   - Reducto: Insurance OCR ✓
   - Supabase: Scaling story ✓

### Step 9.4: Practice Pitch Timing

**90-Second Breakdown:**
```
0:00-0:15  Hook (problem + personal story)
0:15-1:15  Live demo (agent in action)
1:15-1:35  Technical depth (architecture)
1:35-1:45  Impact + scaling
1:45-1:50  Sponsor relevance
1:50-2:00  Questions
```

**Practice until:**
- Stays under 2 minutes
- Demo completes smoothly
- No "umms" or filler words
- Confident delivery
- Can handle interruptions

### Step 9.5: Prepare for Judge Questions

**Expected Questions:**

**"How is this different from MDsave or Zocdoc?"**
```
Answer: "MDsave shows prices but not YOUR cost with insurance.
Zocdoc shows availability but not pricing.
We combine: your insurance + real-time pricing + urgency
+ intelligent recommendation. All in 8 seconds."
```

**"What if pricing data is stale?"**
```
Answer: "We score transparency and show data freshness.
Firecrawl helps us detect when prices haven't been updated.
We're building hourly refresh for production.
Mock data shows the concept."
```

**"Why not just use GPT-4 for everything?"**
```
Answer: "Cost optimization. DeepSeek for triage: $0.001.
Sonnet for ranking: $0.015. Total: $0.03/request.
GPT-4 everywhere: $0.45/request. That's 15x more expensive.
At scale, this matters."
```

**"How do you handle liability?"**
```
Answer: "We're an informational tool, not medical advice.
Clear disclaimers. Users make final decision.
We accelerate research, not replace doctors."
```

***

### ✅ CHECKPOINT 9: Demo Polish

**What you should have:**
- [ ] 3 demo scenarios pre-loaded
- [ ] Backup demo video recorded
- [ ] Pitch deck (5-7 slides)
- [ ] Pitch practiced and timed
- [ ] Judge Q&A prep

**How to verify:**
```bash
# Test all 3 scenarios
1. Run Scenario 1 (ankle twist)
   → Should complete in 5-8 seconds
   → Should show $705 savings
   
2. Run Scenario 2 (sore throat)
   → Should highlight transparency
   
3. Run Scenario 3 (uninsured)
   → Should work without insurance

# Time yourself
Record your pitch → Playback → Should be under 2 minutes
```

**Pitch quality checklist:**
- [ ] Opens with hook (personal story)
- [ ] Demo is smooth and fast
- [ ] Shows agent reasoning clearly
- [ ] Explains technical depth without jargon
- [ ] Articulates impact (45M users, $400 savings)
- [ ] Mentions all 4 sponsor tracks
- [ ] Stays under 2 minutes

**Success criteria:**
- All scenarios work reliably
- Pitch is memorized and confident
- Demo completes in < 10 seconds
- Backup video ready
- Can answer judge questions

***

## Phase 10: Pitch Ready & Deployment

### Step 10.1: Deploy Backend

**Options:**

**Option A: Railway/Render (Easiest)**
```
1. Push code to GitHub
2. Connect Railway to repo
3. Add environment variables
4. Deploy (auto-deploys on push)
```

**Option B: Vercel (For FastAPI)**
```
1. Install vercel CLI
2. Configure vercel.json
3. vercel deploy --prod
```

**Option C: Modal (For Python)**
```
1. Install modal
2. Add @app.function decorators
3. modal deploy
```

**Must Have:**
- All API keys in environment variables
- CORS configured for frontend domain
- Health check endpoint working
- Mock mode enabled by default

### Step 10.2: Deploy Frontend

**Vercel Deployment:**
```bash
cd frontend
vercel deploy --prod

# Configure:
- NEXT_PUBLIC_API_URL=https://your-backend.railway.app
- Auto-deploys on git push
```

**Test Deployment:**
```bash
# Visit deployed URL
curl https://clearbill-advisor.vercel.app

# Test API connection
# Should load page and connect to backend
```

### Step 10.3: Final Testing Checklist

**Functionality:**
- [ ] Insurance card OCR works (mock mode)
- [ ] Symptom analysis completes
- [ ] Price discovery returns facilities
- [ ] Recommendation displays correctly
- [ ] Agent stream shows progress
- [ ] Alternatives appear
- [ ] Copy button works
- [ ] Mobile view functional

**Performance:**
- [ ] Initial load < 2 seconds
- [ ] Recommendation completes < 10 seconds (mock)
- [ ] No console errors
- [ ] No broken images/links

**Sponsor Requirements:**
- [ ] OpenRouter: Multi-agent architecture visible ✓
- [ ] Firecrawl: Price discovery demonstrated ✓
- [ ] Reducto: Insurance OCR shown ✓
- [ ] Supabase: Scaling story in pitch ✓

### Step 10.4: Prepare Submission Materials

**Required:**
- [ ] GitHub repo URL (public)
- [ ] Live demo URL (deployed app)
- [ ] 2-minute demo video (uploaded)
- [ ] README with:
  - Project description
  - Tech stack
  - Setup instructions
  - Sponsor track relevance
  - Team members

**README Template:**
```markdown
# ClearBill Advisor

> A healthcare vertical agent that tells you where to go and what you'll pay—in seconds.

## The Problem
45 million Americans don't know where to go for care or what it will cost.
This leads to $700+ ER bills when urgent care would be $145.

## Our Solution
Multi-agent AI system that:
1. Analyzes your symptoms (triage agent)
2. Checks your insurance (benefits agent)
3. Discovers real pricing (Firecrawl)
4. Recommends best option (ranking agent)

## Tech Stack
- **OpenRouter**: Multi-agent orchestration (Haiku + Sonnet + DeepSeek)
- **Firecrawl**: Real-time price discovery
- **Reducto**: Insurance card OCR
- **Backend**: Python + FastAPI
- **Frontend**: Next.js + TypeScript + Tailwind

## Demo
[Live App](https://clearbill-advisor.vercel.app)
[Demo Video](https://youtube.com/...)

## Sponsor Tracks
- **OpenRouter**: Vertical agent with cost-optimized model routing
- **Firecrawl**: Web intelligence for hidden healthcare pricing
- **Reducto**: Document intelligence for insurance cards
- **Supabase**: Built to scale to millions of users

## Team
[Your Name] - [GitHub]
[Flatmate Name] - [GitHub]
```

### Step 10.5: Practice Final Demo

**Run Through 3 Times:**

```
Attempt 1: Note any bugs or glitches
Attempt 2: Fix issues, practice narration
Attempt 3: Record for submission

Each should:
- Complete in < 2 minutes
- Show all key features
- Highlight sponsor tech
- Feel confident and polished
```

***

### ✅ CHECKPOINT 10: Pitch Ready

**What you should have:**
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] GitHub repo public with README
- [ ] Demo video recorded and uploaded
- [ ] Pitch practiced 3+ times
- [ ] All sponsor requirements met

**How to verify (Final Check):**
```bash
# Test deployed app
1. Visit frontend URL
2. Try all 3 demo scenarios
3. Verify all features work
4. Test on mobile device
5. Check console for errors

# Test from fresh browser (incognito)
- No cached data
- Simulates judge experience
- Should load and work perfectly
```

**Submission checklist:**
- [ ] DevPost submission complete
- [ ] GitHub repo linked
- [ ] Demo video linked
- [ ] All required fields filled
- [ ] Sponsor tracks selected:
  - [ ] OpenRouter
  - [ ] Firecrawl
  - [ ] Reducto
  - [ ] Supabase

**Pitch day checklist:**
- [ ] Laptop fully charged
- [ ] Demo loaded and ready
- [ ] Backup video queued
- [ ] WiFi connection tested
- [ ] GitHub/deployed URLs bookmarked
- [ ] Pitch memorized
- [ ] Partner coordinated (if tag-team pitch)

**Success criteria:**
- App deployed and functional
- Submission complete
- Pitch polished and confident
- Ready to wow judges

**🎉 PROJECT COMPLETE!**

***

## Appendix: Time Estimates

| Checkpoint | Phase | Estimated Time |
|-----------|-------|----------------|
| 1 | Foundation | 15 min |
| 2 | Backend API | 30 min |
| 3 | Reducto OCR | 45 min |
| 4 | OpenRouter Agents | 90 min |
| 5 | Firecrawl Discovery | 60 min |
| 6 | Orchestration | 60 min |
| 7 | Frontend Dashboard | 90 min |
| 8 | Agent Visualization | 60 min |
| 9 | Demo Polish | 45 min |
| 10 | Deployment | 30 min |

**Total: ~8.5 hours** (with buffer: 10 hours)

***

## Quick Start Commands

```bash
# Setup
mkdir clearbill-advisor && cd clearbill-advisor
mkdir backend frontend docs
touch .env README.md

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn openai python-multipart
touch main.py requirements.txt

# Frontend
cd ../frontend
npx create-next-app@latest . --typescript --tailwind --app
npm install lucide-react framer-motion

# Run
# Terminal 1:
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2:
cd frontend && npm run dev
```

***

**Built for SF Hackathon 2026**

**Targeting:**
- 🏆 OpenRouter ($1,000 credits) - Vertical agent
- 🏆 Firecrawl ($5,000 + credits) - Price discovery
- 🏆 Reducto ($1,000 + credits) - Insurance OCR
- 🏆 Supabase ($1,000/person) - Scaling vision

**Expected Total: $7,000-8,000 in prizes**

**Now go build it. You have 10 hours. Clock starts now.** 🚀