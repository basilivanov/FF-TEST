
import asyncio
from app.api.orchestrator_v2 import create_feature, plan_feature, run_feature
from app.api.schemas.orchestrator_schemas import FeatureCreateRequest
from fastapi import Request
from urllib.parse import urlparse

class MockRequest:
    def __init__(self, method, url):
        self.headers = {}
        self.method = method
        self.url = urlparse(url)

async def main():
    # 1. Создаем фичу
    feature_request = FeatureCreateRequest(title="RPS-E2E-PROMPTS-COMPLIANCE", intent={"env": "TEST"})
    request = MockRequest("POST", "/api/v1/orchestrator/features")
    created_feature = await create_feature(request, feature_request)
    feature_id = created_feature.id
    print(f"Feature created with ID: {feature_id}")

    # 2. Планируем фичу
    request = MockRequest("POST", f"/api/v1/orchestrator/features/{feature_id}/plan")
    planned_feature = await plan_feature(request, feature_id)
    print(f"Feature planned: {planned_feature}")

    # 3. Запускаем фичу
    request = MockRequest("POST", f"/api/v1/orchestrator/features/{feature_id}/run")
    run_response = await run_feature(request, feature_id)
    print(f"Feature run started: {run_response}")

if __name__ == "__main__":
    asyncio.run(main())
