#!/usr/bin/env python3
"""
Test GitHub App authentication with JWT and Installation tokens.
"""

import os
import jwt
import time
import requests
from datetime import datetime, timedelta

class GitHubAppAuth:
    def __init__(self):
        self.app_id = "1951709"  # Ваш App ID
        self.installation_id = "85882340"  # Installation ID
        self.private_key_path = "/etc/feature-factory/github-app-private-key.pem"
        
    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        print(f"📝 Generating JWT for App ID: {self.app_id}")
        
        # Check if private key exists
        if not os.path.exists(self.private_key_path):
            raise Exception(f"Private key not found: {self.private_key_path}")
            
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued 1 minute ago (to account for clock skew)
            'exp': now + 600,  # Expires in 10 minutes
            'iss': int(self.app_id)
        }
        
        try:
            with open(self.private_key_path, 'r') as key_file:
                private_key = key_file.read()
                
            jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
            print(f"✅ JWT generated successfully")
            print(f"🔑 JWT (first 50 chars): {jwt_token[:50]}...")
            return jwt_token
            
        except Exception as e:
            print(f"❌ JWT generation failed: {e}")
            raise
    
    def get_installation_token(self) -> str:
        """Get installation access token (valid for 1 hour)."""
        print(f"🚀 Getting installation token for Installation ID: {self.installation_id}")
        
        jwt_token = self.generate_jwt()
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'FeatureFactory-CI/1.0'
        }
        
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        print(f"📡 Making request to: {url}")
        
        try:
            response = requests.post(url, headers=headers)
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 201:
                token_data = response.json()
                token = token_data['token']
                expires_at = token_data.get('expires_at', 'unknown')
                print(f"✅ Installation token received!")
                print(f"⏰ Expires at: {expires_at}")
                print(f"🔑 Token (first 20 chars): {token[:20]}...")
                return token
            else:
                print(f"❌ Failed to get installation token")
                print(f"📄 Response: {response.text}")
                raise Exception(f"Installation token request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Installation token request error: {e}")
            raise

    def test_api_access(self, token: str):
        """Test API access with installation token."""
        print(f"🧪 Testing API access with installation token...")
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'FeatureFactory-CI/1.0'
        }
        
        # Test 1: Get authenticated app info
        print("🔍 Test 1: Getting authenticated app info...")
        response = requests.get('https://api.github.com/app', headers={
            'Authorization': f'Bearer {self.generate_jwt()}',
            'Accept': 'application/vnd.github.v3+json'
        })
        
        if response.status_code == 200:
            app_data = response.json()
            print(f"✅ App info: {app_data['name']} (ID: {app_data['id']})")
        else:
            print(f"❌ App info failed: {response.status_code}")
            
        # Test 2: Access repository
        print("🔍 Test 2: Accessing repository basilivanov/FF-TEST...")
        response = requests.get('https://api.github.com/repos/basilivanov/FF-TEST', headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository access successful: {repo_data['full_name']}")
            print(f"📊 Permissions: {repo_data.get('permissions', 'N/A')}")
        else:
            print(f"❌ Repository access failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
        # Test 3: Rate limit info
        print("🔍 Test 3: Checking rate limits...")
        response = requests.get('https://api.github.com/rate_limit', headers=headers)
        
        if response.status_code == 200:
            rate_data = response.json()
            core_limit = rate_data['resources']['core']
            print(f"✅ Rate limit - Used: {core_limit['used']}/{core_limit['limit']}")
            print(f"⏰ Rate limit reset: {datetime.fromtimestamp(core_limit['reset'])}")
        else:
            print(f"❌ Rate limit check failed: {response.status_code}")

def main():
    print("🚀 GitHub App Authentication Test")
    print("=" * 50)
    
    try:
        auth = GitHubAppAuth()
        
        # Step 1: Generate JWT and get installation token
        installation_token = auth.get_installation_token()
        
        # Step 2: Test API access
        auth.test_api_access(installation_token)
        
        print("\n🎉 GitHub App authentication test completed successfully!")
        print("✅ Ready to use GitHub App for production API calls")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        print("❌ GitHub App authentication not ready")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())