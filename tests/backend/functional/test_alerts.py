"""
Functional Tests for Backend API
Test ID Format: FT-XXX (Functional Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify core API endpoint functionality.
Tests the Backend Flask API (Backend/app.py)

Reference: IEEE 829 Test Case Specification
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Backend"))


class TestUserAuthentication:
    """
    Test Suite: User Authentication Endpoints
    Validates signup, login, and token management.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        self.bcrypt_patcher = patch('app.bcrypt')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        self.mock_bcrypt = self.bcrypt_patcher.start()
        
        # Setup geocoding mock
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        # Setup bcrypt mock
        self.mock_bcrypt.generate_password_hash.return_value = b'hashed_password'
        self.mock_bcrypt.check_password_hash.return_value = True
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app = app
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
        self.bcrypt_patcher.stop()
    
    # =========================================================================
    # FT-001: User Signup - Success
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft001_user_signup_success(self):
        """
        Test ID: FT-001
        Priority: P1 - Critical
        Pre-conditions: Valid user data, user doesn't exist
        Expected Result: User created, JWT token returned
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,  # Check if exists
            {      # Return after insert
                "_id": user_id,
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+919876543210",
                "location": {"city": "Mumbai", "state": "Maharashtra"},
                "isAuthorized": False,
                "notificationPreferences": {"email": True, "sms": True, "push": True}
            }
        ]
        self.mock_mongo.db.users.insert_one.return_value = MagicMock(inserted_id=user_id)
        
        response = self.client.post('/api/signup', json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "phone": "+919876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == "test@example.com"
    
    # =========================================================================
    # FT-002: User Signup - Duplicate Email
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft002_user_signup_duplicate_email(self):
        """
        Test ID: FT-002
        Priority: P1 - Critical
        Pre-conditions: User with email already exists
        Expected Result: 400 error - User already exists
        """
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": ObjectId(),
            "email": "test@example.com"
        }
        
        response = self.client.post('/api/signup', json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "phone": "+919876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['msg'].lower()
    
    # =========================================================================
    # FT-003: User Login - Success
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft003_user_login_success(self):
        """
        Test ID: FT-003
        Priority: P1 - Critical
        Pre-conditions: User exists with correct password
        Expected Result: JWT token returned
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "name": "Test User",
            "email": "test@example.com",
            "password": "hashed_password",
            "phone": "+919876543210",
            "location": {},
            "isAuthorized": False,
            "notificationPreferences": {}
        }
        
        response = self.client.post('/api/login', json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert 'user' in data
    
    # =========================================================================
    # FT-004: User Login - Invalid Password
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft004_user_login_invalid_password(self):
        """
        Test ID: FT-004
        Priority: P1 - Critical
        Pre-conditions: User exists but wrong password
        Expected Result: 401 Unauthorized
        """
        self.mock_bcrypt.check_password_hash.return_value = False
        
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "password": "hashed_password"
        }
        
        response = self.client.post('/api/login', json={
            "email": "test@example.com",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
    
    # =========================================================================
    # FT-005: User Login - Non-existent User
    # Priority: P2 (High)
    # =========================================================================
    def test_ft005_user_login_nonexistent(self):
        """
        Test ID: FT-005
        Priority: P2 - High
        Pre-conditions: User does not exist
        Expected Result: 401 Unauthorized
        """
        self.mock_mongo.db.users.find_one.return_value = None
        
        response = self.client.post('/api/login', json={
            "email": "nonexistent@example.com",
            "password": "somepassword"
        })
        
        assert response.status_code == 401
    
    # =========================================================================
    # FT-006: Admin Authorization Check
    # Priority: P2 (High)
    # =========================================================================
    def test_ft006_admin_authorization(self):
        """
        Test ID: FT-006
        Priority: P2 - High
        Pre-conditions: Email ends with .admin@gmail.com
        Expected Result: User created with isAuthorized=True
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,
            {
                "_id": user_id,
                "name": "Admin User",
                "email": "disaster.admin@gmail.com",
                "phone": "+919876543210",
                "location": {},
                "isAuthorized": True,
                "notificationPreferences": {}
            }
        ]
        self.mock_mongo.db.users.insert_one.return_value = MagicMock(inserted_id=user_id)
        
        response = self.client.post('/api/signup', json={
            "name": "Admin User",
            "email": "disaster.admin@gmail.com",
            "password": "AdminPass123!",
            "phone": "+919876543210",
            "city": "Delhi",
            "state": "Delhi"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['user']['isAuthorized'] == True


class TestAlertManagement:
    """
    Test Suite: Alert Creation and Retrieval
    Validates alert CRUD operations.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        self.bcrypt_patcher = patch('app.bcrypt')
        self.twilio_patcher = patch('app.Client')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        self.mock_bcrypt = self.bcrypt_patcher.start()
        self.mock_twilio = self.twilio_patcher.start()
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        self.mock_bcrypt.check_password_hash.return_value = True
        
        mock_twilio_instance = MagicMock()
        mock_twilio_instance.messages.create.return_value = MagicMock(sid='SM123')
        self.mock_twilio.return_value = mock_twilio_instance
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
        self.bcrypt_patcher.stop()
        self.twilio_patcher.stop()
    
    def _login(self):
        """Helper to login and get token."""
        user_id = ObjectId()
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "name": "Test User",
            "email": "test@test.com",
            "password": "hashed",
            "phone": "+919876543210",
            "location": {},
            "isAuthorized": True,
            "notificationPreferences": {}
        }
        
        response = self.client.post('/api/login', json={
            "email": "test@test.com",
            "password": "password"
        })
        return response.get_json()['token'], user_id
    
    # =========================================================================
    # FT-007: Create Alert - Success
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft007_create_alert_success(self):
        """
        Test ID: FT-007
        Priority: P1 - Critical
        Pre-conditions: Authenticated user, valid alert data
        Expected Result: Alert created and returned
        """
        token, user_id = self._login()
        alert_id = ObjectId()
        
        self.mock_mongo.db.alerts.find.return_value = []
        self.mock_mongo.db.alerts.insert_one.return_value = MagicMock(inserted_id=alert_id)
        self.mock_mongo.db.alerts.find_one.return_value = {
            "_id": alert_id,
            "user_id": user_id,
            "title": "Flood Warning",
            "message": "Heavy flooding expected",
            "type": "flood",
            "severity": "high",
            "location": "Mumbai, Maharashtra",
            "coordinates": {"lat": 19.0760, "lng": 72.8777},
            "status": "active",
            "timestamp": datetime.utcnow(),
            "sms_sent": True
        }
        self.mock_mongo.db.users.find.return_value = []
        
        response = self.client.post(
            '/api/alerts',
            json={
                "title": "Flood Warning",
                "message": "Heavy flooding expected",
                "type": "flood",
                "severity": "high",
                "location": "Mumbai, Maharashtra",
                "coordinates": {"lat": 19.0760, "lng": 72.8777}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == "Flood Warning"
    
    # =========================================================================
    # FT-008: Get Alerts - With Filters
    # Priority: P2 (High)
    # =========================================================================
    def test_ft008_get_alerts_with_filters(self):
        """
        Test ID: FT-008
        Priority: P2 - High
        Pre-conditions: Alerts exist in database
        Expected Result: Filtered alerts returned
        """
        token, user_id = self._login()
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = [
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Flood Alert",
                "message": "Test",
                "type": "flood",
                "severity": "high",
                "location": "Mumbai",
                "coordinates": {"lat": 19.0, "lng": 72.8},
                "status": "active",
                "timestamp": datetime.utcnow(),
                "sms_sent": True
            }
        ]
        self.mock_mongo.db.alerts.find.return_value = mock_cursor
        
        response = self.client.get(
            '/api/alerts?time=24h&type=flood',
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


class TestSMSNotification:
    """
    Test Suite: SMS Notification Logic
    Validates SMS triggering and suppression.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        yield
        
        self.mongo_patcher.stop()
    
    # =========================================================================
    # FT-009: SMS Triggered for New Alert
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft009_sms_triggered_new_alert(self):
        """
        Test ID: FT-009
        Priority: P1 - Critical
        Pre-conditions: No recent alerts in area
        Expected Result: SMS should be sent
        """
        self.mock_mongo.db.alerts.find.return_value = []
        
        from app import should_trigger_sms
        result = should_trigger_sms({"lat": 19.0760, "lng": 72.8777})
        
        assert result == True
    
    # =========================================================================
    # FT-010: SMS Suppressed for Duplicate Alert
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft010_sms_suppressed_duplicate(self):
        """
        Test ID: FT-010
        Priority: P1 - Critical
        Pre-conditions: Recent alert exists within radius
        Expected Result: SMS should be suppressed
        """
        self.mock_mongo.db.alerts.find.return_value = [
            {
                "_id": ObjectId(),
                "coordinates": {"lat": 19.0760, "lng": 72.8777},
                "timestamp": datetime.utcnow(),
                "sms_sent": True
            }
        ]
        
        from app import should_trigger_sms
        result = should_trigger_sms({"lat": 19.0760, "lng": 72.8777})
        
        assert result == False


class TestGeocoding:
    """
    Test Suite: Geocoding Functionality
    Validates coordinate lookup for locations.
    """
    
    # =========================================================================
    # FT-011: Geocoding Success
    # Priority: P2 (High)
    # =========================================================================
    def test_ft011_geocoding_success(self):
        """
        Test ID: FT-011
        Priority: P2 - High
        Pre-conditions: Valid city/state
        Expected Result: Coordinates returned
        """
        with patch('app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
            mock_get.return_value = mock_response
            
            from app import get_coordinates
            result = get_coordinates("Mumbai", "Maharashtra")
            
            assert 'lat' in result
            assert 'lng' in result
            assert result['lat'] == 19.0760
            assert result['lng'] == 72.8777
    
    # =========================================================================
    # FT-012: Geocoding Fallback
    # Priority: P2 (High)
    # =========================================================================
    def test_ft012_geocoding_fallback(self):
        """
        Test ID: FT-012
        Priority: P2 - High
        Pre-conditions: Geocoding API fails
        Expected Result: Default India coordinates returned
        """
        with patch('app.requests.get') as mock_get:
            mock_get.return_value.json.return_value = []
            
            from app import get_coordinates, CONSTANTS
            result = get_coordinates("InvalidCity", "InvalidState")
            
            assert result['lat'] == CONSTANTS['DEFAULT_LAT']
            assert result['lng'] == CONSTANTS['DEFAULT_LNG']
