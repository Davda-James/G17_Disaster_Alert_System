"""
Authorization Tests (AUTH-001)
Tests access control, permission validation, and authorization rules
"""
import pytest
from unittest.mock import patch
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


# ------------------------------------------------------------------
# AUTH-001: ONLY CREATOR CAN MODIFY ALERT
# ------------------------------------------------------------------

def test_auth001_only_creator_can_modify_alert(client, auth_headers):
    """AUTH-001: Only alert creator should be able to modify their alert"""
    other_user_id = str(ObjectId())

    res = client.put(
        f"/api/user/{other_user_id}",
        headers=auth_headers,
        json={"name": "Hacker"}
    )
    assert res.status_code == 403
