#!/usr/bin/env python3
"""
Test environment variables in running service by making HTTP call.
"""

import requests
import json

def test_service_env():
    """Make API call that will trigger GitIntegrationService and check GitHub App."""
    
    print("🔍 Testing GitHub App environment in running service...")
    
    try:
        # Create a simple API call that should log GitHub App status
        response = requests.get("http://127.0.0.1:8081/api/v1/ci/debug/git-env")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Service responded:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Service error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def test_github_app_directly():
    """Test GitHub App by creating a quick test feature."""
    
    print("\n🚀 Testing GitHub App by creating test feature...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8081/api/v1/orchestrator/features",
            headers={
                "Content-Type": "application/json", 
                "X-Correlation-Id": "ENV_TEST"
            },
            json={
                "title": "ENV_TEST_GITHUB_APP",
                "intent": {"goal": "test-github-app"},
                "type": "BUSINESS", 
                "autostart": False  # Don't auto-start to avoid GitOps
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            feature_id = data.get('id')
            print(f"✅ Test feature created: #{feature_id}")
            
            # Now check if GitIntegrationService initializes with GitHub App
            # by looking at recent logs
            print("📋 Check journalctl for 'github_app_initialized' in last 1 minute")
            
        else:
            print(f"❌ Feature creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_service_env()
    test_github_app_directly()