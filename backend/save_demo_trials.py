import asyncio
import json
import os
from advisor import ClearBillAdvisor, get_healthcare_recommendation
from datetime import datetime

async def save_trials():
    # Ensure directory exists
    output_dir = "test_trials"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    scenarios = [
        {
            "name": "ankle_injury_anthem",
            "symptoms": "Twisted ankle running, swelling and pain, can't walk properly",
            "location": "San Francisco, CA",
            "insurance_plan": "anthem_ppo"
        },
        {
            "name": "chest_pain_emergency",
            "symptoms": "Chest pain, shortness of breath, left arm tingling",
            "location": "San Francisco, CA",
            "insurance_plan": "anthem_ppo"
        },
        {
            "name": "sore_throat_uninsured",
            "symptoms": "Sore throat for 3 days, mild fever",
            "location": "San Francisco, CA",
            "insurance_plan": None
        }
    ]
    
    results = {}
    
    print(f"Running {len(scenarios)} test trials...")
    
    for sc in scenarios:
        print(f"Running scenario: {sc['name']}...")
        result = await get_healthcare_recommendation(
            symptoms=sc['symptoms'],
            location=sc['location'],
            insurance_plan=sc['insurance_plan']
        )
        
        # Add metadata
        result["scenario_input"] = sc
        results[sc['name']] = result
        
        # Save individual file
        filename = f"{output_dir}/{sc['name']}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved to {filename}")

if __name__ == "__main__":
    asyncio.run(save_trials())
