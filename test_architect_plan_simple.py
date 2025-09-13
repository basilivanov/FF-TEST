#!/usr/bin/env python3
"""
Simple test script to generate an architect plan directly
"""

import json
import requests
import sys
import os
import time

def test_plan_generation_only():
    """Test just the plan generation on an existing feature"""
    base_url = "http://localhost:8000"
    
    # First, let's check if there's an existing feature we can use
    try:
        # Get existing features
        response = requests.get(f"{base_url}/api/v1/orchestrator/features", timeout=10)
        if response.status_code == 200:
            features = response.json()
            if features:
                feature_id = features[-1]['id']  # Use the latest feature
                print(f"Using existing feature ID: {feature_id}")
                
                # Generate plan for this feature
                print("Generating architect plan...")
                plan_response = requests.post(
                    f"{base_url}/api/v1/orchestrator/features/{feature_id}/plan",
                    timeout=30
                )
                
                if plan_response.status_code == 200:
                    plan_data = plan_response.json()
                    print("✅ Plan generated successfully!")
                    
                    # Display results
                    if 'tasks' in plan_data:
                        print(f"\nTasks created: {len(plan_data['tasks'])}")
                        for i, task in enumerate(plan_data['tasks'], 1):
                            role = task.get('role', 'Unknown')
                            task_name = task.get('dsl_json', {}).get('name', 'Unnamed')
                            print(f"  {i}. {role}: {task_name}")
                    
                    if 'package_contract' in plan_data:
                        print(f"\nPackage contract: {len(str(plan_data['package_contract']))} characters")
                        
                    return True
                else:
                    print(f"❌ Plan generation failed: {plan_response.status_code}")
                    print(f"Response: {plan_response.text}")
                    return False
                    
        # If no existing features, create one
        print("No existing features found, creating new one...")
        return create_feature_and_plan()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_feature_and_plan():
    """Create a new feature and generate plan"""
    base_url = "http://localhost:8000"
    
    feature_payload = {
        "title": f"Test E2E CI Feature {int(time.time())}",
        "intent": {
            "action": "test_e2e_ci",
            "params": {
                "description": "Simple test of E2E CI pipeline automation",
                "correlation_id": f"test-{int(time.time())}"
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
        
        print(f"Feature creation response: {response.status_code}")
        if response.status_code == 200:
            feature_data = response.json()
            feature_id = feature_data['id']
            print(f"✅ Feature created: {feature_id}")
            
            # Now generate plan
            print("Generating plan...")
            plan_response = requests.post(
                f"{base_url}/api/v1/orchestrator/features/{feature_id}/plan",
                timeout=60
            )
            
            if plan_response.status_code == 200:
                plan_data = plan_response.json()
                print("✅ Plan generated!")
                return True
            else:
                print(f"❌ Plan failed: {plan_response.status_code} - {plan_response.text}")
                return False
        else:
            print(f"❌ Feature creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing Architect AI plan generation...")
    success = test_plan_generation_only()
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)