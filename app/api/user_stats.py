#!/usr/bin/env python3
"""
User statistics API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from typing import Optional
import structlog
import json

from app.db.session import get_db
from app.db.models import User, UserSession, UserActivity
from app.api.schemas.user_stats_schemas import UserStatsResponse, UserStatsError
from app.api.middleware import get_correlation_id
from app.api.rate_limiter import rate_limit

# Setup structured logging
log = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["User Statistics"])


class UserStatsService:
    """Service class for user statistics operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_statistics(self, user_id: int) -> Optional[UserStatsResponse]:
        """
        Retrieve comprehensive user statistics.
        
        Args:
            user_id: The ID of the user to get statistics for
            
        Returns:
            UserStatsResponse object with all user statistics, or None if user not found
        """
        # Get user basic info
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Calculate login count (total sessions)
        login_count = self.db.query(UserSession).filter(UserSession.user_id == user_id).count()
        
        # Get last activity time
        last_activity = self.db.query(func.max(UserSession.last_activity)).filter(
            UserSession.user_id == user_id
        ).scalar()
        
        # Get last login time
        last_login = self.db.query(func.max(UserSession.login_time)).filter(
            UserSession.user_id == user_id
        ).scalar()
        
        # Calculate total session duration
        sessions = self.db.query(UserSession).filter(UserSession.user_id == user_id).all()
        total_duration = sum(session.duration_seconds for session in sessions)
        
        # Calculate average session duration
        average_duration = total_duration / login_count if login_count > 0 else 0.0
        
        # Count active sessions
        active_sessions_count = self.db.query(UserSession).filter(
            and_(UserSession.user_id == user_id, UserSession.is_active == True)
        ).count()
        
        # Count total activities
        total_activities_count = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).count()
        
        return UserStatsResponse(
            user_id=user.id,
            username=user.username,
            login_count=login_count,
            last_activity=last_activity,
            last_login=last_login,
            total_session_duration_seconds=total_duration,
            average_session_duration_seconds=average_duration,
            active_sessions_count=active_sessions_count,
            total_activities_count=total_activities_count,
            is_active=user.is_active,
            created_at=user.created_at,
            last_updated=datetime.now(timezone.utc)
        )
    
    def log_api_access(self, user_id: int, request: Request, correlation_id: str) -> None:
        """
        Log API access for monitoring and analytics.
        
        Args:
            user_id: The user ID being queried
            request: FastAPI request object
            correlation_id: Request correlation ID
        """
        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log structured data
        log.info(
            "user_stats_api_access",
            user_id=user_id,
            correlation_id=correlation_id,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint="/api/v1/users/{user_id}/stats",
            method="GET"
        )
        
        # Record activity in database if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            activity = UserActivity(
                user_id=user_id,
                activity_type="api_call",
                activity_data=json.dumps({
                    "endpoint": f"/api/v1/users/{user_id}/stats",
                    "method": "GET",
                    "correlation_id": correlation_id
                }),
                ip_address=client_ip,
                user_agent=user_agent
            )
            self.db.add(activity)
            self.db.commit()


@router.get(
    "/users/{user_id}/stats",
    response_model=UserStatsResponse,
    responses={
        200: {"description": "User statistics retrieved successfully"},
        400: {"model": UserStatsError, "description": "Invalid user ID"},
        404: {"model": UserStatsError, "description": "User not found"},
        429: {"model": UserStatsError, "description": "Rate limit exceeded"},
        500: {"model": UserStatsError, "description": "Internal server error"}
    },
    summary="Get User Statistics",
    description="""
    Retrieve comprehensive user activity statistics including:
    - Login count and session information
    - Last activity and login timestamps
    - Session duration metrics (total and average)
    - Activity counts and user status
    
    **Rate Limiting**: This endpoint is rate-limited to prevent abuse.
    - 60 requests per minute per client
    - 1000 requests per hour per client
    
    **Monitoring**: All requests are logged for security and analytics purposes.
    """
)
@rate_limit(requests_per_minute=60, requests_per_hour=1000)
async def get_user_stats(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> UserStatsResponse:
    """
    Get comprehensive user activity statistics and metrics.
    
    Args:
        user_id: The ID of the user to retrieve statistics for (must be positive integer)
        request: FastAPI request object (injected)
        db: Database session (injected)
    
    Returns:
        UserStatsResponse: Comprehensive user statistics
        
    Raises:
        HTTPException: 
            - 400 if user_id is invalid
            - 404 if user not found
            - 500 for internal server errors
    """
    correlation_id = get_correlation_id(request)
    
    # Input validation
    if user_id <= 0:
        log.warning(
            "invalid_user_id",
            user_id=user_id,
            correlation_id=correlation_id,
            error="User ID must be a positive integer"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UserStatsError(
                error="INVALID_USER_ID",
                message=f"User ID must be a positive integer, got: {user_id}",
                correlation_id=correlation_id
            ).dict()
        )
    
    try:
        # Initialize service
        stats_service = UserStatsService(db)
        
        # Log API access
        stats_service.log_api_access(user_id, request, correlation_id)
        
        # Get user statistics
        user_stats = stats_service.get_user_statistics(user_id)
        
        if user_stats is None:
            log.warning(
                "user_not_found",
                user_id=user_id,
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=UserStatsError(
                    error="USER_NOT_FOUND",
                    message=f"User with ID {user_id} not found",
                    correlation_id=correlation_id
                ).dict()
            )
        
        log.info(
            "user_stats_retrieved",
            user_id=user_id,
            username=user_stats.username,
            correlation_id=correlation_id,
            login_count=user_stats.login_count,
            active_sessions=user_stats.active_sessions_count
        )
        
        return user_stats
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(
            "user_stats_error",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=UserStatsError(
                error="INTERNAL_SERVER_ERROR",
                message="An internal error occurred while retrieving user statistics",
                correlation_id=correlation_id
            ).dict()
        )