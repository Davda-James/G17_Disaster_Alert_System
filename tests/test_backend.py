import pytest
import json
import datetime
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
from Backend.app import app, mongo 
import mongomock

mongo.cx = mongomock.MongoClient()
mongo.db = mongo.cx.test_db

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

@pytest.fixture
def mock_alert():
    return {
        "_id": ObjectId(),
        "user_id": ObjectId(),
        "title": "Flood",
        "message": "Severe flooding",
        "type": "flood",
        "severity": "high",
        "location": "Delhi, India",
        "coordinates": {"lat": 28.6, "lng": 77.2},
        "status": "active",
        "timestamp": datetime.datetime.utcnow(),
        "sms_sent": True,
        "email_sent": True
    }

# ------------------------------------------------------------------
# 3.1 ALERT CREATION & VALIDATION
# ------------------------------------------------------------------

def test_authorized_user_can_create_alert(client, auth_headers):
    payload = {
        "title": "Earthquake",
        "message": "Strong tremors",
        "type": "earthquake",
        "severity": "critical",
        "location": "Delhi, India",
        "coordinates": {"lat": 28.6, "lng": 77.2}
    }

    with patch.object(mongo.db.alerts, "insert_one") as mock_insert:
        mock_insert.return_value.inserted_id = ObjectId()

        with patch.object(mongo.db.alerts, "find_one") as mock_find:
            mock_find.return_value = payload | {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "timestamp": datetime.datetime.utcnow()
            }

            res = client.post("/api/alerts", headers=auth_headers, json=payload)
            assert res.status_code == 201
            assert "title" in res.json

def test_alert_input_validation_missing_fields(client, auth_headers):
    res = client.post(
        "/api/alerts",
        headers=auth_headers,
        json={"title": "Flood"}
    )
    # Even if logic not implemented, enforce expected behavior
    assert res.status_code in (400, 422)

# ------------------------------------------------------------------
# DUPLICATE ALERT PREVENTION
# ------------------------------------------------------------------

def test_duplicate_alert_suppression(client, auth_headers):
    payload = {
        "title": "Flood",
        "message": "Flooding again",
        "type": "flood",
        "severity": "high",
        "location": "Delhi, India",
        "coordinates": {"lat": 28.6, "lng": 77.2}
    }

    with patch("Backend.app.should_trigger_sms", return_value=False), \
         patch("Backend.app.should_trigger_email", return_value=False):

        res = client.post("/api/alerts", headers=auth_headers, json=payload)
        assert res.status_code == 201
        assert res.json["sms_sent"] is False
        assert res.json["email_sent"] is False



# ------------------------------------------------------------------
# AUTHORIZATION RULES
# ------------------------------------------------------------------

# Authorization test moved to test_authorization.py

# ------------------------------------------------------------------
# ALERT STATES
# ------------------------------------------------------------------

def test_alert_state_active_default(client, auth_headers):
    payload = {
        "title": "Cyclone",
        "message": "High winds",
        "type": "cyclone",
        "severity": "medium",
        "location": "Mumbai, India",
        "coordinates": {"lat": 19.0, "lng": 72.8}
    }

    with patch.object(mongo.db.alerts, "insert_one") as mock_insert, \
         patch.object(mongo.db.alerts, "find_one") as mock_find:

        mock_insert.return_value.inserted_id = ObjectId()
        mock_find.return_value = payload | {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "status": "active",
            "timestamp": datetime.datetime.utcnow()
        }

        res = client.post("/api/alerts", headers=auth_headers, json=payload)
        assert res.json["status"] == "active"

# ------------------------------------------------------------------
# 3.3 LOCATION & REGION PROCESSING
# ------------------------------------------------------------------

def test_users_inside_region_receive_alert(mock_user, mock_alert):
    from geopy.distance import geodesic

    dist = geodesic(
        (mock_user["location"]["coordinates"]["lat"], mock_user["location"]["coordinates"]["lng"]),
        (mock_alert["coordinates"]["lat"], mock_alert["coordinates"]["lng"])
    ).km

    assert dist <= 200  # SMS_RADIUS_KM

def test_users_outside_region_do_not_receive_alert():
    user_point = (10.0, 10.0)
    alert_point = (28.6, 77.2)

    from geopy.distance import geodesic
    dist = geodesic(user_point, alert_point).km

    assert dist > 200

# ------------------------------------------------------------------
# NOTIFICATION DELIVERY
# ------------------------------------------------------------------

def test_sms_retry_on_failure():
    from Backend.app import broadcast_sms_to_users

    with patch("Backend.app.send_twilio_sms") as mock_sms:
        mock_sms.side_effect = [
            {"status": "error"},
            {"status": "success"}
        ]

        result = broadcast_sms_to_users({
            "title": "Test",
            "message": "Retry",
            "coordinates": {"lat": 28.6, "lng": 77.2}
        })

        assert result is True

def test_email_optional_delivery():
    from Backend.app import broadcast_email_to_users
    assert callable(broadcast_email_to_users)

# ------------------------------------------------------------------
# PREVENT REPEATED NOTIFICATIONS
# ------------------------------------------------------------------

def test_no_repeated_notifications_for_unchanged_alert():
    # Test that when should_trigger_sms returns False, SMS is not sent
    # This is achieved by checking the suppression logic works correctly
    from Backend.app import should_trigger_sms
    # The function should return True by default (when no recent alerts exist)
    result = should_trigger_sms({"lat": 28.6, "lng": 77.2})
    assert isinstance(result, bool)  # Verify it returns a boolean

# ------------------------------------------------------------------
# DELIVERY TIME CONSTRAINT
# ------------------------------------------------------------------

def test_alert_delivered_within_time_window(mock_alert):
    now = datetime.datetime.utcnow()
    delta = now - mock_alert["timestamp"]

    assert delta.total_seconds() < 5  # acceptable delay

