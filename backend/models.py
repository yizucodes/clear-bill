# ClearBill Advisor Backend - Core Data Models

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class UrgencyLevel(str, Enum):
    """Urgency classification for medical situations"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"


# ==================== Insurance Models ====================

class InsuranceBenefits(BaseModel):
    """Insurance benefit details extracted from card"""
    urgent_care_copay: Optional[float] = Field(None, description="Copay for urgent care visit")
    er_copay: Optional[float] = Field(None, description="Copay for emergency room visit")
    specialist_copay: Optional[float] = Field(None, description="Copay for specialist visit")
    deductible: Optional[float] = Field(None, description="Annual deductible amount")
    deductible_met: Optional[float] = Field(None, description="Amount of deductible already met")
    out_of_pocket_max: Optional[float] = Field(None, description="Annual out-of-pocket maximum")


class InsuranceInfo(BaseModel):
    """Insurance information from OCR or manual entry"""
    provider: str = Field(..., description="Insurance provider name (e.g., 'Anthem Blue Cross')")
    plan_name: str = Field(..., description="Plan type (e.g., 'PPO Silver')")
    member_id: str = Field(..., description="Member ID number")
    benefits: Optional[InsuranceBenefits] = Field(None, description="Benefit details")
    confidence: Optional[float] = Field(None, description="OCR confidence score (0-1)")


class InsuranceOCRRequest(BaseModel):
    """Request for insurance card OCR"""
    # File will be handled separately in FastAPI
    return_benefits: bool = Field(True, description="Whether to extract copay amounts")


class InsuranceOCRResponse(BaseModel):
    """Response from insurance card OCR"""
    success: bool = Field(..., description="Whether OCR succeeded")
    insurance: Optional[InsuranceInfo] = Field(None, description="Extracted insurance information")
    error: Optional[str] = Field(None, description="Error message if failed")


# ==================== Facility Models ====================

class FacilityInfo(BaseModel):
    """Information about a healthcare facility"""
    name: str = Field(..., description="Facility name")
    address: str = Field(..., description="Full address")
    distance_miles: float = Field(..., description="Distance from user location")
    drive_time_minutes: int = Field(..., description="Estimated drive time")
    wait_time_minutes: Optional[int] = Field(None, description="Estimated wait time")
    rating: Optional[float] = Field(None, description="Quality rating (0-5)")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    accepts_insurance: bool = Field(True, description="Whether facility accepts user's insurance")
    pricing: Dict[str, float] = Field(default_factory=dict, description="Procedure pricing")
    total_cost: float = Field(..., description="Total estimated cost for this visit")
    transparency_score: Optional[float] = Field(None, description="Price transparency score (0-10)")


# ==================== Recommendation Models ====================

class RecommendationRequest(BaseModel):
    """Request for facility recommendation"""
    symptoms: str = Field(..., description="User's symptoms description", min_length=10)
    insurance: Optional[InsuranceInfo] = Field(None, description="Insurance information")
    location: str = Field(..., description="User location (ZIP or city)")
    urgency: UrgencyLevel = Field(UrgencyLevel.MODERATE, description="Urgency level")
    use_mock: bool = Field(False, description="Whether to use mock data for testing")


class RecommendationReasoning(BaseModel):
    """Reasoning for the recommendation"""
    why_recommended: List[str] = Field(..., description="Reasons for the recommendation")
    why_not_er: Optional[str] = Field(None, description="Why ER is not necessary")
    alternative_considerations: List[str] = Field(default_factory=list, description="Why alternatives weren't chosen")


class Recommendation(BaseModel):
    """Final recommendation for user"""
    recommended_facility: FacilityInfo = Field(..., description="Primary recommended facility")
    alternatives: List[FacilityInfo] = Field(default_factory=list, description="Alternative options")
    reasoning: RecommendationReasoning = Field(..., description="Explanation of the choice")
    expected_procedures: List[str] = Field(default_factory=list, description="Expected procedures")
    timeline: str = Field(..., description="Expected timeline for care")


class RecommendationResponse(BaseModel):
    """Response from recommendation endpoint"""
    success: bool = Field(..., description="Whether recommendation was generated")
    recommendation: Optional[Recommendation] = Field(None, description="The recommendation")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: Optional[int] = Field(None, description="Time taken to process")


# ==================== Agent Stream Models ====================

class AgentStepStatus(str, Enum):
    """Status of an agent step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentStep(BaseModel):
    """Individual agent step in the orchestration"""
    step_name: str = Field(..., description="Name of the agent step")
    status: AgentStepStatus = Field(..., description="Current status")
    progress_percent: int = Field(0, description="Progress percentage (0-100)")
    message: str = Field("", description="Current status message")
    duration_ms: Optional[int] = Field(None, description="Time taken (if complete)")
    result: Optional[Dict] = Field(None, description="Result data (if complete)")


# ==================== Health Check Model ====================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field("healthy", description="API status")
    version: str = Field("1.0.0", description="API version")
    services: Dict[str, bool] = Field(default_factory=dict, description="External service status")
    timestamp: str = Field(..., description="Current timestamp")
