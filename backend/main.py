"""
ClearBill Advisor - Backend API Server
A healthcare vertical agent that recommends where to go and what you'll pay.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import time
import uuid
import logging
from typing import Optional, List
from dotenv import load_dotenv

from models import (
    HealthCheckResponse,
    InsuranceOCRResponse,
    RecommendationRequest,
    RecommendationResponse,
    FacilityInfo,
    AgentStep,
    AgentStepStatus,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ClearBillAPI")

# Initialize FastAPI app
app = FastAPI(
    title="ClearBill Advisor API",
    description="Healthcare vertical agent for intelligent care recommendations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REDUCTO_API_KEY = os.getenv("REDUCTO_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Session storage (in-memory for now, would use Redis/DB in production)
active_sessions: dict = {}


# ==================== Middleware ====================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Middleware for request/response logging and error handling.
    Logs request details, timing, and any errors.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
        
        # Log response
        logger.info(f"[{request_id}] Completed {response.status_code} in {process_time:.2f}ms")
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] Error after {process_time:.2f}ms: {str(e)}")
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id}
        )


# ==================== Health Check ====================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify API is running and services are configured.
    """
    services = {
        "openrouter": bool(OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here"),
        "reducto": bool(REDUCTO_API_KEY and REDUCTO_API_KEY != "your_reducto_api_key_here"),
        "firecrawl": bool(FIRECRAWL_API_KEY and FIRECRAWL_API_KEY != "your_firecrawl_api_key_here"),
        "supabase": bool(SUPABASE_URL and SUPABASE_URL != "your_supabase_url_here"),
    }
    
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        services=services,
        timestamp=datetime.utcnow().isoformat()
    )


# ==================== Insurance OCR ====================

@app.post("/ocr/insurance-card", response_model=InsuranceOCRResponse)
async def upload_insurance_card(
    file: UploadFile = File(...),
    return_benefits: bool = True
):
    """
    Upload insurance card image for OCR extraction.
    Uses Reducto API for document intelligence.
    
    Args:
        file: Insurance card image (JPEG, PNG)
        return_benefits: Whether to extract copay/deductible information
    
    Returns:
        InsuranceOCRResponse with extracted information
    """
    # TODO: Implement Reducto OCR integration
    # This will be implemented in Phase 3
    
    return InsuranceOCRResponse(
        success=False,
        error="OCR endpoint not yet implemented - will be available in Phase 3"
    )


# ==================== Facility Recommendation ====================

@app.post("/advisor/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """
    Get intelligent facility recommendation based on symptoms, insurance, and location.
    
    This endpoint orchestrates multiple agents:
    1. Triage agent - Analyzes symptoms and determines urgency
    2. Insurance agent - Calculates expected costs
    3. Price discovery - Finds facilities and pricing (Firecrawl)
    4. Ranking agent - Recommends best option
    
    Args:
        request: RecommendationRequest with symptoms, insurance, location
    
    Returns:
        RecommendationResponse with recommended facility and reasoning
    """
    # TODO: Implement multi-agent orchestration
    # This will be implemented in Phases 4-6
    
    return RecommendationResponse(
        success=False,
        error="Recommendation endpoint not yet implemented - will be available after Phase 6"
    )


# ==================== Demo Scenarios ====================

@app.get("/demo/scenarios")
async def get_demo_scenarios():
    """
    Return predefined demo scenarios for testing and presentation.
    """
    scenarios = [
        {
            "id": 1,
            "name": "Ankle Twist → Savings",
            "symptoms": "Twisted ankle running, swelling and pain, can't put weight on it",
            "insurance": {
                "provider": "Anthem Blue Cross",
                "plan_name": "PPO Silver",
                "member_id": "ABC123456789"
            },
            "location": "San Francisco, CA",
            "expected_savings": 705
        },
        {
            "id": 2,
            "name": "Transparency Wins",
            "symptoms": "Sore throat for 3 days, fever of 101°F, difficulty swallowing",
            "insurance": {
                "provider": "Aetna",
                "plan_name": "HMO Gold",
                "member_id": "AET987654321"
            },
            "location": "Oakland, CA",
            "expected_savings": 285
        },
        {
            "id": 3,
            "name": "Uninsured Care",
            "symptoms": "Cut hand while cooking, bled for 10 minutes, might need stitches",
            "insurance": None,
            "location": "Berkeley, CA",
            "expected_savings": 430
        }
    ]
    
    return {"scenarios": scenarios}


# ==================== Facility Search ====================

@app.get("/facilities/search")
async def search_facilities(
    location: str = Query(..., description="User location (ZIP or city)"),
    procedures: str = Query(None, description="Comma-separated procedure codes"),
    use_mock: bool = Query(False, description="Use mock data for testing")
):
    """
    Search for healthcare facilities by location.
    Uses Firecrawl for real-time price discovery.
    
    Args:
        location: User's location (ZIP code or city name)
        procedures: Comma-separated CPT procedure codes (e.g., "99283,73610")
        use_mock: Whether to return mock data for testing
    
    Returns:
        Array of facilities with pricing information
    """
    # TODO: Implement Firecrawl price discovery
    # This will be implemented in Phase 5
    
    # Parse procedure codes
    procedure_list = [p.strip() for p in procedures.split(",")] if procedures else []
    
    if use_mock:
        # Return mock facility data for testing
        mock_facilities = [
            {
                "name": "Carbon Health Downtown",
                "address": "123 Market St, San Francisco, CA 94102",
                "distance_miles": 0.8,
                "drive_time_minutes": 8,
                "wait_time_minutes": 30,
                "rating": 4.5,
                "review_count": 342,
                "accepts_insurance": True,
                "pricing": {"99283": 270, "73610": 180},
                "total_cost": 450,
                "transparency_score": 9.2
            },
            {
                "name": "Exer Urgent Care Mission",
                "address": "456 Mission St, San Francisco, CA 94103",
                "distance_miles": 1.2,
                "drive_time_minutes": 12,
                "wait_time_minutes": 45,
                "rating": 4.2,
                "review_count": 218,
                "accepts_insurance": True,
                "pricing": {"99283": 430, "73610": 220},
                "total_cost": 650,
                "transparency_score": 6.5
            },
            {
                "name": "SF General Emergency Room",
                "address": "789 General Ave, San Francisco, CA 94110",
                "distance_miles": 0.5,
                "drive_time_minutes": 5,
                "wait_time_minutes": 150,
                "rating": 4.7,
                "review_count": 892,
                "accepts_insurance": True,
                "pricing": {"99283": 2850, "73610": 950},
                "total_cost": 3800,
                "transparency_score": 3.0
            }
        ]
        return {
            "success": True,
            "location": location,
            "procedures": procedure_list,
            "facilities": mock_facilities,
            "total_found": len(mock_facilities)
        }
    
    return {
        "success": False,
        "error": "Facility search not yet implemented - will be available in Phase 5",
        "location": location,
        "procedures": procedure_list
    }


# ==================== WebSocket Agent Stream ====================

@app.websocket("/agent/stream")
async def agent_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent reasoning updates.
    Streams progress updates as each agent completes its work.
    
    Message format (from server):
    {
        "type": "agent_update",
        "step": {
            "step_name": "triage",
            "status": "in_progress",
            "progress_percent": 50,
            "message": "Analyzing symptoms..."
        }
    }
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "websocket": websocket,
        "connected_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"WebSocket connected: {session_id}")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to ClearBill Advisor agent stream"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle ping/pong for connection keep-alive
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            # Handle recommendation requests via WebSocket
            elif data.get("type") == "start_recommendation":
                # TODO: Implement streaming agent orchestration in Phase 6
                await websocket.send_json({
                    "type": "agent_update",
                    "step": {
                        "step_name": "orchestration",
                        "status": "pending",
                        "progress_percent": 0,
                        "message": "Agent streaming not yet implemented - will be available in Phase 6"
                    }
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    finally:
        if session_id in active_sessions:
            del active_sessions[session_id]


# ==================== Server Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

