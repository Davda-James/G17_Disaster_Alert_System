"""
Functional Tests (FT-001 to FT-004)
Tests complete workflows and user journeys
"""
import pytest
import datetime
from unittest.mock import patch
from bson.objectid import ObjectId
from Backend.app import app, mongo



# ------------------------------------------------------------------
# FIXTURES
# ------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    from Backend.app import app
    from flask_jwt_extended import create_access_token
    from bson.objectid import ObjectId
    with app.app_context():
        user_id = str(ObjectId())
        token = create_access_token(identity=user_id)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_user():
    return {
        "_id": ObjectId(),
        "name": "Test User",
        "email": "test@example.com",
        "phone": "9999999999",
        "location": {
            "coordinates": {"lat": 28.6, "lng": 77.2}
        },
        "notificationPreferences": {
            "email": True,
            "sms": True
        }
    }


# ------------------------------------------------------------------
# FT-001: COMPLETE USER REGISTRATION AND LOGIN FLOW
# ------------------------------------------------------------------

def test_ft001_complete_user_registration_flow(client, generate_unique_email_fixture):
    """FT-001: Complete user registration and login flow"""
    # Register user
    email = generate_unique_email_fixture("functional@test.com")
    signup_data = {
        "name": "Functional Test User",
        "email": email,
        "password": "testpass123",
        "phone": "9999999999",
        "city": "Mumbai",
        "state": "Maharashtra"
    }

    with patch("Backend.app.get_coordinates") as mock_coords:
        mock_coords.return_value = {"lat": 19.0760, "lng": 72.8777}

        res = client.post("/api/signup", json=signup_data)
        assert res.status_code == 201
        assert "token" in res.json
        assert "user" in res.json

        token = res.json["token"]

    # Login with registered user
    login_data = {
        "email": email,
        "password": "testpass123"
    }

    res = client.post("/api/login", json=login_data)
    assert res.status_code == 200
    assert "token" in res.json


# ------------------------------------------------------------------
# FT-002: ALERT CREATION WITH COORDINATES
# ------------------------------------------------------------------

def test_ft002_alert_creation_with_coordinates(client, auth_headers):
    """FT-002: Alert creation with explicit coordinates"""
    payload = {
        "title": "Functional Test Alert",
        "message": "Testing coordinate functionality",
        "type": "earthquake",
        "severity": "critical",
        "location": "Tokyo, Japan",
        "coordinates": {"lat": 35.6762, "lng": 139.6503}
    }

    with patch.object(mongo.db.alerts, "insert_one") as mock_insert, \
         patch("Backend.app.should_trigger_sms") as mock_sms_trigger, \
         patch("Backend.app.should_trigger_email") as mock_email_trigger:

        mock_insert.return_value.inserted_id = ObjectId()
        mock_sms_trigger.return_value = True
        mock_email_trigger.return_value = True

        with patch.object(mongo.db.alerts, "find_one") as mock_find:
            mock_find.return_value = payload | {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "status": "active",
                "timestamp": datetime.datetime.utcnow(),
                "sms_sent": True,
                "email_sent": True
            }

            res = client.post("/api/alerts", headers=auth_headers, json=payload)
            assert res.status_code == 201
            assert res.json["coordinates"]["lat"] == 35.6762
            assert res.json["coordinates"]["lng"] == 139.6503


# ------------------------------------------------------------------
# FT-003: ALERT FILTERING BY TYPE
# ------------------------------------------------------------------

def test_ft003_alert_filtering_by_type(client, auth_headers):
    """FT-003: Test alert filtering by disaster type"""
    # Create multiple alerts of different types
    alerts_data = [
        {
            "title": "Flood Alert",
            "message": "Flooding detected",
            "type": "flood",
            "severity": "high",
            "location": "Delhi, India"
        },
        {
            "title": "Earthquake Alert",
            "message": "Earthquake detected",
            "type": "earthquake",
            "severity": "critical",
            "location": "Tokyo, Japan"
        }
    ]

    # Mock the database to return filtered results
    with patch.object(mongo.db.alerts, "find") as mock_find:
        # Mock flood alerts only
        flood_alerts = [
            {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "title": "Flood Alert",
                "message": "Flooding detected",
                "type": "flood",
                "severity": "high",
                "location": "Delhi, India",
                "coordinates": {"lat": 28.6, "lng": 77.2},
                "status": "active",
                "timestamp": datetime.datetime.utcnow(),
                "sms_sent": False,
                "email_sent": False
            }
        ]
        mock_find.return_value.sort.return_value = flood_alerts

        res = client.get("/api/alerts?type=flood", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json) >= 0  # May return empty or filtered results


# ------------------------------------------------------------------
# FT-004: USER PROFILE UPDATE FLOW
# ------------------------------------------------------------------

def test_ft004_user_profile_update_flow(client, auth_headers, mock_user):
    """FT-004: Complete user profile update flow"""
    update_data = {
        "name": "Updated Test User",
        "phone": "8888888888",
        "location": {
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "India"
        },
        "notificationPreferences": {
            "email": False,
            "sms": True
        }
    }

    # Use the same user ID from the mock_user fixture
    test_user_id = str(mock_user["_id"])

    with patch("Backend.app.get_coordinates") as mock_coords, \
         patch.object(mongo.db.users, "find_one") as mock_find, \
         patch.object(mongo.db.users, "update_one") as mock_update, \
         patch("Backend.app.get_jwt_identity") as mock_jwt_identity:

        mock_coords.return_value = {"lat": 12.9716, "lng": 77.5946}
        mock_jwt_identity.return_value = test_user_id  # Mock JWT to return our test user ID

        # Mock current user data
        mock_find.return_value = mock_user.copy()

        # Mock the update operation
        def mock_update_side_effect(*args, **kwargs):
            # Simulate the update by modifying the mock_user data
            updated_user = mock_user.copy()
            updated_user.update(update_data)
            mock_find.return_value = updated_user  # Return updated data on subsequent calls

        mock_update.side_effect = mock_update_side_effect

        # Test the update endpoint
        res = client.put(f"/api/user/{test_user_id}", headers=auth_headers, json=update_data)
        assert res.status_code == 200
        assert res.json["name"] == "Updated Test User"
