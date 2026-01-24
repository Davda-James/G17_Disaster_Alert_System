"""
Pytest configuration and shared fixtures
"""
import pytest
import uuid
import mongomock
from Backend.app import app, mongo


def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


@pytest.fixture(scope="function", autouse=True)
def reset_mongo_db():
    """Reset mock MongoDB before each test"""
    mongo.cx = mongomock.MongoClient()
    mongo.db = mongo.cx.test_db
    yield
    # Cleanup after test
    mongo.cx.close()


@pytest.fixture(scope="session")
def generate_unique_email_fixture():
    """Fixture to generate unique email addresses with UUID suffix"""
    def _generate_email(base_email):
        local, domain = base_email.split("@")
        return f"{local}_{uuid.uuid4().hex[:8]}@{domain}"
    return _generate_email


# Module-level function for import
def generate_unique_email(base_email):
    """Generate a unique email address with UUID suffix"""
    local, domain = base_email.split("@")
    return f"{local}_{uuid.uuid4().hex[:8]}@{domain}"
