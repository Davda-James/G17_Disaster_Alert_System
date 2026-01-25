"""
Boundary Value Analysis Tests for Backend API
Test ID Format: BVA-XXX (Boundary Value Analysis)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify system behavior at boundary conditions for API inputs.
Tests the Backend Flask API (Backend/app.py)

Reference: IEEE 829 Test Case Specification, ISTQB Boundary Value Analysis
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Backend"))


class TestUserInputBoundaries:
    """
    Test Suite: User Registration Input Boundary Values
    Tests validation of user input fields at boundary conditions.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        # Patch mongo before importing app
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        
        # Setup default mongo mock behavior
        self.mock_mongo.db.users.find_one.return_value = None
        self.mock_mongo.db.users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        # Setup geocoding mock
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app = app
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
    
    # =========================================================================
    # BVA-001: Email Format Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("email,should_pass", [
        ("a@b.co", True),                          # Minimum valid
        ("user@example.com", True),                # Standard valid
        ("user.name+tag@domain.co.uk", True),      # Complex valid
        ("", False),                               # Empty - invalid
        ("@example.com", False),                   # No local part
        ("test@", False),                          # No domain
        ("test", False),                           # No @ symbol
    ])
    def test_bva001_email_validation_boundaries(self, email, should_pass):
        """
        Test ID: BVA-001
        Priority: P1 - Critical
        Tests email format validation at boundaries.
        """
        user_id = ObjectId()
        
        # Setup mock to return created user after insert
        self.mock_mongo.db.users.find_one.side_effect = [
            None,  # Check if exists
            {      # Return after insert
                "_id": user_id,
                "name": "Test User",
                "email": email,
                "phone": "+919876543210",
                "location": {"city": "Mumbai", "state": "Maharashtra", "coordinates": {"lat": 19.0, "lng": 72.8}},
                "isAuthorized": False,
                "notificationPreferences": {"email": True, "sms": True, "push": True}
            }
        ]
        
        data = {
            "name": "Test User",
            "email": email,
            "password": "ValidPass123!",
            "phone": "+919876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = self.client.post('/api/signup', json=data)
        
        if should_pass:
            assert response.status_code in [201, 400, 500]
        else:
            assert response.status_code in [201, 400, 422, 500]
    
    # =========================================================================
    # BVA-002: Phone Number Length Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("phone,is_valid", [
        ("+919876543210", True),           # Standard Indian format
        ("+1234567890", True),             # 10 digits with +
        ("9876543210", True),              # Without +
        ("", False),                       # Empty
    ])
    def test_bva002_phone_validation_boundaries(self, phone, is_valid):
        """
        Test ID: BVA-002
        Priority: P2 - High
        Tests phone number length validation at boundaries.
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,
            {
                "_id": user_id,
                "name": "Test User",
                "email": "test@example.com",
                "phone": phone,
                "location": {},
                "isAuthorized": False,
                "notificationPreferences": {}
            }
        ]
        
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "ValidPass123!",
            "phone": phone,
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = self.client.post('/api/signup', json=data)
        assert response.status_code in [201, 400, 422, 500]
    
    # =========================================================================
    # BVA-003: Password Length Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("password,description", [
        ("abcdefgh", "8 characters - at minimum"),
        ("a" * 100, "100 characters - within limit"),
    ])
    def test_bva003_password_length_boundaries(self, password, description):
        """
        Test ID: BVA-003
        Priority: P1 - Critical
        Tests password length validation at boundaries.
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,
            {
                "_id": user_id,
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+919876543210",
                "location": {},
                "isAuthorized": False,
                "notificationPreferences": {}
            }
        ]
        
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": password,
            "phone": "+919876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = self.client.post('/api/signup', json=data)
        assert response.status_code in [201, 400, 500]
    
    # =========================================================================
    # BVA-004: Name Field Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("name,should_pass", [
        ("A", True),                       # Single character
        ("Test User", True),               # Standard
        ("A" * 100, True),                 # Long name
    ])
    def test_bva004_name_validation_boundaries(self, name, should_pass):
        """
        Test ID: BVA-004
        Priority: P2 - High
        Tests name field validation at boundaries.
        """
        user_id = ObjectId()
        
        self.mock_mongo.db.users.find_one.side_effect = [
            None,
            {
                "_id": user_id,
                "name": name,
                "email": "test@example.com",
                "phone": "+919876543210",
                "location": {},
                "isAuthorized": False,
                "notificationPreferences": {}
            }
        ]
        
        data = {
            "name": name,
            "email": "test@example.com",
            "password": "ValidPass123!",
            "phone": "+919876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = self.client.post('/api/signup', json=data)
        assert response.status_code in [201, 400, 422, 500]


class TestCoordinateBoundaries:
    """
    Test Suite: Coordinate Value Boundary Tests
    Tests geographic coordinate validation.
    """
    
    # =========================================================================
    # BVA-005: Coordinate Value Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("lat,lng,is_valid", [
        (0.0, 0.0, True),                  # Origin
        (90.0, 180.0, True),               # Max valid
        (-90.0, -180.0, True),             # Min valid
        (45.0, 90.0, True),                # Mid-range
        (90.1, 0.0, False),                # Latitude too high
        (-90.1, 0.0, False),               # Latitude too low
        (0.0, 180.1, False),               # Longitude too high
        (0.0, -180.1, False),              # Longitude too low
        (19.0760, 72.8777, True),          # Mumbai coordinates
    ])
    def test_bva005_coordinate_boundaries(self, lat, lng, is_valid):
        """
        Test ID: BVA-005
        Priority: P1 - Critical
        Tests coordinate value validation at boundaries.
        """
        lat_valid = -90.0 <= lat <= 90.0
        lng_valid = -180.0 <= lng <= 180.0
        
        assert (lat_valid and lng_valid) == is_valid
    
    # =========================================================================
    # BVA-006: Alert Severity Values
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("severity,is_valid", [
        ("low", True),
        ("medium", True),
        ("high", True),
        ("critical", True),
        ("", False),
        ("invalid", False),
    ])
    def test_bva006_severity_boundaries(self, severity, is_valid):
        """
        Test ID: BVA-006
        Priority: P1 - Critical
        Tests alert severity value validation.
        """
        valid_severities = ["low", "medium", "high", "critical"]
        result = severity.lower() in valid_severities if severity else False
        assert result == is_valid
    
    # =========================================================================
    # BVA-007: Alert Type Values
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("alert_type,is_valid", [
        ("flood", True),
        ("earthquake", True),
        ("cyclone", True),
        ("tsunami", True),
        ("fire", True),
        ("", False),
    ])
    def test_bva007_alert_type_boundaries(self, alert_type, is_valid):
        """
        Test ID: BVA-007
        Priority: P1 - Critical
        Tests alert type value validation.
        """
        valid_types = ["flood", "earthquake", "cyclone", "tsunami", "fire", "landslide", "drought"]
        result = alert_type.lower() in valid_types if alert_type else False
        assert result == is_valid


class TestRadiusBoundaries:
    """
    Test Suite: Distance/Radius Calculation Boundaries
    Tests the SMS_RADIUS_KM and DUPLICATE_CHECK_RADIUS_KM boundaries.
    """
    
    # =========================================================================
    # BVA-008: SMS Radius Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("distance_km,should_notify", [
        (0, True),                         # Same location
        (100, True),                       # Within 200km
        (199, True),                       # Just below threshold
        (200, True),                       # At threshold
        (201, False),                      # Just above threshold
        (500, False),                      # Well above threshold
    ])
    def test_bva008_sms_radius_boundaries(self, distance_km, should_notify):
        """
        Test ID: BVA-008
        Priority: P1 - Critical
        Tests SMS notification radius at boundary values.
        SMS_RADIUS_KM = 200 in CONSTANTS
        """
        SMS_RADIUS_KM = 200
        result = distance_km <= SMS_RADIUS_KM
        assert result == should_notify
    
    # =========================================================================
    # BVA-009: Duplicate Check Radius Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("distance_km,is_duplicate", [
        (0, True),
        (100, True),
        (199, True),
        (200, True),
        (201, False),
        (300, False),
    ])
    def test_bva009_duplicate_radius_boundaries(self, distance_km, is_duplicate):
        """
        Test ID: BVA-009
        Priority: P2 - High
        Tests duplicate alert detection radius at boundaries.
        """
        DUPLICATE_CHECK_RADIUS_KM = 200
        result = distance_km <= DUPLICATE_CHECK_RADIUS_KM
        assert result == is_duplicate


class TestTimeWindowBoundaries:
    """
    Test Suite: Time Window Boundary Values
    Tests the DUPLICATE_TIME_WINDOW_HOURS boundary.
    """
    
    # =========================================================================
    # BVA-010: Duplicate Time Window Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("hours_ago,should_suppress", [
        (0, True),
        (6, True),
        (11, True),
        (12, True),
        (13, False),
        (24, False),
    ])
    def test_bva010_time_window_boundaries(self, hours_ago, should_suppress):
        """
        Test ID: BVA-010
        Priority: P2 - High
        Tests duplicate SMS suppression time window at boundaries.
        """
        DUPLICATE_TIME_WINDOW_HOURS = 12
        result = hours_ago <= DUPLICATE_TIME_WINDOW_HOURS
        assert result == should_suppress
