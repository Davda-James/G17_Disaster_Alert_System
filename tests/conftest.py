"""
PyTest Configuration and Fixtures
Provides shared fixtures for all DAS test modules.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import Config
from src.core.logger import DASLogger
from src.alerts.alert_manager import AlertManager, DisasterType, SeverityLevel
from src.api.messaging import SMSGateway, EmailGateway, NotificationService
from src.db.storage import DatabaseManager, EmergencyContact


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset logger singleton between tests."""
    yield
    DASLogger.reset()


@pytest.fixture
def default_config():
    """Provide a default configuration for testing."""
    return Config(
        earthquake_magnitude_threshold=5.0,
        tsunami_wave_height_threshold=2.0,
        flood_water_level_threshold=3.0,
        cyclone_wind_speed_threshold=120.0,
        api_timeout_seconds=30,
        max_retry_attempts=3,
        simulate_network_failure=False,
        simulate_db_corruption=False,
        simulate_high_latency=False,
    )


@pytest.fixture
def failure_config():
    """Configuration with network failure simulation enabled."""
    return Config(
        earthquake_magnitude_threshold=5.0,
        tsunami_wave_height_threshold=2.0,
        flood_water_level_threshold=3.0,
        cyclone_wind_speed_threshold=120.0,
        api_timeout_seconds=30,
        max_retry_attempts=3,
        simulate_network_failure=True,
        simulate_db_corruption=False,
        simulate_high_latency=False,
    )


@pytest.fixture
def db_corruption_config():
    """Configuration with database corruption simulation enabled."""
    return Config(
        earthquake_magnitude_threshold=5.0,
        tsunami_wave_height_threshold=2.0,
        flood_water_level_threshold=3.0,
        cyclone_wind_speed_threshold=120.0,
        api_timeout_seconds=30,
        max_retry_attempts=3,
        simulate_network_failure=False,
        simulate_db_corruption=True,
        simulate_high_latency=False,
    )


@pytest.fixture
def high_latency_config():
    """Configuration with high latency simulation enabled."""
    return Config(
        earthquake_magnitude_threshold=5.0,
        tsunami_wave_height_threshold=2.0,
        flood_water_level_threshold=3.0,
        cyclone_wind_speed_threshold=120.0,
        api_timeout_seconds=30,
        max_retry_attempts=3,
        simulate_network_failure=False,
        simulate_db_corruption=False,
        simulate_high_latency=True,
        latency_delay_ms=100,  # 100ms for tests
    )


@pytest.fixture
def alert_manager(default_config):
    """Provide an AlertManager instance."""
    return AlertManager(config=default_config)


@pytest.fixture
def sms_gateway(default_config):
    """Provide an SMS Gateway instance."""
    return SMSGateway(config=default_config)


@pytest.fixture
def email_gateway(default_config):
    """Provide an Email Gateway instance."""
    return EmailGateway(config=default_config)


@pytest.fixture
def notification_service(default_config):
    """Provide a Notification Service instance."""
    return NotificationService(config=default_config)


@pytest.fixture
def database_manager(default_config):
    """Provide a Database Manager instance."""
    db = DatabaseManager(config=default_config)
    db.connect()
    yield db
    db.disconnect()


@pytest.fixture
def sample_contacts():
    """Provide sample emergency contacts for testing."""
    return [
        EmergencyContact(
            contact_id="EC001",
            name="Emergency Response Team A",
            phone="+1234567890",
            email="team-a@emergency.gov",
            region="North",
            priority_level=1,
        ),
        EmergencyContact(
            contact_id="EC002",
            name="Fire Department",
            phone="+1234567891",
            email="fire@emergency.gov",
            region="North",
            priority_level=2,
        ),
        EmergencyContact(
            contact_id="EC003",
            name="Medical Team",
            phone="+1234567892",
            email="medical@emergency.gov",
            region="South",
            priority_level=1,
        ),
    ]


@pytest.fixture
def mock_notification_callback():
    """Provide a mock notification callback."""
    callback = Mock(return_value=True)
    return callback


# Test markers
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
