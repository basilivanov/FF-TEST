from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Dict, Any

router = APIRouter(prefix="/api/v1")

@router.get("/hello")
async def hello() -> Dict[str, Any]:
    """
    Returns a Hello World message with current timestamp.
    
    Returns:
        JSON response with message and timestamp
    """
    return {
        "message": "Hello World",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }