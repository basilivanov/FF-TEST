#!/usr/bin/env python3
"""
Database models for the Feature Factory application.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    """User model for tracking user information and activity."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to user sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserSession(Base):
    """User session model for tracking login activity and session duration."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    login_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    logout_time = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship back to user
    user = relationship("User", back_populates="sessions")
    
    @property
    def duration_seconds(self) -> float:
        """Calculate session duration in seconds."""
        end_time = self.logout_time or self.last_activity
        if end_time and self.login_time:
            return (end_time - self.login_time).total_seconds()
        return 0.0
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, login_time='{self.login_time}')>"


class UserActivity(Base):
    """User activity model for tracking various user actions and metrics."""
    
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)  # e.g., 'api_call', 'page_view', 'feature_usage'
    activity_data = Column(Text, nullable=True)  # JSON data for additional activity context
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationship back to user
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, activity_type='{self.activity_type}', timestamp='{self.timestamp}')>"