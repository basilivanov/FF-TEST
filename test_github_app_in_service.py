#!/usr/bin/env python3
"""
Test GitHub App authentication within the running service environment.
"""

import sys
sys.path.append('/opt/feature-factory')

import os
import requests
from app.services.git_integration import GitIntegrationService

def main():
    print("🔍 Testing GitHub App integration within service...")
    
    # Check environment variables
    print(f"GITHUB_APP_ID: {os.getenv('GITHUB_APP_ID', 'NOT SET')}")
    print(f"GITHUB_APP_INSTALLATION_ID: {os.getenv('GITHUB_APP_INSTALLATION_ID', 'NOT SET')}")
    print(f"GITHUB_APP_PRIVATE_KEY_PATH: {os.getenv('GITHUB_APP_PRIVATE_KEY_PATH', 'NOT SET')}")
    print(f"GITHUB_TOKEN: {'SET' if os.getenv('GITHUB_TOKEN') else 'NOT SET'}")
    
    # Manually set environment variables for testing
    print("\n📝 Setting GitHub App environment variables manually...")
    os.environ['GITHUB_APP_ID'] = '1951709'
    os.environ['GITHUB_APP_INSTALLATION_ID'] = '85882340'
    os.environ['GITHUB_APP_PRIVATE_KEY_PATH'] = '/etc/feature-factory/github-app-private-key.pem'
    
    try:
        # Initialize GitIntegrationService
        print("🚀 Initializing GitIntegrationService...")
        git_service = GitIntegrationService()
        
        # Test authentication method
        print("🔐 Testing authentication headers...")
        headers = git_service._get_auth_headers("TEST_CORRELATION_ID")
        
        print(f"✅ Auth headers generated successfully!")
        print(f"🎯 Authorization header: {headers['Authorization'][:50]}...")
        print(f"👤 User-Agent: {headers['User-Agent']}")
        
        # Test API call on repository (what we actually need)
        print("\n🧪 Testing GitHub API call on repository...")
        response = requests.get("https://api.github.com/repos/basilivanov/FF-TEST", headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ GitHub API call successful!")
            print(f"📁 Repository: {repo_data['full_name']}")
            print(f"🔧 Permissions: {repo_data.get('permissions', {})}")
            print(f"🔢 Rate limit remaining: {response.headers.get('x-ratelimit-remaining')}")
        else:
            print(f"❌ GitHub API call failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
        # Also test PR creation endpoint (dry run)
        print("\n🧪 Testing PR API access (GET only)...")
        response = requests.get("https://api.github.com/repos/basilivanov/FF-TEST/pulls", headers=headers)
        
        if response.status_code == 200:
            prs = response.json()
            print(f"✅ PR API access successful! Found {len(prs)} PRs")
        else:
            print(f"❌ PR API access failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()