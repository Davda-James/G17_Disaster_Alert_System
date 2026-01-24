"""
Boundary Value Analysis Tests (BVA-001 to BVA-006)
Tests edge cases, boundary conditions, and input validation
"""
import pytest
from unittest.mock import patch
from bson.objectid import ObjectId
from Backend.app import app, mongo
import mongomock
import datetime

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


# ------------------------------------------------------------------
# BVA-001: EMPTY TITLE VALIDATION
# ------------------------------------------------------------------

def test_bva001_empty_title_validation(client, auth_headers):
    """BVA-001: Empty title should be rejected"""
    payload = {
        "title": "",
        "message": "Test message",
        "type": "flood",
        "severity": "high",
        "location": "Delhi, India"
    }
    res = client.post("/api/alerts", headers=auth_headers, json=payload)
    assert res.status_code == 400
    assert "Missing required fields" in res.json["msg"]


# ------------------------------------------------------------------
# BVA-002: NULL MESSAGE VALIDATION
# ------------------------------------------------------------------

def test_bva002_null_message_validation(client, auth_headers):
    """BVA-002: Null message should be rejected"""
    payload = {
        "title": "Test Alert",
        "message": None,
        "type": "flood",
        "severity": "high",
        "location": "Delhi, India"
    }
    res = client.post("/api/alerts", headers=auth_headers, json=payload)
    assert res.status_code == 400
    assert "Missing required fields" in res.json["msg"]


# ------------------------------------------------------------------
# BVA-003: VERY LONG TITLE (BOUNDARY TEST)
# ------------------------------------------------------------------

def test_bva003_very_long_title(client, auth_headers):
    """BVA-003: Very long title (boundary test)"""
    long_title = "A" * 500  # Test with extremely long title
    payload = {
        "title": long_title,
        "message": "Test message",
        "type": "flood",
        "severity": "high",
        "location": "Delhi, India"
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
            assert res.status_code == 201  # Should accept long titles


# ------------------------------------------------------------------
# BVA-004: COORDINATE BOUNDARIES
# ------------------------------------------------------------------

def test_bva004_coordinate_boundaries():
    """BVA-004: Test coordinate boundary values"""
    from Backend.app import get_coordinates

    # Test valid coordinates
    coords = get_coordinates("Delhi", "Delhi")
    assert -90 <= coords["lat"] <= 90
    assert -180 <= coords["lng"] <= 180


# ------------------------------------------------------------------
# BVA-005: INVALID SEVERITY LEVEL
# ------------------------------------------------------------------

def test_bva005_invalid_severity_level(client, auth_headers):
    """BVA-005: Invalid severity level should be accepted (no validation in current code)"""
    payload = {
        "title": "Test Alert",
        "message": "Test message",
        "type": "flood",
        "severity": "invalid_severity",  # Invalid severity
        "location": "Delhi, India"
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
            assert res.status_code == 201  # Currently accepts any severity


# ------------------------------------------------------------------
# BVA-006: EMPTY LOCATION STRING
# ------------------------------------------------------------------

def test_bva006_empty_location_string(client, auth_headers):
    """BVA-006: Empty location should be rejected"""
    payload = {
        "title": "Test Alert",
        "message": "Test message",
        "type": "flood",
        "severity": "high",
        "location": ""
    }
    res = client.post("/api/alerts", headers=auth_headers, json=payload)
    assert res.status_code == 400
