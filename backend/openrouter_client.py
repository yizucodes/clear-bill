"""
ClearBill Advisor - OpenRouter Client
Uses OpenRouter to access Claude for symptom enrichment and facility ranking.
"""

import os
import json
import logging
from typing import Optional, List
import httpx
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("OpenRouter")

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model configurations with fallbacks for robustness
# Order: try fast/cheap first, then fall back to alternatives
MODELS = [
    "anthropic/claude-3.5-haiku",  # Primary: fast, cheap (Haiku 3.5 is widely available)
    "anthropic/claude-3-haiku",    # Fallback 1: original Haiku
    "anthropic/claude-3.5-sonnet", # Fallback 2: more capable, slightly slower
    "openai/gpt-4o-mini",          # Fallback 3: OpenAI alternative
]

DEFAULT_MODEL = MODELS[0]  # Start with first model


# ==================== Response Models ====================

class SymptomEnrichment(BaseModel):
    """Response from symptom enrichment agent"""
    urgency: str = Field(..., description="Urgency level: low, moderate, high, emergency")
    care_level: str = Field(..., description="Care level: primary_care, urgent_care, emergency_room")
    search_queries: List[str] = Field(..., description="Search queries for finding facilities")
    expected_procedures: List[str] = Field(..., description="Expected medical procedures")
    keywords: List[str] = Field(..., description="Keywords for facility search")


class RankingResult(BaseModel):
    """Response from ranking agent"""
    recommended: dict = Field(..., description="Recommended facility details")
    reasoning: List[str] = Field(..., description="Reasons for recommendation")
    why_not_er: Optional[str] = Field(None, description="Why ER is not recommended")
    alternatives: List[dict] = Field(default_factory=list, description="Alternative facilities")


# ==================== Symptom Enricher Agent ====================

class SymptomEnricherAgent:
    """
    Agent that enriches raw symptoms for better facility search.
    Uses Claude Haiku via OpenRouter for fast, cost-effective processing.
    """
    
    SYSTEM_PROMPT = """You are a medical triage assistant. Your job is to analyze symptoms and provide structured information to help find appropriate healthcare facilities.

IMPORTANT: You are NOT diagnosing. You are only helping route to the right level of care.

For urgency levels:
- "low": Can wait 24-48 hours, minor issues
- "moderate": Should be seen today, noticeable symptoms
- "high": Should be seen within hours, concerning symptoms
- "emergency": Call 911 or go to ER immediately, life-threatening

For care levels:
- "primary_care": Family doctor, scheduled visit
- "urgent_care": Walk-in clinic, same-day care
- "emergency_room": ER, life-threatening situations only

Always return valid JSON. Be concise."""

    USER_PROMPT_TEMPLATE = """Analyze these symptoms and return JSON.

Symptoms: {symptoms}
Location: {location}

Return JSON with EXACTLY these fields:
{{
  "urgency": "low" | "moderate" | "high" | "emergency",
  "care_level": "primary_care" | "urgent_care" | "emergency_room",
  "search_queries": ["2-3 hyper-specific search queries. For injuries, include 'x-ray' or 'orthopedic'"],
  "expected_procedures": ["list of likely procedures, e.g. 'Ankle 3-view X-ray'"],
  "keywords": ["facility qualities to look for"]
}}

Return ONLY valid JSON, no markdown, no explanation."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model
        self.fallback_models = MODELS[1:]  # All models except primary
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, will use mock responses")
    
    async def enrich(self, symptoms: str, location: str) -> SymptomEnrichment:
        """
        Enrich symptoms with urgency assessment and search queries.
        
        Args:
            symptoms: Raw symptom description from user
            location: User's location (city, state or ZIP)
        
        Returns:
            SymptomEnrichment with urgency, search queries, etc.
        """
        # If no API key, return mock response
        if not self.api_key:
            logger.info("Using mock enrichment (no API key)")
            return self._get_mock_enrichment(symptoms, location)
        
        # Try primary model first, then fallbacks
        models_to_try = [self.model] + self.fallback_models
        last_error = None
        
        for model in models_to_try:
            try:
                result = await self._try_model(model, symptoms, location)
                if result:
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}. Trying next model...")
                continue
        
        # All models failed, use mock
        logger.error(f"All models failed. Last error: {last_error}. Using mock response.")
        return self._get_mock_enrichment(symptoms, location)
    
    async def _try_model(self, model: str, symptoms: str, location: str) -> Optional[SymptomEnrichment]:
        """
        Try to get enrichment from a specific model.
        Returns None if model fails, allowing fallback.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://clearbill.ai",
                    "X-Title": "ClearBill Advisor"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": self.USER_PROMPT_TEMPLATE.format(
                            symptoms=symptoms,
                            location=location
                        )}
                    ],
                    "temperature": 0.1,  # Low temperature for consistent output
                    "max_tokens": 500
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if "error" in data:
                raise Exception(f"API error: {data['error']}")
            
            # Extract the assistant's message
            content = data["choices"][0]["message"]["content"]
            logger.info(f"[{model}] OpenRouter response: {content[:200]}...")
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            
            return SymptomEnrichment(
                urgency=parsed.get("urgency", "moderate"),
                care_level=parsed.get("care_level", "urgent_care"),
                search_queries=parsed.get("search_queries", [f"urgent care near {location}"]),
                expected_procedures=parsed.get("expected_procedures", ["examination"]),
                keywords=parsed.get("keywords", ["walk-in", "same-day"])
            )
    
    def _get_mock_enrichment(self, symptoms: str, location: str) -> SymptomEnrichment:
        """
        Return mock enrichment when API is unavailable.
        Uses simple keyword matching to provide reasonable defaults.
        """
        symptoms_lower = symptoms.lower()
        
        # Emergency detection
        emergency_keywords = ["chest pain", "can't breathe", "severe bleeding", "unconscious", 
                            "stroke", "heart attack", "seizure", "allergic reaction", "anaphylaxis"]
        
        if any(kw in symptoms_lower for kw in emergency_keywords):
            return SymptomEnrichment(
                urgency="emergency",
                care_level="emergency_room",
                search_queries=[
                    f"emergency room near {location}",
                    f"hospital ER {location}"
                ],
                expected_procedures=["emergency evaluation", "immediate treatment"],
                keywords=["24/7", "emergency", "trauma center"]
            )
        
        # Ankle/Foot specific (Demo Optimization)
        if "ankle" in symptoms_lower or "foot" in symptoms_lower:
            return SymptomEnrichment(
                urgency="moderate",
                care_level="urgent_care",
                search_queries=[
                    f"urgent care with x-ray {location}",
                    f"orthopedic urgent care {location}",
                    f"walk-in clinic ankle injury {location}"
                ],
                expected_procedures=["Ankle X-ray", "Splinting", "Evaluation"],
                keywords=["X-ray on-site", "Orthopedic", "Walk-in"]
            )
        
        # High urgency detection
        high_keywords = ["high fever", "severe pain", "broken", "fracture", "deep cut", 
                        "can't walk", "vomiting blood"]
        
        if any(kw in symptoms_lower for kw in high_keywords):
            return SymptomEnrichment(
                urgency="high",
                care_level="urgent_care",
                search_queries=[
                    f"urgent care open now {location}",
                    f"walk-in clinic {location}"
                ],
                expected_procedures=["X-ray", "examination", "treatment"],
                keywords=["X-ray available", "walk-in", "open now"]
            )
        
        # Default to moderate urgency
        return SymptomEnrichment(
            urgency="moderate",
            care_level="urgent_care",
            search_queries=[
                f"urgent care {location}",
                f"walk-in clinic near {location}",
                f"same day doctor {location}"
            ],
            expected_procedures=["examination", "consultation"],
            keywords=["walk-in", "same-day", "affordable"]
        )


# ==================== Ranking Agent ====================

class RankingAgent:
    """
    Agent that ranks facilities and generates recommendation with reasoning.
    Uses Claude Haiku via OpenRouter for intelligent ranking.
    """
    
    SYSTEM_PROMPT = """You are a healthcare cost advisor. Your job is to rank healthcare facilities and recommend the best option for the patient based on cost, convenience, and appropriateness.

Always consider:
1. Total out-of-pocket cost (most important for non-emergencies)
2. Distance and wait time
3. Appropriateness for the condition
4. Patient should NOT go to ER unless it's an emergency

Be direct and helpful. Return valid JSON only."""

    USER_PROMPT_TEMPLATE = """Rank these facilities and recommend the best option.

Urgency Level: {urgency}
Insurance Copay for Urgent Care: ${copay}
Insurance Copay for ER: ${er_copay}

Facilities:
{facilities_json}

Return JSON with:
{{
  "recommended": {{
    "name": "facility name",
    "your_cost": total estimated out-of-pocket cost,
    "distance_miles": distance,
    "wait_time": "estimated wait"
  }},
  "reasoning": ["reason 1", "reason 2", "reason 3"],
  "why_not_er": "explanation why ER is not needed (if applicable)",
  "alternatives": [
    {{"name": "...", "your_cost": ..., "reason_not_top": "..."}}
  ]
}}

Return ONLY valid JSON."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model
        self.fallback_models = MODELS[1:]  # All models except primary
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, will use mock responses")
    
    async def rank(
        self, 
        facilities: List[dict], 
        insurance_copay: float, 
        er_copay: float,
        urgency: str
    ) -> RankingResult:
        """
        Rank facilities and generate recommendation.
        
        Args:
            facilities: List of facility dicts from Firecrawl
            insurance_copay: User's urgent care copay
            er_copay: User's ER copay
            urgency: Urgency level from symptom enrichment
        
        Returns:
            RankingResult with recommendation and reasoning
        """
        if not facilities:
            return self._get_empty_result()
        
        # If no API key or only one facility, use simple ranking
        if not self.api_key or len(facilities) == 1:
            logger.info("Using mock ranking")
            return self._get_mock_ranking(facilities, insurance_copay, er_copay, urgency)
        
        # Try primary model first, then fallbacks
        models_to_try = [self.model] + self.fallback_models
        last_error = None
        
        for model in models_to_try:
            try:
                result = await self._try_rank_model(model, facilities, insurance_copay, er_copay, urgency)
                if result:
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Ranking model {model} failed: {e}. Trying next model...")
                continue
        
        # All models failed, use mock ranking
        logger.error(f"All ranking models failed. Last error: {last_error}. Using mock ranking.")
        return self._get_mock_ranking(facilities, insurance_copay, er_copay, urgency)
    
    async def _try_rank_model(
        self, 
        model: str, 
        facilities: List[dict], 
        insurance_copay: float, 
        er_copay: float,
        urgency: str
    ) -> Optional[RankingResult]:
        """Try ranking with a specific model."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://clearbill.ai",
                    "X-Title": "ClearBill Advisor"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": self.USER_PROMPT_TEMPLATE.format(
                            urgency=urgency,
                            copay=insurance_copay,
                            er_copay=er_copay,
                            facilities_json=json.dumps(facilities, indent=2)
                        )}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if "error" in data:
                raise Exception(f"API error: {data['error']}")
            
            content = data["choices"][0]["message"]["content"]
            logger.info(f"[{model}] Ranking response: {content[:200]}...")
            
            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            
            # Rehydrate/Normalize data from source facilities
            # The LLM might hallucinate or omit fields like distance_miles
            recommended = parsed.get("recommended", {})
            self._hydrate_facility_data(recommended, facilities)
            
            alternatives = parsed.get("alternatives", [])
            for alt in alternatives:
                self._hydrate_facility_data(alt, facilities)
            
            return RankingResult(
                recommended=recommended,
                reasoning=parsed.get("reasoning", []),
                why_not_er=parsed.get("why_not_er"),
                alternatives=alternatives
            )

    def _hydrate_facility_data(self, target: dict, sources: List[dict]):
        """Inject valid data (distance, wait_time, address, url) from source facilities into LLM result."""
        if not target or not sources:
            return

        target_name = target.get("name", "").lower()
        target_url = target.get("url", "").lower()

        # Find best match - prioritize URL match (more unique), then name
        best_match = None

        # First pass: exact URL match (most reliable)
        if target_url:
            for source in sources:
                src_url = source.get("url", "").lower()
                if src_url and (src_url == target_url or target_url in src_url or src_url in target_url):
                    best_match = source
                    break

        # Second pass: name + address combo (for chain locations)
        if not best_match:
            target_address = target.get("address", "").lower()
            for source in sources:
                src_name = source.get("name", "").lower()
                src_address = source.get("address", "").lower()
                # If addresses match, use this source
                if target_address and src_address and target_address in src_address:
                    best_match = source
                    break
                # Otherwise, require more specific name match
                if src_name == target_name:  # Exact match only
                    best_match = source
                    break

        # Third pass: substring match (fallback, less reliable for chains)
        if not best_match:
            for source in sources:
                src_name = source.get("name", "").lower()
                if src_name in target_name or target_name in src_name:
                    best_match = source
                    break
        
        if best_match:
            # Inject trusted data if missing or null in target
            if not target.get("distance_miles") and "distance_miles" in best_match:
                target["distance_miles"] = best_match["distance_miles"]

            if not target.get("wait_time") and "wait_time" in best_match:
                target["wait_time"] = best_match["wait_time"]

            # Inject address for UX credibility
            if not target.get("address") and best_match.get("address"):
                target["address"] = best_match["address"]

            # Inject URL for "Visit Website" button
            if not target.get("url") and best_match.get("url"):
                target["url"] = best_match["url"]
            
            # Fix keys (LLM sometimes uses 'distance' instead of 'distance_miles')
            if "distance" in target and not target.get("distance_miles"):
                target["distance_miles"] = target["distance"]
    
    def _get_empty_result(self) -> RankingResult:
        """Return empty result when no facilities found."""
        return RankingResult(
            recommended={
                "name": "No facilities found",
                "your_cost": 0,
                "distance_miles": 0,
                "wait_time": "N/A"
            },
            reasoning=["No facilities were found matching your search criteria"],
            why_not_er=None,
            alternatives=[]
        )
    
    def _get_mock_ranking(
        self, 
        facilities: List[dict], 
        copay: float, 
        er_copay: float,
        urgency: str
    ) -> RankingResult:
        """
        Simple cost-based ranking when API is unavailable.
        """
        # Sort by total cost (prefer lower cost)
        sorted_facilities = sorted(
            facilities, 
            key=lambda f: f.get("total_cost", f.get("pricing", {}).get("urgent_care", 300))
        )
        
        top = sorted_facilities[0]
        top_cost = top.get("total_cost", 0)
        
        # Calculate user's out-of-pocket cost
        if "emergency" in top.get("name", "").lower() or top.get("type") == "er":
            user_cost = top_cost + er_copay if copay else top_cost
        else:
            user_cost = copay if copay else top_cost
        
        return RankingResult(
            recommended={
                "name": top.get("name", "Unknown Facility"),
                "your_cost": user_cost,
                "distance_miles": top.get("distance_miles", 0),
                "wait_time": f"{top.get('wait_time_minutes', 30)} min"
            },
            reasoning=[
                f"Lowest estimated cost (${user_cost:.0f})",
                f"Closest location ({top.get('distance_miles', 0):.1f} miles)",
                "Appropriate care level for your symptoms"
            ],
            why_not_er="Your condition doesn't require emergency care. ER would cost significantly more with longer wait times." if urgency != "emergency" else None,
            alternatives=[
                {
                    "name": f.get("name"),
                    "your_cost": f.get("total_cost", 0),
                    "address": f.get("address"),
                    "distance_miles": f.get("distance_miles"),
                    "wait_time": f.get("wait_time"),
                    "url": f.get("url"),
                    "reason_not_top": "Higher cost" if f.get("total_cost", 0) > top_cost else "Further away"
                }
                for f in sorted_facilities[1:3]
            ]
        )


# ==================== Test Function ====================

async def test_enricher():
    """Test the symptom enricher agent."""
    agent = SymptomEnricherAgent()
    result = await agent.enrich(
        symptoms="Twisted ankle, swelling and bruising, hurts to walk",
        location="San Francisco, CA"
    )
    print("=" * 50)
    print("SYMPTOM ENRICHMENT TEST")
    print("=" * 50)
    print(f"Urgency: {result.urgency}")
    print(f"Care Level: {result.care_level}")
    print(f"Search Queries: {result.search_queries}")
    print(f"Expected Procedures: {result.expected_procedures}")
    print(f"Keywords: {result.keywords}")
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enricher())
