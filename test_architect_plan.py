#!/usr/bin/env python3
"""
Simple test script to generate an architect plan for E2E CI testing
"""

import json
import requests
import sys
import os

def test_architect_plan():
    # Configuration
    base_url = "http://localhost:8000"
    
    # Create a feature first
    print("1. Creating feature...")
    feature_payload = {
        "title": f"E2E CI Test Feature",
        "intent": {
            "action": "test_e2e_ci",
            "params": {
                "description": "Automated E2E test feature for CI/CD pipeline",
                "correlation_id": "28ae6f51-26ae-405d-b5d5-e26b259028f1"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/orchestrator/features",
            headers={'Content-Type': 'application/json'},
            json=feature_payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Feature creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        feature_data = response.json()
        feature_id = feature_data['id']
        print(f"✅ Feature created with ID: {feature_id}")
        
        # Generate plan
        print("2. Generating architect plan...")
        plan_response = requests.post(
            f"{base_url}/api/v1/orchestrator/features/{feature_id}/plan",
            timeout=30
        )
        
        if plan_response.status_code != 200:
            print(f"❌ Plan generation failed: {plan_response.status_code}")
            print(f"Response: {plan_response.text}")
            return False
            
        plan_data = plan_response.json()
        print("✅ Plan generated successfully!")
        print(f"Tasks created: {len(plan_data.get('tasks', []))}")
        
        # Pretty print the plan structure
        if 'tasks' in plan_data:
            print("\nGenerated tasks:")
            for task in plan_data['tasks']:
                role = task.get('role', 'Unknown')
                name = task.get('dsl_json', {}).get('name', 'Unnamed task')
                print(f"  - {role}: {name}")
        
        if 'package_contract' in plan_data:
            print(f"\nPackage contract generated: {len(plan_data['package_contract'])} characters")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Architect AI plan generation for E2E CI...")
    success = test_architect_plan()
    
    if success:
        print("✅ Architect plan test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Architect plan test failed!")
        sys.exit(1)