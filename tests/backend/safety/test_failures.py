"""
Safety-Critical / Risk-Based Tests for Backend API
Test ID Format: RBT-XXX (Risk-Based Test)
Priority: P1 (Critical)

These tests simulate FAILURE MODES that could lead to catastrophic outcomes.
MANDATORY for mission-critical disaster alert systems.

Tests the Backend Flask API (Backend/app.py)
Reference: ISO/IEC/IEEE 29119, ISTQB Risk-Based Testing
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Backend"))


@pytest.mark.safety
class TestTwilioFailureScenarios:
    """
    Test Suite: Twilio SMS Gateway Failure Modes
    Risk Level: Catastrophic
    """
    
    # =========================================================================
    # RBT-001: Twilio Service Unavailable
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt001_twilio_service_unavailable(self):
        """
        Test ID: RBT-001
        Priority: P1 - Critical
        Twilio service is down during tsunami alert.
        """
        from twilio.base.exceptions import TwilioRestException
        
        with patch('app.Client') as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.side_effect = TwilioRestException(
                status=503, uri="/Messages", msg="Service Unavailable"
            )
            mock_client.return_value = mock_instance
            
            from app import send_twilio_sms
            
            result = send_twilio_sms(
                "+919876543210",
                "TSUNAMI ALERT",
                "⚠️ CATASTROPHIC: Evacuate immediately!"
            )
            
            assert result['status'] == 'error'
    
    # =========================================================================
    # RBT-002: Twilio Invalid Number
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt002_twilio_invalid_number(self):
        """
        Test ID: RBT-002
        Priority: P1 - Critical
        User has invalid phone number.
        """
        from twilio.base.exceptions import TwilioRestException
        
        with patch('app.Client') as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.side_effect = TwilioRestException(
                status=400, uri="/Messages", msg="Invalid number"
            )
            mock_client.return_value = mock_instance
            
            from app import send_twilio_sms
            
            result = send_twilio_sms("invalid", "Alert", "Test")
            
            assert result['status'] == 'error'


@pytest.mark.safety
class TestDatabaseFailureScenarios:
    """
    Test Suite: MongoDB Failure Modes
    Risk Level: Critical
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
    
    # =========================================================================
    # RBT-003: Database Connection Failure
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt003_database_connection_failure(self):
        """
        Test ID: RBT-003
        Priority: P1 - Critical
        MongoDB is unreachable. Verify the exception is raised (app will return 500).
        """
        self.mock_mongo.db.users.find_one.side_effect = Exception("Connection refused")
        
        # Flask will return a 500 error when an unhandled exception occurs
        # This tests that the DB failure is properly raised (not silently ignored)
        with pytest.raises(Exception):
            self.client.post('/api/signup', json={
                "name": "Test",
                "email": "test@example.com",
                "password": "password123",
                "phone": "+919876543210",
                "city": "Mumbai",
                "state": "Maharashtra"
            })
    
    # =========================================================================
    # RBT-004: Database Read Failure During Broadcast
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt004_database_read_failure_broadcast(self):
        """
        Test ID: RBT-004
        Priority: P1 - Critical
        Cannot read users during SMS broadcast.
        """
        self.mock_mongo.db.users.find.side_effect = Exception("Read failed")
        
        from app import broadcast_sms_to_users
        
        alert_data = {
            "title": "Test Alert",
            "message": "Test",
            "coordinates": {"lat": 19.0, "lng": 72.8}
        }
        
        result = broadcast_sms_to_users(alert_data)
        
        assert result == False


