"""
ClearBill Advisor - Main Orchestrator

Coordinates the multi-agent pipeline:
1. Symptom Enrichment (OpenRouter)
2. Facility Search (Firecrawl)
3. Ranking & Recommendation (OpenRouter)
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from openrouter_client import SymptomEnricherAgent, RankingAgent, SymptomEnrichment, RankingResult
from firecrawl_client import FirecrawlClient

logger = logging.getLogger("ClearBillAdvisor")

# Insurance copay lookup
# Source: Common copay amounts from major insurers (2024)
INSURANCE_COPAYS = {
    "anthem_ppo": {"urgent_care": 55, "er": 250, "primary_care": 30},
    "anthem_hmo": {"urgent_care": 45, "er": 200, "primary_care": 25},
    "bcbs_ppo": {"urgent_care": 60, "er": 275, "primary_care": 35},
    "bcbs_hmo": {"urgent_care": 40, "er": 200, "primary_care": 20},
    "aetna_ppo": {"urgent_care": 60, "er": 275, "primary_care": 35},
    "aetna_hmo": {"urgent_care": 45, "er": 225, "primary_care": 25},
    "cigna_ppo": {"urgent_care": 55, "er": 250, "primary_care": 30},
    "cigna_hmo": {"urgent_care": 40, "er": 200, "primary_care": 20},
    "unitedhealth_ppo": {"urgent_care": 60, "er": 275, "primary_care": 35},
    "unitedhealth_hmo": {"urgent_care": 45, "er": 225, "primary_care": 25},
    "kaiser": {"urgent_care": 35, "er": 150, "primary_care": 20},
    "medicare": {"urgent_care": 0, "er": 0, "primary_care": 0},
    "uninsured": None  # Use cash prices
}


@dataclass
class AdvisorResult:
    """Result from the ClearBill Advisor"""
    success: bool
    recommended: Optional[Dict] = None
    reasoning: Optional[List[str]] = None
    why_not_er: Optional[str] = None
    alternatives: Optional[List[Dict]] = None
    urgency: Optional[str] = None
    care_level: Optional[str] = None
    expected_procedures: Optional[List[str]] = None
    data_quality: Optional[str] = None
    disclaimer: Optional[str] = None
    processing_time_ms: Optional[int] = None
    phases: Optional[Dict] = None
    error: Optional[str] = None


class ClearBillAdvisor:
    """
    Main orchestrator that coordinates the multi-agent healthcare recommendation system.
    
    Pipeline:
    1. SymptomEnricherAgent - Analyzes symptoms → urgency, search queries
    2. FirecrawlClient - Searches facilities → real pricing data
    3. RankingAgent - Ranks facilities → recommendation with reasoning
    """
    
    def __init__(self):
        # Phase 1: Fast Triage (Haiku)
        self.symptom_agent = SymptomEnricherAgent(model="anthropic/claude-3.5-haiku")
        
        # Phase 2 & 3: Firecrawl Discovery
        self.firecrawl = FirecrawlClient()
        
        # Phase 4: High Reasoning (DeepSeek R1)
        self.ranking_agent = RankingAgent(model="deepseek/deepseek-r1")
        
        logger.info("ClearBillAdvisor initialized with all agents")
    
    async def get_recommendation(
        self,
        symptoms: str,
        location: str,
        insurance_plan: Optional[str] = None
    ) -> AdvisorResult:
        """
        Get a complete healthcare facility recommendation.
        
        Args:
            symptoms: User's symptom description
            location: User's location (city, state or ZIP)
            insurance_plan: Insurance plan key (e.g., "anthem_ppo") or None for uninsured
        
        Returns:
            AdvisorResult with recommendation, reasoning, and alternatives
        """
        start_time = time.time()
        phases = {}
        
        try:
            # ==================== PHASE 1: Symptom Enrichment ====================
            logger.info(f"Phase 1: Enriching symptoms for '{symptoms[:50]}...'")
            phase1_start = time.time()
            
            enrichment = await self.symptom_agent.enrich(symptoms, location)
            
            phases["symptom_enrichment"] = {
                "status": "success",
                "duration_ms": int((time.time() - phase1_start) * 1000),
                "urgency": enrichment.urgency,
                "care_level": enrichment.care_level,
                "search_queries": enrichment.search_queries
            }
            
            logger.info(f"Phase 1 complete: urgency={enrichment.urgency}, care_level={enrichment.care_level}")
            
            # Handle emergency case
            if enrichment.urgency == "emergency":
                return AdvisorResult(
                    success=True,
                    recommended={
                        "name": "CALL 911 or go to nearest Emergency Room",
                        "your_cost": "N/A - this is an emergency",
                        "distance_miles": 0,
                        "wait_time": "Immediate"
                    },
                    reasoning=[
                        "Your symptoms indicate a medical emergency",
                        "Emergency care is the appropriate level of care",
                        "Do not delay - seek immediate medical attention"
                    ],
                    urgency="emergency",
                    care_level="emergency_room",
                    expected_procedures=enrichment.expected_procedures,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    phases=phases
                )
            
            # ==================== PHASE 2: Facility Search ====================
            logger.info(f"Phase 2: Searching facilities with query: {enrichment.search_queries[0]}")
            phase2_start = time.time()
            
            search_result = await self.firecrawl.search_and_enrich(
                queries=enrichment.search_queries,
                location=location,
                expected_procedures=enrichment.expected_procedures,
                top_n=5  # Get top 5 for ranking
            )
            
            facilities = search_result.get("facilities", [])
            
            phases["facility_search"] = {
                "status": "success" if facilities else "no_results",
                "duration_ms": int((time.time() - phase2_start) * 1000),
                "facilities_found": len(facilities),
                "data_quality": search_result.get("data_quality", "unknown")
            }
            
            logger.info(f"Phase 2 complete: found {len(facilities)} facilities")
            
            if not facilities:
                return AdvisorResult(
                    success=False,
                    error="No facilities found matching your search. Please try a different location.",
                    urgency=enrichment.urgency,
                    care_level=enrichment.care_level,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    phases=phases
                )
            
            # ==================== PHASE 3: Get Insurance Copays ====================
            copay_info = self._get_copay(insurance_plan)
            urgent_care_copay = copay_info.get("urgent_care", 0) if copay_info else 0
            er_copay = copay_info.get("er", 0) if copay_info else 0
            
            # Prepare facilities with cost calculation
            enriched_facilities = self._calculate_user_costs(
                facilities, 
                urgent_care_copay, 
                copay_info is None  # is_uninsured
            )
            
            phases["cost_calculation"] = {
                "status": "success",
                "insurance_plan": insurance_plan,
                "urgent_care_copay": urgent_care_copay,
                "er_copay": er_copay,
                "is_uninsured": copay_info is None
            }
            
            # ==================== PHASE 4: Ranking & Recommendation ====================
            logger.info("Phase 4: Ranking facilities and generating recommendation")
            phase4_start = time.time()
            
            ranking = await self.ranking_agent.rank(
                facilities=enriched_facilities,
                insurance_copay=urgent_care_copay,
                er_copay=er_copay,
                urgency=enrichment.urgency,
                care_level=enrichment.care_level
            )
            
            phases["ranking"] = {
                "status": "success",
                "duration_ms": int((time.time() - phase4_start) * 1000)
            }
            
            logger.info(f"Phase 4 complete: recommended {ranking.recommended.get('name', 'Unknown')}")
            
            # ==================== BUILD FINAL RESULT ====================
            total_time = int((time.time() - start_time) * 1000)
            
            return AdvisorResult(
                success=True,
                recommended=ranking.recommended,
                reasoning=ranking.reasoning,
                why_not_er=ranking.why_not_er,
                alternatives=ranking.alternatives,
                urgency=enrichment.urgency,
                care_level=enrichment.care_level,
                expected_procedures=enrichment.expected_procedures,
                data_quality=search_result.get("data_quality", "unknown"),
                disclaimer=search_result.get("disclaimer", ""),
                processing_time_ms=total_time,
                phases=phases
            )
            
        except Exception as e:
            logger.error(f"Error in get_recommendation: {e}", exc_info=True)
            return AdvisorResult(
                success=False,
                error=f"An error occurred: {str(e)}",
                processing_time_ms=int((time.time() - start_time) * 1000),
                phases=phases
            )
    
    def _get_copay(self, insurance_plan: Optional[str]) -> Optional[Dict]:
        """Get copay information for an insurance plan."""
        if not insurance_plan:
            return None
        
        # Normalize the plan name
        plan_key = insurance_plan.lower().replace(" ", "_").replace("-", "_")
        
        # Try exact match first
        if plan_key in INSURANCE_COPAYS:
            return INSURANCE_COPAYS[plan_key]
        
        # Try partial match
        for key in INSURANCE_COPAYS:
            if key in plan_key or plan_key in key:
                return INSURANCE_COPAYS[key]
        
        # Default to moderate copays
        return {"urgent_care": 50, "er": 250, "primary_care": 30}
    
    def _calculate_user_costs(
        self, 
        facilities: List[Dict], 
        copay: float,
        is_uninsured: bool
    ) -> List[Dict]:
        """Calculate user's out-of-pocket costs for each facility."""
        enriched = []
        
        for facility in facilities:
            pricing = facility.get("pricing", {})
            base_visit = pricing.get("urgent_care_visit", 270)
            xray_cost = pricing.get("xray", 180)
            
            if is_uninsured:
                # Full cost for uninsured
                total_cost = base_visit + xray_cost
            else:
                # Copay + any remaining costs
                total_cost = copay + (xray_cost * 0.2)  # Assume 20% coinsurance for procedures
            
            enriched.append({
                **facility,
                "total_cost": round(total_cost, 2),
                "user_cost_breakdown": {
                    "copay": copay if not is_uninsured else 0,
                    "visit_cost": base_visit,
                    "xray_cost": xray_cost,
                    "estimated_total": round(total_cost, 2)
                }
            })
        
        return enriched


# ==================== Convenience Function ====================

async def get_healthcare_recommendation(
    symptoms: str,
    location: str,
    insurance_plan: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for getting a healthcare recommendation.
    
    Returns a dictionary suitable for JSON serialization.
    """
    advisor = ClearBillAdvisor()
    result = await advisor.get_recommendation(symptoms, location, insurance_plan)
    
    return {
        "success": result.success,
        "recommended": result.recommended,
        "reasoning": result.reasoning,
        "why_not_er": result.why_not_er,
        "alternatives": result.alternatives,
        "urgency": result.urgency,
        "care_level": result.care_level,
        "expected_procedures": result.expected_procedures,
        "data_quality": result.data_quality,
        "disclaimer": result.disclaimer,
        "processing_time_ms": result.processing_time_ms,
        "phases": result.phases,
        "error": result.error
    }


# ==================== Test ====================

async def test_advisor():
    """Test the complete advisor pipeline."""
    print("=" * 60)
    print("CLEARBILL ADVISOR - FULL PIPELINE TEST")
    print("=" * 60)
    
    advisor = ClearBillAdvisor()
    
    # Test Case 1: Ankle injury with insurance
    print("\n📋 Test Case 1: Ankle Injury with Anthem PPO")
    print("-" * 40)
    
    result1 = await advisor.get_recommendation(
        symptoms="Twisted my ankle running, swelling and pain, can't walk properly",
        location="San Francisco, CA",
        insurance_plan="anthem_ppo"
    )
    
    print(f"✅ Success: {result1.success}")
    print(f"🚨 Urgency: {result1.urgency}")
    print(f"🏥 Care Level: {result1.care_level}")
    
    if result1.recommended:
        print(f"\n🎯 RECOMMENDED: {result1.recommended.get('name')}")
        print(f"   💰 Your Cost: ${result1.recommended.get('your_cost', 'N/A')}")
        print(f"   📍 Distance: {result1.recommended.get('distance_miles', 'N/A')} miles")
    
    if result1.reasoning:
        print(f"\n📝 REASONING:")
        for reason in result1.reasoning[:3]:
            print(f"   • {reason}")
    
    if result1.why_not_er:
        print(f"\n❌ WHY NOT ER: {result1.why_not_er}")
    
    print(f"\n⏱️  Processing Time: {result1.processing_time_ms}ms")
    print(f"📊 Data Quality: {result1.data_quality}")
    
    # Test Case 2: Uninsured
    print("\n\n📋 Test Case 2: Sore Throat (Uninsured)")
    print("-" * 40)
    
    result2 = await advisor.get_recommendation(
        symptoms="Sore throat for 3 days, mild fever",
        location="San Francisco, CA",
        insurance_plan=None  # Uninsured
    )
    
    print(f"✅ Success: {result2.success}")
    print(f"🚨 Urgency: {result2.urgency}")
    
    if result2.recommended:
        print(f"🎯 RECOMMENDED: {result2.recommended.get('name')}")
        print(f"   💰 Your Cost: ${result2.recommended.get('your_cost', 'N/A')}")
    
    print(f"⏱️  Processing Time: {result2.processing_time_ms}ms")
    
    return result1, result2


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_advisor())
