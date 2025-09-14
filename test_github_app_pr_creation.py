#!/usr/bin/env python3
"""
Test actual PR creation with GitHub App - bypass permissions check.
"""

import sys
sys.path.append('/opt/feature-factory')

import os
import requests
import json
import time
from app.services.git_integration import GitIntegrationService

def main():
    print("🚀 Testing GitHub App PR creation directly...")
    
    # Set environment variables
    os.environ['GITHUB_APP_ID'] = '1951709'
    os.environ['GITHUB_APP_INSTALLATION_ID'] = '85882340'
    os.environ['GITHUB_APP_PRIVATE_KEY_PATH'] = '/etc/feature-factory/github-app-private-key.pem'
    os.environ['GITHUB_OWNER'] = 'basilivanov'
    os.environ['GITHUB_REPO'] = 'FF-TEST'
    
    try:
        # Initialize service
        git_service = GitIntegrationService()
        
        # Get auth headers
        headers = git_service._get_auth_headers("PR_TEST")
        
        print(f"🔐 Got GitHub App token: {headers['Authorization'][:50]}...")
        
        # Test simple repository info
        print("\n1️⃣ Testing repository access...")
        response = requests.get("https://api.github.com/repos/basilivanov/FF-TEST", headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository: {repo_data['full_name']}")
            print(f"🌟 Default branch: {repo_data['default_branch']}")
        else:
            print(f"❌ Repository access failed: {response.status_code}")
            return
            
        # Test branches access
        print("\n2️⃣ Testing branches access...")
        response = requests.get("https://api.github.com/repos/basilivanov/FF-TEST/branches", headers=headers)
        if response.status_code == 200:
            branches = response.json()
            print(f"✅ Found {len(branches)} branches")
            branch_names = [b['name'] for b in branches[:3]]
            print(f"📝 First 3 branches: {', '.join(branch_names)}")
        else:
            print(f"❌ Branches access failed: {response.status_code}")
            return
            
        # Test PR creation (with unique title)
        print("\n3️⃣ Testing PR creation...")
        
        test_pr_data = {
            "title": f"Test GitHub App PR #{int(time.time())}",
            "head": "feature/79_github_app_e2e_test",  # Existing branch
            "base": "main",
            "body": "Test PR created by GitHub App to verify write permissions.\n\nThis PR tests that GitHub App can create PRs with write access.",
            "draft": True  # Make it draft so it doesn't clutter
        }
        
        print(f"📝 Creating PR: {test_pr_data['title']}")
        print(f"🌿 Head: {test_pr_data['head']} -> Base: {test_pr_data['base']}")
        
        response = requests.post(
            "https://api.github.com/repos/basilivanov/FF-TEST/pulls", 
            headers=headers, 
            json=test_pr_data
        )
        
        if response.status_code == 201:
            pr_data = response.json()
            print(f"✅ PR created successfully!")
            print(f"🔗 PR URL: {pr_data['html_url']}")
            print(f"📄 PR Number: {pr_data['number']}")
            print(f"🎯 State: {pr_data['state']}")
            
            # Close the test PR immediately
            print(f"\n4️⃣ Closing test PR #{pr_data['number']}...")
            close_response = requests.patch(
                f"https://api.github.com/repos/basilivanov/FF-TEST/pulls/{pr_data['number']}", 
                headers=headers, 
                json={"state": "closed"}
            )
            
            if close_response.status_code == 200:
                print(f"✅ Test PR closed successfully")
            else:
                print(f"⚠️ Could not close test PR: {close_response.status_code}")
                
        elif response.status_code == 422:
            error_data = response.json()
            if "pull request already exists" in error_data.get("message", "").lower():
                print(f"ℹ️ PR already exists between these branches")
                print(f"✅ This means GitHub App DOES have write access!")
            else:
                print(f"❌ PR creation failed (422): {error_data}")
        else:
            print(f"❌ PR creation failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()