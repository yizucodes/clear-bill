# ClearBill Advisor

> A healthcare vertical agent that tells you where to go and what you'll pay—in seconds.

## The Problem

45 million Americans don't know where to go for care or what it will cost. This leads to $700+ ER bills when urgent care would be $145. Healthcare navigation is broken.

## Our Solution

ClearBill Advisor is a multi-agent AI system that:

1. **Analyzes your symptoms** (triage agent)
2. **Checks your insurance** (benefits agent via OCR)
3. **Discovers real pricing** (Firecrawl web intelligence)
4. **Recommends best option** (ranking agent)

All in under 10 seconds.

## Tech Stack

### Backend
- **Python + FastAPI** - High-performance async API server
- **OpenRouter** - Multi-agent orchestration (Haiku + Sonnet + DeepSeek)
- **Reducto** - Insurance card OCR with document intelligence
- **Firecrawl** - Real-time price discovery from websites

### Frontend
- **Next.js** - React framework with TypeScript
- **Tailwind CSS** - Modern, responsive styling
- **Framer Motion** - Smooth animations

### Optional
- **Supabase** - Caching and scaling infrastructure

## Project Structure

```
clearbill-advisor/
├── backend/              # Python FastAPI server
│   ├── main.py          # API endpoints and orchestration
│   ├── agents/          # Individual agent implementations
│   ├── models.py        # Data models
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js React app
│   ├── app/            # Next.js 14 app directory
│   ├── components/     # React components
│   └── public/         # Static assets
├── docs/               # Pitch deck and demo assets
├── .env                # Environment variables (not committed)
└── README.md           # This file
```

## Core Data Models

### Insurance Information
- Provider name (e.g., "Anthem Blue Cross")
- Plan type (e.g., "PPO Silver")
- Member ID
- Copay amounts (urgent care, ER, specialist)
- Deductible information

### Facility Information
- Name (e.g., "Carbon Health Downtown")
- Address and distance from user
- Pricing for procedures
- Wait time estimate
- Quality rating
- Accepts insurance (yes/no)

### Recommendation
- Recommended facility
- Estimated out-of-pocket cost
- Reasoning for the choice
- Alternative options
- What to expect (procedures, timeline)

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- API keys for OpenRouter, Reducto, and Firecrawl

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Environment Variables

Copy `.env` to the project root and fill in your API keys:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
REDUCTO_API_KEY=your_reducto_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
SUPABASE_URL=your_supabase_url_here  # Optional
SUPABASE_KEY=your_supabase_key_here  # Optional
```

## Usage

1. **Upload Insurance Card** - Snap a photo or upload an image
2. **Describe Symptoms** - Free-form text description of your issue
3. **Enter Location** - ZIP code or city
4. **Get Recommendation** - See where to go and what you'll pay

## Sponsor Track Relevance

### OpenRouter ($1,000 credits)
- **Vertical agent architecture** - Multi-agent orchestration for healthcare
- **Cost-optimized model routing** - DeepSeek for triage ($0.001), Sonnet for ranking ($0.015)
- **15x cost reduction** vs. GPT-4 everywhere

### Firecrawl ($5,000 + credits)
- **Web intelligence** - Real-time price discovery from facility websites
- **Hidden data extraction** - Finding pricing PDFs and transparency documents
- **Transparency scoring** - Rating facilities on data freshness and availability

### Reducto ($1,000 + credits)
- **Document intelligence** - OCR extraction from insurance cards
- **Multi-field extraction** - Provider, plan type, copays, deductibles
- **Mobile-first** - Camera integration for instant capture

### Supabase ($1,000/person)
- **Scaling vision** - Built to handle millions of users
- **Caching layer** - Price data and facility information
- **Real-time features** - Live agent stream visualization

## Demo Scenarios

### Scenario 1: Ankle Twist → Savings
- **Symptoms**: "Twisted ankle running, swelling and pain"
- **Insurance**: Anthem PPO Silver
- **Result**: Saves $705 by going to urgent care vs ER

### Scenario 2: Transparency Wins
- **Symptoms**: "Sore throat 3 days, fever 101°F"
- **Insurance**: Aetna HMO
- **Result**: Highlights facility with best price transparency

### Scenario 3: Uninsured Care
- **Symptoms**: "Cut hand while cooking, bled for 10 min"
- **Insurance**: Self-pay
- **Result**: Balances cost + quality + distance for uninsured

## Development Roadmap

- [x] Phase 1: Project Foundation
- [ ] Phase 2: Backend API Architecture
- [ ] Phase 3: Reducto Insurance OCR
- [ ] Phase 4: OpenRouter Agent System
- [ ] Phase 5: Firecrawl Price Discovery
- [ ] Phase 6: Agent Orchestration
- [ ] Phase 7: Frontend Dashboard
- [ ] Phase 8: Agent Visualization
- [ ] Phase 9: Demo Polish
- [ ] Phase 10: Deployment

## Team

Built for SF Hackathon 2026

## License

MIT License - See LICENSE file for details
