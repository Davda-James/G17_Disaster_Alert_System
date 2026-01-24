"""
Integration Tests (IT-001 to IT-003)
Tests complete workflows across multiple components and systems
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


# ------------------------------------------------------------------
# IT-001: END-TO-END ALERT WORKFLOW
# ------------------------------------------------------------------

@pytest.mark.integration
def test_it001_end_to_end_alert_workflow(client, generate_unique_email_fixture):
    """IT-001: End-to-end alert creation and retrieval workflow"""
    # Step 1: Register a new user
    email = generate_unique_email_fixture("integration@test.com")
    signup_data = {
        "name": "Integration Test User",
        "email": email,
        "password": "testpass123",
        "phone": "7777777777",
        "city": "Chennai",
        "state": "Tamil Nadu"
    }

    with patch("Backend.app.get_coordinates") as mock_coords:
        mock_coords.return_value = {"lat": 13.0827, "lng": 80.2707}

        signup_res = client.post("/api/signup", json=signup_data)
        assert signup_res.status_code == 201
        token = signup_res.json["token"]
        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Step 2: Create an alert
    alert_data = {
        "title": "Integration Test Alert",
        "message": "Testing complete workflow",
        "type": "cyclone",
        "severity": "medium",
        "location": "Chennai, Tamil Nadu"
    }

    with patch.object(mongo.db.alerts, "insert_one") as mock_insert, \
         patch("Backend.app.should_trigger_sms") as mock_sms, \
         patch("Backend.app.should_trigger_email") as mock_email:

        mock_insert.return_value.inserted_id = ObjectId()
        mock_sms.return_value = True
        mock_email.return_value = True

        with patch.object(mongo.db.alerts, "find_one") as mock_find:
            mock_find.return_value = alert_data | {
                "_id": ObjectId(),
                "user_id": ObjectId(),
                "status": "active",
                "timestamp": datetime.datetime.utcnow(),
                "sms_sent": True,
                "email_sent": True
            }

            alert_res = client.post("/api/alerts", headers=auth_headers, json=alert_data)
            assert alert_res.status_code == 201

    # Step 3: Retrieve alerts
    alerts_res = client.get("/api/alerts", headers=auth_headers)
    assert alerts_res.status_code == 200
    assert isinstance(alerts_res.json, list)


# ------------------------------------------------------------------
# IT-002: COMPLETE AUTHENTICATION FLOW INTEGRATION
# ------------------------------------------------------------------

@pytest.mark.integration
def test_it002_user_authentication_integration(client, generate_unique_email_fixture):
    """IT-002: Complete authentication flow integration"""
    # Register user
    user_email = generate_unique_email_fixture("auth.integration@test.com")
    user_data = {
        "name": "Auth Integration User",
        "email": user_email,
        "password": "securepass123",
        "phone": "5555555555",
        "city": "Pune",
        "state": "Maharashtra"
    }

    with patch("Backend.app.get_coordinates") as mock_coords:
        mock_coords.return_value = {"lat": 18.5204, "lng": 73.8567}

        # Signup
        signup_res = client.post("/api/signup", json=user_data)
        assert signup_res.status_code == 201
        signup_token = signup_res.json["token"]

        # Login
        login_data = {"email": user_email, "password": user_data["password"]}
        login_res = client.post("/api/login", json=login_data)
        assert login_res.status_code == 200
        login_token = login_res.json["token"]

        # Verify tokens are different (JWT tokens are unique per generation)
        assert signup_token != login_token

        # Access protected endpoint
        auth_headers = {"Authorization": f"Bearer {login_token}"}
        me_res = client.get("/api/me", headers=auth_headers)
        assert me_res.status_code == 200
        assert me_res.json["user"]["email"] == user_email


# ------------------------------------------------------------------
# IT-003: ALERT TIME FILTERING INTEGRATION
# ------------------------------------------------------------------

@pytest.mark.integration
def test_it003_alert_time_filtering_integration(client, auth_headers):
    """IT-003: Alert filtering by time periods integration"""
    # Create alerts with different timestamps
    base_time = datetime.datetime.utcnow()

    alerts = [
        {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "title": "Recent Alert",
            "message": "Recent disaster",
            "type": "flood",
            "severity": "high",
            "location": "Delhi, India",
            "coordinates": {"lat": 28.6, "lng": 77.2},
            "status": "active",
            "timestamp": base_time,  # Now
            "sms_sent": False,
            "email_sent": False
        },
        {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "title": "Week Old Alert",
            "message": "Old disaster",
            "type": "earthquake",
            "severity": "medium",
            "location": "Mumbai, India",
            "coordinates": {"lat": 19.0760, "lng": 72.8777},
            "status": "active",
            "timestamp": base_time - datetime.timedelta(days=10),  # 10 days ago
            "sms_sent": False,
            "email_sent": False
        }
    ]

    with patch.object(mongo.db.alerts, "find") as mock_find:
        mock_find.return_value.sort.return_value = alerts

        # Test 24h filter
        res_24h = client.get("/api/alerts?time=24h", headers=auth_headers)
        assert res_24h.status_code == 200

        # Test 7d filter
        res_7d = client.get("/api/alerts?time=7d", headers=auth_headers)
        assert res_7d.status_code == 200

        # Test 30d filter (default)
        res_30d = client.get("/api/alerts?time=30d", headers=auth_headers)
        assert res_30d.status_code == 200
