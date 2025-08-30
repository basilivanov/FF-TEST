from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status

async def corr_id_from_request(request: Request) -> str:
    return request.scope.get("correlation_id") or request.headers.get("x-correlation-id") or "unknown"

async def unhandled_error_handler(request: Request, exc: Exception):
    cid = await corr_id_from_request(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "correlation_id": cid},
        headers={"x-correlation-id": cid},
    )