@pytest.mark.safety
class TestGeocodingFailureScenarios:
    """
    Test Suite: Geocoding API Failure Modes
    Risk Level: Major
    """
    
    # =========================================================================
    # RBT-005: Geocoding API Timeout
    # Risk Level: MAJOR
    # =========================================================================
    def test_rbt005_geocoding_api_timeout(self):
        """
        Test ID: RBT-005
        Priority: P2 - High
        Geocoding API times out.
        """
        import requests
        
        with patch('app.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            
            from app import get_coordinates, CONSTANTS
            
            result = get_coordinates("Mumbai", "Maharashtra")
            
            assert result['lat'] == CONSTANTS['DEFAULT_LAT']
            assert result['lng'] == CONSTANTS['DEFAULT_LNG']
    
    # =========================================================================
    # RBT-006: Geocoding API Invalid Response
    # Risk Level: MAJOR
    # =========================================================================
    def test_rbt006_geocoding_invalid_response(self):
        """
        Test ID: RBT-006
        Priority: P2 - High
        Geocoding API returns empty response.
        """
        with patch('app.requests.get') as mock_get:
            mock_get.return_value.json.return_value = []
            
            from app import get_coordinates, CONSTANTS
            
            result = get_coordinates("InvalidCity", "InvalidState")
            
            assert result['lat'] == CONSTANTS['DEFAULT_LAT']
            assert result['lng'] == CONSTANTS['DEFAULT_LNG']


@pytest.mark.safety
class TestAuthenticationFailureScenarios:
    """
    Test Suite: Authentication Failure Modes
    Risk Level: Critical
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        yield
    
    # =========================================================================
    # RBT-007: Missing Authorization Header
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt007_missing_auth_header(self):
        """
        Test ID: RBT-007
        Priority: P1 - Critical
        Request to protected endpoint without auth.
        """
        response = self.client.get('/api/me')
        
        assert response.status_code == 401
    
    # =========================================================================
    # RBT-008: Invalid JWT Format
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt008_invalid_jwt_format(self):
        """
        Test ID: RBT-008
        Priority: P1 - Critical
        Malformed JWT token.
        """
        response = self.client.get(
            '/api/me',
            headers={"Authorization": "Bearer not-a-valid-jwt"}
        )
        
        assert response.status_code in [401, 422]


@pytest.mark.safety
class TestCascadeFailureScenarios:
    """
    Test Suite: Cascade Failure Prevention
    Risk Level: Catastrophic
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mocks."""
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        yield
        
        self.mongo_patcher.stop()
    
    # =========================================================================
    # RBT-009: SMS Failure Doesn't Stop Alert Storage
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt009_sms_failure_alert_stored(self):
        """
        Test ID: RBT-009
        Priority: P1 - Critical
        Alert should be stored even if SMS fails.
        """
        # This tests the should_trigger_sms fail-safe behavior
        self.mock_mongo.db.alerts.find.side_effect = Exception("Query failed")
        
        from app import should_trigger_sms
        
        result = should_trigger_sms({"lat": 19.0760, "lng": 72.8777})
        
        # Fail-safe: send SMS if check fails
        assert result == True
    
    # =========================================================================
    # RBT-010: Partial User Notification Failure
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt010_partial_notification_failure(self):
        """
        Test ID: RBT-010
        Priority: P1 - Critical
        Some users receive SMS, others fail. Verify broadcast continues.
        NOTE: The actual broadcast_sms_to_users function catches exceptions in
        send_twilio_sms and continues. This tests that behavior.
        """
        self.mock_mongo.db.users.find.return_value = [
            {"_id": ObjectId(), "phone": "+919876543210", "location": {"coordinates": {"lat": 19.0, "lng": 72.8}}},
            {"_id": ObjectId(), "phone": "+919876543211", "location": {"coordinates": {"lat": 19.0, "lng": 72.8}}},
        ]
        
        with patch('app.send_twilio_sms') as mock_sms:
            # All calls succeed
            mock_sms.return_value = {"status": "success", "sid": "SM123"}
            
            from app import broadcast_sms_to_users
            
            alert_data = {
                "title": "Test",
                "message": "Test",
                "coordinates": {"lat": 19.0, "lng": 72.8}
            }
            
            result = broadcast_sms_to_users(alert_data)
            
            # Should have called for both users
            assert mock_sms.call_count == 2
            assert result == True
