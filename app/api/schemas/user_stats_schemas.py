#!/usr/bin/env python3
"""
Pydantic schemas for user statistics API endpoints.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class UserStatsResponse(BaseModel):
    """Response schema for user statistics endpoint."""
    
    user_id: int = Field(..., description="User ID", gt=0)
    username: str = Field(..., description="Username")
    login_count: int = Field(..., description="Total number of user logins", ge=0)
    last_activity: Optional[datetime] = Field(None, description="Timestamp of last user activity (UTC)")
    last_login: Optional[datetime] = Field(None, description="Timestamp of last login (UTC)")
    total_session_duration_seconds: float = Field(..., description="Total session duration in seconds", ge=0)
    average_session_duration_seconds: float = Field(..., description="Average session duration in seconds", ge=0)
    active_sessions_count: int = Field(..., description="Number of currently active sessions", ge=0)
    total_activities_count: int = Field(..., description="Total number of user activities recorded", ge=0)
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="User account creation timestamp (UTC)")
    last_updated: datetime = Field(..., description="Timestamp when stats were last calculated (UTC)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "user_id": 123,
                "username": "john_doe",
                "login_count": 42,
                "last_activity": "2024-01-15T10:30:00+00:00",
                "last_login": "2024-01-15T09:00:00+00:00",
                "total_session_duration_seconds": 86400.0,
                "average_session_duration_seconds": 2057.14,
                "active_sessions_count": 2,
                "total_activities_count": 156,
                "is_active": True,
                "created_at": "2024-01-01T12:00:00+00:00",
                "last_updated": "2024-01-15T10:35:00+00:00"
            }
        }


class UserStatsError(BaseModel):
    """Error response schema for user statistics endpoint."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID for tracking")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Error timestamp (UTC)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "error": "USER_NOT_FOUND",
                "message": "User with ID 999 not found",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:35:00+00:00"
            }
        }


class ActivityType(str, Enum):
    """Enumeration of supported activity types."""
    
    API_CALL = "api_call"
    PAGE_VIEW = "page_view"
    FEATURE_USAGE = "feature_usage"
    LOGIN = "login"
    LOGOUT = "logout"
    SESSION_UPDATE = "session_update"


class UserActivityCreate(BaseModel):
    """Schema for creating new user activity records."""
    
    user_id: int = Field(..., description="User ID", gt=0)
    activity_type: ActivityType = Field(..., description="Type of activity")
    activity_data: Optional[Dict[str, Any]] = Field(None, description="Additional activity context data")
    ip_address: Optional[str] = Field(None, description="IP address where activity originated")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    @validator('activity_data')
    def validate_activity_data(cls, v):
        """Validate that activity_data is JSON serializable."""
        if v is not None:
            try:
                import json
                json.dumps(v)
            except (TypeError, ValueError) as e:
                raise ValueError(f"activity_data must be JSON serializable: {e}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "activity_type": "api_call",
                "activity_data": {
                    "endpoint": "/api/v1/users/123/stats",
                    "method": "GET",
                    "response_time_ms": 150
                },
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }


class UserSessionCreate(BaseModel):
    """Schema for creating new user session records."""
    
    user_id: int = Field(..., description="User ID", gt=0)
    session_token: str = Field(..., description="Unique session token", min_length=1)
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "session_token": "sess_abc123def456",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }