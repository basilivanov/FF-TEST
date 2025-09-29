"""Real PR test for feature #777."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/real-pr-test")
def real_pr_test_endpoint():
    return {"message": "Real PR test works!", "feature_id": 777}
