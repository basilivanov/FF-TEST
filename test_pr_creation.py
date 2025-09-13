
import sys, os
sys.path.insert(0, '.')

# Load all environment variables from .env and system
with open('.env', 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# Mock the token if not available for testing
if not os.environ.get('GITHUB_TOKEN'):
    print('No GITHUB_TOKEN found - this is expected in testing mode')

from app.services.git_integration import GitIntegrationService

# Create service and try to create PR
git_service = GitIntegrationService()
try:
    pr_info = git_service.create_pull_request(
        branch_name='feature/99_test-merge-functionality',
        feature_id=99,
        feature_title='Test Merge Functionality',
        correlation_id='TEST_MERGE_20250912'
    )
    print(f'PR created successfully: {pr_info}')
except Exception as e:
    print(f'PR creation failed: {e}')
    
    # If we are in non-push mode, show what would happen
    if not git_service.push_enabled:
        print('This is expected in test mode - mock PR would be created')

