#!/usr/bin/env python3
"""
Автоматическая настройка branch protection rules для блокировки merge при падении E2E
"""

import os
import json
import requests
import sys

def setup_branch_protection():
    """Настройка branch protection для main ветки"""
    
    # Получение параметров из окружения
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPOSITORY')  # format: owner/repo
    
    if not github_token:
        print("❌ GITHUB_TOKEN not set")
        return False
        
    if not github_repo:
        print("❌ GITHUB_REPOSITORY not set")
        return False
    
    # Конфигурация branch protection
    protection_config = {
        "required_status_checks": {
            "strict": True,
            "contexts": [
                "E2E Regression Tests / feature_e2e",
                "E2E Regression Tests / task_e2e"
            ]
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_linear_history": True
    }
    
    # API запрос к GitHub
    url = f"https://api.github.com/repos/{github_repo}/branches/main/protection"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.put(url, 
                              headers=headers, 
                              json=protection_config,
                              timeout=30)
        
        if response.status_code == 200:
            print("✅ Branch protection rules configured successfully")
            print("   - E2E tests are now required for merge to main")
            print("   - Pull request reviews required")
            print("   - Linear history enforced")
            return True
        else:
            print(f"❌ Failed to configure branch protection: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error configuring branch protection: {e}")
        return False

def check_existing_protection():
    """Проверка существующих branch protection rules"""
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPOSITORY')
    
    if not github_token or not github_repo:
        return None
        
    url = f"https://api.github.com/repos/{github_repo}/branches/main/protection"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            protection = response.json()
            print("📋 Current branch protection status:")
            
            # Проверка required status checks
            if 'required_status_checks' in protection:
                contexts = protection['required_status_checks'].get('contexts', [])
                print(f"   Required status checks: {len(contexts)}")
                for context in contexts:
                    print(f"     - {context}")
            else:
                print("   Required status checks: None")
                
            # Проверка PR reviews
            if 'required_pull_request_reviews' in protection:
                reviews = protection['required_pull_request_reviews']
                count = reviews.get('required_approving_review_count', 0)
                print(f"   Required PR reviews: {count}")
            else:
                print("   Required PR reviews: None")
                
            return protection
        elif response.status_code == 404:
            print("📋 No branch protection rules found")
            return None
        else:
            print(f"❌ Failed to check protection: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking protection: {e}")
        return None

def main():
    """Основная функция"""
    print("🔒 Setting up E2E Branch Protection for merge blocking...")
    
    # Проверка существующих правил
    existing = check_existing_protection()
    
    # Настройка новых правил
    if "--force" in sys.argv or not existing:
        success = setup_branch_protection()
        if success:
            print("\n✅ E2E blocking is now active:")
            print("   - Merge to main blocked if E2E tests fail")
            print("   - Both feature_e2e and task_e2e must pass")
            print("   - Pull requests require approval")
        else:
            print("\n❌ Failed to setup E2E blocking")
            sys.exit(1)
    else:
        print("\n📋 Branch protection already exists")
        print("   Use --force to overwrite existing rules")

if __name__ == '__main__':
    main()