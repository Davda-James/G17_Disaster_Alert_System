"""
PyTest Configuration and Fixtures
Provides shared fixtures for all Backend API test modules.

Tests the Backend Flask API (Backend/app.py)
"""

import os
import sys
import pytest
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent.parent.parent / "Backend"
sys.path.insert(0, str(backend_path))


# Test markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests"
    )
    config.addinivalue_line(
        "markers", "safety: marks tests as safety-critical tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Shared test data fixtures
@pytest.fixture
def sample_user_data():
    """Provide sample user registration data."""
    return {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "SecurePass123!",
        "phone": "+919876543210",
        "city": "Mumbai",
        "state": "Maharashtra"
    }


@pytest.fixture
def sample_admin_data():
    """Provide sample admin user data (ends with .admin@gmail.com)."""
    return {
        "name": "Admin User",
        "email": "disaster.admin@gmail.com",
        "password": "AdminPass123!",
        "phone": "+919876543211",
        "city": "Delhi",
        "state": "Delhi"
    }


@pytest.fixture
def sample_alert_data():
    """Provide sample alert creation data."""
    return {
        "title": "Flood Warning",
        "message": "Heavy flooding expected in low-lying areas. Please evacuate.",
        "type": "flood",
        "severity": "high",
        "location": "Mumbai, Maharashtra",
        "coordinates": {"lat": 19.0760, "lng": 72.8777}
    }


@pytest.fixture
def sample_earthquake_alert():
    """Provide sample earthquake alert data."""
    return {
        "title": "Earthquake Alert",
        "message": "Magnitude 6.5 earthquake detected. Take cover immediately.",
        "type": "earthquake",
        "severity": "critical",
        "location": "Shimla, Himachal Pradesh",
        "coordinates": {"lat": 31.1048, "lng": 77.1734}
    }


@pytest.fixture
def sample_cyclone_alert():
    """Provide sample cyclone alert data."""
    return {
        "title": "Cyclone Warning",
        "message": "Category 4 cyclone approaching. Evacuate coastal areas.",
        "type": "cyclone",
        "severity": "critical",
        "location": "Chennai, Tamil Nadu",
        "coordinates": {"lat": 13.0827, "lng": 80.2707}
    }


@pytest.fixture
def multiple_users():
    """Provide multiple user data for bulk testing."""
    return [
        {
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "password": "TestPass123!",
            "phone": f"+91987654{i:04d}",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        for i in range(10)
    ]


@pytest.fixture
def multiple_alerts():
    """Provide multiple alert data for bulk testing."""
    alert_types = ["flood", "earthquake", "cyclone", "tsunami", "fire"]
    severities = ["low", "medium", "high", "critical"]
    locations = [
        ("Mumbai", "Maharashtra", 19.0760, 72.8777),
        ("Delhi", "Delhi", 28.6139, 77.2090),
        ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
        ("Kolkata", "West Bengal", 22.5726, 88.3639),
        ("Bangalore", "Karnataka", 12.9716, 77.5946),
    ]
    
    alerts = []
    for i in range(20):
        loc = locations[i % len(locations)]
        alerts.append({
            "title": f"Alert {i}: {alert_types[i % len(alert_types)].title()} Warning",
            "message": f"Emergency alert #{i}. Please follow safety protocols.",
            "type": alert_types[i % len(alert_types)],
            "severity": severities[i % len(severities)],
            "location": f"{loc[0]}, {loc[1]}",
            "coordinates": {"lat": loc[2], "lng": loc[3]}
        })
    return alerts
