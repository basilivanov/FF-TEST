
import sys, os
sys.path.insert(0, '.')

# Load environment variables
with open('.env', 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

from app.services.git_integration import GitIntegrationService

# Test merge on PR #2
git_service = GitIntegrationService()

try:
    merge_info = git_service.merge_pull_request(
        feature_id=30,  # Based on PR title 'Feature #30'
        pr_number=2,    # PR #2
        head_sha='6ab9034ab3796671e60a4b452efa1b4372a08089',  # From API response
        correlation_id='TEST_MERGE_PR2_20250912'
    )
    print(f'Merge successful: {merge_info}')
except Exception as e:
    print(f'Merge failed (expected without real token): {e}')
    
    # Check if this is just a token issue
    if 'Unauthorized' in str(e) or '401' in str(e):
        print('This is expected - no GitHub token available in test environment')
    else:
        print(f'Unexpected error: {e}')

