#!/usr/bin/env python3

import json
import sys

# Add project path to imports
sys.path.append('/opt/feature-factory')

from app.llm.router import completion

def generate_architect_plan():
    """Generate architect plan for E2E CI test feature."""
    
    intent = {
        "action": "test_e2e_ci", 
        "params": {
            "description": "Automated E2E test feature for CI/CD pipeline", 
            "correlation_id": "c14c52d1-3207-4a94-a23a-789f65de9cce"
        }
    }
    
    messages = [
        {
            "role": "system", 
            "content": "You are an Architect AI. Your task is to generate a detailed plan (DAG of tasks) based on the provided intent. The plan should be in JSON format, strictly following the architect.plan.schema.json."
        },
        {
            "role": "user", 
            "content": f"Generate a plan for the following intent: {json.dumps(intent)}"
        }
    ]
    
    try:
        print("Generating architect plan...")
        llm_response = completion(
            role="Architect", 
            messages=messages, 
            max_tokens=4000, 
            temperature=0.7, 
            timeout_s=60
        )
        
        plan_content = llm_response['choices'][0]['message']['content']
        plan_data = json.loads(plan_content)
        
        print("\nGenerated Plan:")
        print(json.dumps(plan_data, indent=2))
        
        return plan_data
        
    except Exception as e:
        print(f"Error generating plan: {e}")
        return None

if __name__ == "__main__":
    generate_architect_plan()