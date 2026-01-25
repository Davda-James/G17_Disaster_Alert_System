"""
Integration Tests for Backend API
Test ID Format: IT-XXX (Integration Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify end-to-end flows across multiple components.
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


@pytest.mark.integration
class TestEndToEndUserFlow:
    """
    Test Suite: End-to-End User Registration to Alert Flow
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
        
        self.mock_bcrypt.generate_password_hash.return_value = b'hashed'
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
    
    # =========================================================================
    # IT-001: Complete User Registration Flow
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it001_complete_registration_flow(self):
        """
        Test ID: IT-001
        Priority: P1 - Critical
        Complete user registration with valid token.
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,  # Check existence
            {      # Return after insert
                "_id": user_id,
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+919876543210",
                "location": {"city": "Mumbai", "state": "Maharashtra"},
                "isAuthorized": False,
                "notificationPreferences": {}
            },
            {      # For /api/me call
                "_id": user_id,
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+919876543210",
                "location": {},
                "isAuthorized": False,
                "notificationPreferences": {}
            }
        ]
        self.mock_mongo.db.users.insert_one.return_value = MagicMock(inserted_id=user_id)
        
        # Step 1: Signup
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
        token = data['token']
        
        # Step 2: Access protected endpoint
        me_response = self.client.get(
            '/api/me',
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
    
    # =========================================================================
    # IT-002: Login and Create Alert Flow
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it002_login_create_alert_flow(self):
        """
        Test ID: IT-002
        Priority: P1 - Critical
        Login then create alert with SMS notification.
        """
        user_id = ObjectId()
        alert_id = ObjectId()
        
        # Login
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "name": "Test User",
            "email": "test@test.com",
            "password": "hashed",
            "phone": "+919876543210",
            "location": {"coordinates": {"lat": 19.0, "lng": 72.8}},
            "isAuthorized": True,
            "notificationPreferences": {}
        }
        
        login_response = self.client.post('/api/login', json={
            "email": "test@test.com",
            "password": "password"
        })
        
        assert login_response.status_code == 200
        token = login_response.get_json()['token']
        
        # Create alert
        self.mock_mongo.db.alerts.find.return_value = []
        self.mock_mongo.db.alerts.insert_one.return_value = MagicMock(inserted_id=alert_id)
        self.mock_mongo.db.alerts.find_one.return_value = {
            "_id": alert_id,
            "user_id": user_id,
            "title": "Flood Warning",
            "message": "Heavy flooding",
            "type": "flood",
            "severity": "high",
            "location": "Mumbai",
            "coordinates": {"lat": 19.0760, "lng": 72.8777},
            "status": "active",
            "timestamp": datetime.utcnow(),
            "sms_sent": True
        }
        self.mock_mongo.db.users.find.return_value = []
        
        alert_response = self.client.post(
            '/api/alerts',
            json={
                "title": "Flood Warning",
                "message": "Heavy flooding",
                "type": "flood",
                "severity": "high",
                "location": "Mumbai",
                "coordinates": {"lat": 19.0760, "lng": 72.8777}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert alert_response.status_code == 201


@pytest.mark.integration
class TestAlertNotificationFlow:
    """
    Test Suite: Alert to SMS Notification Flow
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mocks."""
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        yield
        
        self.mongo_patcher.stop()
    
    # =========================================================================
    # IT-003: Alert Triggers SMS to Nearby Users
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it003_alert_triggers_sms_nearby_users(self):
        """
        Test ID: IT-003
        Priority: P1 - Critical
        Alert should trigger SMS to users within radius.
        """
        with patch('app.send_twilio_sms') as mock_sms:
            mock_sms.return_value = {"status": "success", "sid": "SM123"}
            
            self.mock_mongo.db.users.find.return_value = [
                {"_id": ObjectId(), "phone": "+919876543210", "location": {"coordinates": {"lat": 19.0760, "lng": 72.8777}}},
                {"_id": ObjectId(), "phone": "+919876543211", "location": {"coordinates": {"lat": 19.1, "lng": 72.9}}},
            ]
            
            from app import broadcast_sms_to_users
            
            alert_data = {
                "title": "Test Alert",
                "message": "Test message",
                "coordinates": {"lat": 19.0760, "lng": 72.8777}
            }
            
            result = broadcast_sms_to_users(alert_data)
            
            assert result == True
            assert mock_sms.call_count == 2
    
    # =========================================================================
    # IT-004: Duplicate Alert Suppression Flow
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it004_duplicate_alert_suppression(self):
        """
        Test ID: IT-004
        Priority: P1 - Critical
        Second alert in same area should be suppressed.
        """
        from app import should_trigger_sms
        
        coords = {"lat": 19.0760, "lng": 72.8777}
        
        # First alert - no existing alerts
        self.mock_mongo.db.alerts.find.return_value = []
        first_result = should_trigger_sms(coords)
        assert first_result == True
        
        # Second alert - existing alert in same area
        self.mock_mongo.db.alerts.find.return_value = [
            {
                "_id": ObjectId(),
                "coordinates": {"lat": 19.0760, "lng": 72.8777},
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "sms_sent": True
            }
        ]
        second_result = should_trigger_sms(coords)
        assert second_result == False


@pytest.mark.integration
class TestUserProfileUpdateFlow:
    """
    Test Suite: User Profile Update Flow
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
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "28.6139", "lon": "77.2090"}]
        self.mock_geocoding.return_value = mock_response
        
        self.mock_bcrypt.check_password_hash.return_value = True
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
        self.bcrypt_patcher.stop()
    
    # =========================================================================
    # IT-005: Update User Location Flow
    # Priority: P2 (High)
    # =========================================================================
    def test_it005_update_user_location(self):
        """
        Test ID: IT-005
        Priority: P2 - High
        User updates their location with re-geocoding.
        """
        user_id = ObjectId()
        
        # Login
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "name": "Test User",
            "email": "test@test.com",
            "password": "hashed",
            "phone": "+919876543210",
            "location": {"city": "Mumbai", "state": "Maharashtra"},
            "isAuthorized": False,
            "notificationPreferences": {}
        }
        
        login_resp = self.client.post('/api/login', json={
            "email": "test@test.com",
            "password": "password"
        })
        
        token = login_resp.get_json()['token']
        
        # Update location
        self.mock_mongo.db.users.update_one.return_value = MagicMock()
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "name": "Test User",
            "email": "test@test.com",
            "phone": "+919876543210",
            "location": {
                "city": "Delhi",
                "state": "Delhi",
                "coordinates": {"lat": 28.6139, "lng": 77.2090}
            },
            "isAuthorized": False,
            "notificationPreferences": {}
        }
        
        update_resp = self.client.put(
            f'/api/user/{str(user_id)}',
            json={
                "location": {"city": "Delhi", "state": "Delhi"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert update_resp.status_code == 200
        data = update_resp.get_json()
        assert data['location']['city'] == 'Delhi'


@pytest.mark.integration
class TestMultiUserAlertScenario:
    """
    Test Suite: Multi-User Alert Distribution
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mocks."""
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        yield
        
        self.mongo_patcher.stop()
    
    # =========================================================================
    # IT-006: Regional Alert Distribution
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it006_regional_alert_distribution(self):
        """
        Test ID: IT-006
        Priority: P1 - Critical
        Alert should only notify users in affected region.
        """
        with patch('app.send_twilio_sms') as mock_sms:
            mock_sms.return_value = {"status": "success"}
            
            self.mock_mongo.db.users.find.return_value = [
                # Mumbai user - within radius
                {"_id": ObjectId(), "phone": "+919876543210", "location": {"coordinates": {"lat": 19.0760, "lng": 72.8777}}},
                # Pune user - within radius
                {"_id": ObjectId(), "phone": "+919876543211", "location": {"coordinates": {"lat": 18.5204, "lng": 73.8567}}},
                # Delhi user - outside radius
                {"_id": ObjectId(), "phone": "+919876543212", "location": {"coordinates": {"lat": 28.6139, "lng": 77.2090}}},
            ]
            
            from app import broadcast_sms_to_users
            
            alert_data = {
                "title": "Mumbai Flood Alert",
                "message": "Flooding in Mumbai",
                "coordinates": {"lat": 19.0760, "lng": 72.8777}
            }
            
            broadcast_sms_to_users(alert_data)
            
            # Only Mumbai and Pune within 200km should receive SMS
            assert mock_sms.call_count == 2
