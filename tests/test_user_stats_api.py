#!/usr/bin/env python3
"""
Comprehensive unit tests for user statistics API endpoint.
"""

import unittest
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.models import Base, User, UserSession, UserActivity
from app.db.session import get_db


class TestUserStatsAPI(unittest.TestCase):
    """Test suite for user statistics API endpoint."""
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        # Create in-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Override dependency
        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        app.dependency_overrides.clear()
    
    def setUp(self):
        """Setup before each test."""
        self.db = self.TestingSessionLocal()
        # Clear database before each test
        self.db.query(UserActivity).delete()
        self.db.query(UserSession).delete()
        self.db.query(User).delete()
        self.db.commit()
        
        # Create test users
        self.test_user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
        self.db.add(self.test_user)
        
        self.inactive_user = User(
            id=2,
            username="inactive_user",
            email="inactive@example.com",
            is_active=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=15)
        )
        self.db.add(self.inactive_user)
        self.db.commit()
        
    def tearDown(self):
        """Cleanup after each test."""
        self.db.close()
    
    def _create_test_sessions(self, user_id: int, count: int = 3) -> list:
        """Helper method to create test sessions."""
        sessions = []
        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        
        for i in range(count):
            login_time = base_time + timedelta(hours=i * 2)
            logout_time = login_time + timedelta(minutes=30 + i * 10) if i < count - 1 else None
            
            session = UserSession(
                user_id=user_id,
                session_token=f"session_token_{user_id}_{i}",
                login_time=login_time,
                logout_time=logout_time,
                last_activity=logout_time or (login_time + timedelta(minutes=45)),
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"TestAgent/{i + 1}.0",
                is_active=(i == count - 1)  # Last session is active
            )
            sessions.append(session)
            self.db.add(session)
        
        self.db.commit()
        return sessions
    
    def _create_test_activities(self, user_id: int, count: int = 5):
        """Helper method to create test activities."""
        activities = []
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        activity_types = ["api_call", "page_view", "feature_usage", "login", "logout"]
        
        for i in range(count):
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_types[i % len(activity_types)],
                activity_data=json.dumps({"test_data": f"activity_{i}"}),
                timestamp=base_time + timedelta(minutes=i * 10),
                ip_address=f"192.168.1.{200 + i}",
                user_agent=f"TestAgent/{i + 1}.0"
            )
            activities.append(activity)
            self.db.add(activity)
        
        self.db.commit()
        return activities
    
    def test_get_user_stats_success(self):
        """Test successful retrieval of user statistics."""
        # Create test data
        self._create_test_sessions(1, 3)
        self._create_test_activities(1, 5)
        
        # Make request
        response = self.client.get("/api/v1/users/1/stats")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        
        data = response.json()
        
        # Verify structure
        required_fields = [
            "user_id", "username", "login_count", "last_activity", "last_login",
            "total_session_duration_seconds", "average_session_duration_seconds",
            "active_sessions_count", "total_activities_count", "is_active",
            "created_at", "last_updated"
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Verify values
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(data["username"], "test_user")
        self.assertEqual(data["login_count"], 3)
        self.assertEqual(data["active_sessions_count"], 1)
        self.assertEqual(data["total_activities_count"], 5)
        self.assertTrue(data["is_active"])
        self.assertGreater(data["total_session_duration_seconds"], 0)
        self.assertGreater(data["average_session_duration_seconds"], 0)
    
    def test_get_user_stats_user_not_found(self):
        """Test error response when user does not exist."""
        response = self.client.get("/api/v1/users/999/stats")
        
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn("detail", data)
        
        error_detail = data["detail"]
        self.assertEqual(error_detail["error"], "USER_NOT_FOUND")
        self.assertIn("User with ID 999 not found", error_detail["message"])
        self.assertIn("correlation_id", error_detail)
    
    def test_get_user_stats_invalid_user_id(self):
        """Test error response for invalid user ID."""
        test_cases = [-1, 0]
        
        for invalid_id in test_cases:
            with self.subTest(user_id=invalid_id):
                response = self.client.get(f"/api/v1/users/{invalid_id}/stats")
                
                self.assertEqual(response.status_code, 400)
                
                data = response.json()
                self.assertIn("detail", data)
                
                error_detail = data["detail"]
                self.assertEqual(error_detail["error"], "INVALID_USER_ID")
                self.assertIn("positive integer", error_detail["message"])
    
    def test_get_user_stats_inactive_user(self):
        """Test statistics for inactive user."""
        self._create_test_sessions(2, 2)
        self._create_test_activities(2, 3)
        
        response = self.client.get("/api/v1/users/2/stats")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["user_id"], 2)
        self.assertEqual(data["username"], "inactive_user")
        self.assertFalse(data["is_active"])
        self.assertEqual(data["login_count"], 2)
        self.assertEqual(data["total_activities_count"], 3)
    
    def test_get_user_stats_no_sessions_or_activities(self):
        """Test statistics for user with no sessions or activities."""
        response = self.client.get("/api/v1/users/1/stats")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(data["login_count"], 0)
        self.assertEqual(data["active_sessions_count"], 0)
        self.assertEqual(data["total_activities_count"], 0)
        self.assertEqual(data["total_session_duration_seconds"], 0.0)
        self.assertEqual(data["average_session_duration_seconds"], 0.0)
        self.assertIsNone(data["last_activity"])
        self.assertIsNone(data["last_login"])
    
    def test_get_user_stats_correlation_id_header(self):
        """Test that correlation ID is included in response headers."""
        response = self.client.get(
            "/api/v1/users/1/stats",
            headers={"x-correlation-id": "test-correlation-123"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("x-correlation-id", response.headers)
    
    def test_get_user_stats_method_not_allowed(self):
        """Test that POST method is not allowed."""
        response = self.client.post("/api/v1/users/1/stats")
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_get_user_stats_activity_logging(self):
        """Test that API access is logged as user activity."""
        initial_activities_count = self.db.query(UserActivity).filter(
            UserActivity.user_id == 1
        ).count()
        
        response = self.client.get("/api/v1/users/1/stats")
        
        self.assertEqual(response.status_code, 200)
        
        # Check that activity was logged
        final_activities_count = self.db.query(UserActivity).filter(
            UserActivity.user_id == 1
        ).count()
        
        self.assertEqual(final_activities_count, initial_activities_count + 1)
        
        # Verify the logged activity
        logged_activity = self.db.query(UserActivity).filter(
            UserActivity.user_id == 1,
            UserActivity.activity_type == "api_call"
        ).order_by(UserActivity.timestamp.desc()).first()
        
        self.assertIsNotNone(logged_activity)
        
        activity_data = json.loads(logged_activity.activity_data)
        self.assertIn("endpoint", activity_data)
        self.assertIn("/api/v1/users/1/stats", activity_data["endpoint"])
        self.assertEqual(activity_data["method"], "GET")
    
    def test_session_duration_calculation(self):
        """Test session duration calculations are correct."""
        # Create sessions with known durations
        now = datetime.now(timezone.utc)
        
        # Session 1: 1 hour duration (logged out)
        session1 = UserSession(
            user_id=1,
            session_token="session_1",
            login_time=now - timedelta(hours=2),
            logout_time=now - timedelta(hours=1),
            last_activity=now - timedelta(hours=1),
            is_active=False
        )
        
        # Session 2: 30 minutes duration (logged out)
        session2 = UserSession(
            user_id=1,
            session_token="session_2",
            login_time=now - timedelta(minutes=45),
            logout_time=now - timedelta(minutes=15),
            last_activity=now - timedelta(minutes=15),
            is_active=False
        )
        
        self.db.add_all([session1, session2])
        self.db.commit()
        
        response = self.client.get("/api/v1/users/1/stats")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        expected_total_duration = 3600 + 1800  # 1 hour + 30 minutes = 5400 seconds
        expected_average_duration = expected_total_duration / 2  # 2700 seconds
        
        self.assertAlmostEqual(data["total_session_duration_seconds"], expected_total_duration, delta=1)
        self.assertAlmostEqual(data["average_session_duration_seconds"], expected_average_duration, delta=1)
    
    def test_timestamp_formats(self):
        """Test that all timestamps are properly formatted as ISO 8601 UTC."""
        self._create_test_sessions(1, 1)
        
        response = self.client.get("/api/v1/users/1/stats")
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Test timestamp fields that should be present
        timestamp_fields = ["created_at", "last_updated"]
        for field in timestamp_fields:
            if data[field]:
                # Should be ISO 8601 format with timezone
                self.assertTrue(data[field].endswith("+00:00"), f"{field} should be UTC timezone")
                # Should be parseable as datetime
                try:
                    parsed = datetime.fromisoformat(data[field])
                    self.assertIsInstance(parsed, datetime)
                except ValueError:
                    self.fail(f"{field} is not in valid ISO format: {data[field]}")
        
        # Test optional timestamp fields
        optional_timestamp_fields = ["last_activity", "last_login"]
        for field in optional_timestamp_fields:
            if data[field]:
                self.assertTrue(data[field].endswith("+00:00"), f"{field} should be UTC timezone")


class TestRateLimiting(unittest.TestCase):
    """Test suite for rate limiting functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        # Create in-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Override dependency
        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        app.dependency_overrides.clear()
    
    def setUp(self):
        """Setup before each test."""
        self.db = self.TestingSessionLocal()
        # Clear database before each test
        self.db.query(UserActivity).delete()
        self.db.query(UserSession).delete()
        self.db.query(User).delete()
        
        # Create test user
        self.test_user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            is_active=True
        )
        self.db.add(self.test_user)
        self.db.commit()
        
        # Reset rate limiter state
        from app.api.rate_limiter import _rate_limiter
        _rate_limiter._clients.clear()
    
    def tearDown(self):
        """Cleanup after each test."""
        self.db.close()
    
    @patch('app.api.rate_limiter.time.time')
    def test_rate_limiting_within_limits(self, mock_time):
        """Test that requests within limits are allowed."""
        # Mock time to be consistent
        mock_time.return_value = 1000.0
        
        # Make multiple requests within limit
        for i in range(10):
            response = self.client.get("/api/v1/users/1/stats")
            self.assertEqual(response.status_code, 200, f"Request {i + 1} should succeed")
    
    @patch('app.api.rate_limiter.time.time')
    def test_rate_limiting_minute_exceeded(self, mock_time):
        """Test rate limiting when minute limit is exceeded."""
        # Mock time to be consistent
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Make requests up to the minute limit (60)
        for i in range(60):
            response = self.client.get("/api/v1/users/1/stats")
            self.assertEqual(response.status_code, 200, f"Request {i + 1} should succeed")
        
        # The 61st request should be rate limited
        response = self.client.get("/api/v1/users/1/stats")
        self.assertEqual(response.status_code, 429)
        
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"]["error"], "RATE_LIMIT_EXCEEDED")
        self.assertIn("60 requests per minute", data["detail"]["message"])
        
        # Check rate limit headers
        self.assertIn("X-RateLimit-Limit", response.headers)
        self.assertIn("X-RateLimit-Remaining", response.headers)
        self.assertIn("Retry-After", response.headers)
    
    def test_rate_limiting_different_clients(self):
        """Test that rate limiting is per-client."""
        # Requests from different IP addresses should have separate limits
        headers1 = {"x-real-ip": "192.168.1.1"}
        headers2 = {"x-real-ip": "192.168.1.2"}
        
        # Each client should be able to make requests independently
        response1 = self.client.get("/api/v1/users/1/stats", headers=headers1)
        response2 = self.client.get("/api/v1/users/1/stats", headers=headers2)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)


if __name__ == "__main__":
    unittest.main()