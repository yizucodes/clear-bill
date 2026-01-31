import { NextResponse } from 'next/server';

// Types for the recommendation response
interface Facility {
    name: string;
    your_cost: number;
    distance: number;
    wait_time: string;
    rating: number;
    why_recommended: string[];
    address: string;
    phone: string;
    hours: string;
    facility_type: 'urgent_care' | 'emergency_room' | 'virtual_care' | 'primary_care';
}

interface Alternative {
    name: string;
    cost: number;
    distance: number;
    wait_time: string;
    facility_type: string;
}

interface AgentStep {
    step: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    duration: number;
    message: string;
}

interface RecommendationResponse {
    recommended_facility: Facility;
    alternatives: Alternative[];
    agent_steps: AgentStep[];
    urgency_level: 'low' | 'medium' | 'high' | 'emergency';
    urgency_explanation: string;
    savings_vs_er: number;
}

// Stub data - will be replaced with real agent logic
const MOCK_RECOMMENDATION: RecommendationResponse = {
    recommended_facility: {
        name: "Carbon Health Downtown",
        your_cost: 145,
        distance: 0.8,
        wait_time: "30 min",
        rating: 4.5,
        why_recommended: [
            "Lowest total cost ($145 vs $430 alternatives)",
            "Closest location (0.8 miles, 4 min drive)",
            "Shortest wait time (~30 minutes)",
            "High quality ratings (4.5/5 stars)",
            "In-network with your insurance plan"
        ],
        address: "123 Market St, San Francisco, CA 94105",
        phone: "(415) 555-0123",
        hours: "Open now · Closes 9:00 PM",
        facility_type: 'urgent_care'
    },
    alternatives: [
        {
            name: "Exer Urgent Care",
            cost: 430,
            distance: 1.2,
            wait_time: "45 min",
            facility_type: "urgent_care"
        },
        {
            name: "SF General ER",
            cost: 850,
            distance: 0.5,
            wait_time: "2-4 hours",
            facility_type: "emergency_room"
        },
        {
            name: "One Medical Virtual Visit",
            cost: 75,
            distance: 0,
            wait_time: "Available now",
            facility_type: "virtual_care"
        }
    ],
    agent_steps: [
        { step: "triage", status: "complete", duration: 500, message: "Analyzed symptoms: twisted ankle" },
        { step: "insurance", status: "complete", duration: 300, message: "Verified Blue Shield PPO coverage" },
        { step: "pricing", status: "complete", duration: 1200, message: "Compared 12 facilities in your area" },
        { step: "ranking", status: "complete", duration: 800, message: "Ranked by cost, distance, and wait time" }
    ],
    urgency_level: 'medium',
    urgency_explanation: "A twisted ankle typically requires same-day care but is not life-threatening. Urgent care is appropriate for this condition.",
    savings_vs_er: 705
};

export async function POST(request: Request) {
    try {
        const body = await request.json();

        // Log incoming request for debugging
        console.log('Received recommendation request:', body);

        // Simulate API delay for realistic UX testing
        await new Promise(resolve => setTimeout(resolve, 2000));

        // TODO: Replace with real agent logic
        // const advisor = new ClearBillAdvisor();
        // const result = await advisor.getRecommendation(body);
        // return NextResponse.json(result);

        return NextResponse.json(MOCK_RECOMMENDATION);
    } catch (error) {
        console.error('Error processing recommendation:', error);
        return NextResponse.json(
            { error: 'Failed to process recommendation request' },
            { status: 500 }
        );
    }
}
