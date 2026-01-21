"""
Functional Tests for DAS Alert System
Test ID Format: FT-XXX (Functional Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify core alert logic functions correctly.
Reference: IEEE 829 Test Case Specification
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alerts.alert_manager import AlertManager, Alert, DisasterType, SeverityLevel
from src.core.config import Config


class TestAlertTriggers:
    """
    Test Suite: Alert Trigger Logic
    Validates that alerts are triggered correctly based on sensor thresholds.
    """
    
    # =========================================================================
    # FT-001: Earthquake Alert Trigger
    # Priority: P1 (Critical)
    # Pre-conditions: AlertManager initialized with default config (threshold=5.0)
    # =========================================================================
    def test_ft001_earthquake_alert_above_threshold(self, alert_manager):
        """
        Test ID: FT-001
        Priority: P1 - Critical
        Pre-conditions: AlertManager with earthquake threshold = 5.0
        Input: Earthquake magnitude = 6.5, Location = "Tokyo, Japan"
        Expected Result: Alert generated with severity HIGH or above
        """
        # Arrange
        disaster_type = DisasterType.EARTHQUAKE
        sensor_value = 6.5
        location = "Tokyo, Japan"
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=disaster_type,
            sensor_value=sensor_value,
            location=location
        )
        
        # Assert
        assert alert is not None, "Alert should be generated for value above threshold"
        assert alert.disaster_type == DisasterType.EARTHQUAKE
        assert alert.sensor_value == 6.5
        assert alert.location == "Tokyo, Japan"
        assert alert.severity.value >= SeverityLevel.HIGH.value
    
    # =========================================================================
    # FT-002: Earthquake No Alert Below Threshold
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft002_earthquake_no_alert_below_threshold(self, alert_manager):
        """
        Test ID: FT-002
        Priority: P1 - Critical
        Pre-conditions: AlertManager with earthquake threshold = 5.0
        Input: Earthquake magnitude = 4.5
        Expected Result: No alert generated
        """
        # Arrange
        disaster_type = DisasterType.EARTHQUAKE
        sensor_value = 4.5
        location = "San Francisco, USA"
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=disaster_type,
            sensor_value=sensor_value,
            location=location
        )
        
        # Assert
        assert alert is None, "No alert should be generated for value below threshold"
    
    # =========================================================================
    # FT-003: Tsunami Alert - Critical Severity
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft003_tsunami_critical_severity(self, alert_manager):
        """
        Test ID: FT-003
        Priority: P1 - Critical
        Pre-conditions: AlertManager with tsunami threshold = 2.0
        Input: Wave height = 12.0 meters
        Expected Result: Alert with CRITICAL or CATASTROPHIC severity
        """
        # Arrange
        disaster_type = DisasterType.TSUNAMI
        sensor_value = 12.0
        location = "Coastal Region, Indonesia"
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=disaster_type,
            sensor_value=sensor_value,
            location=location
        )
        
        # Assert
        assert alert is not None
        assert alert.severity.value >= SeverityLevel.CRITICAL.value
        assert "TSUNAMI" in alert.message.upper()
    
    # =========================================================================
    # FT-004: Flood Alert Generation
    # Priority: P2 (High)
    # =========================================================================
    def test_ft004_flood_alert_generation(self, alert_manager):
        """
        Test ID: FT-004
        Priority: P2 - High
        Pre-conditions: AlertManager with flood threshold = 3.0
        Input: Water level = 5.5 meters
        Expected Result: Flood alert generated
        """
        # Arrange
        disaster_type = DisasterType.FLOOD
        sensor_value = 5.5
        location = "Mumbai, India"
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=disaster_type,
            sensor_value=sensor_value,
            location=location
        )
        
        # Assert
        assert alert is not None
        assert alert.disaster_type == DisasterType.FLOOD
        assert alert.severity.value >= SeverityLevel.HIGH.value
    
    # =========================================================================
    # FT-005: Cyclone Alert Generation
    # Priority: P2 (High)
    # =========================================================================
    def test_ft005_cyclone_alert_generation(self, alert_manager):
        """
        Test ID: FT-005
        Priority: P2 - High
        Pre-conditions: AlertManager with cyclone threshold = 120 km/h
        Input: Wind speed = 200 km/h
        Expected Result: Cyclone alert generated with HIGH severity
        """
        # Arrange
        disaster_type = DisasterType.CYCLONE
        sensor_value = 200.0
        location = "Bay of Bengal"
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=disaster_type,
            sensor_value=sensor_value,
            location=location
        )
        
        # Assert
        assert alert is not None
        assert alert.disaster_type == DisasterType.CYCLONE
        assert alert.severity == SeverityLevel.HIGH


class TestSeverityClassification:
    """
    Test Suite: Severity Level Classification
    Validates correct severity assignment based on sensor values.
    """
    
    # =========================================================================
    # FT-006: Severity Classification - LOW
    # Priority: P2 (High)
    # =========================================================================
    def test_ft006_severity_classification_low(self):
        """
        Test ID: FT-006
        Priority: P2 - High
        Input: Earthquake magnitude = 3.5
        Expected Result: LOW severity
        """
        severity = SeverityLevel.from_value(3.5, DisasterType.EARTHQUAKE)
        assert severity == SeverityLevel.LOW
    
    # =========================================================================
    # FT-007: Severity Classification - CATASTROPHIC
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft007_severity_classification_catastrophic(self):
        """
        Test ID: FT-007
        Priority: P1 - Critical
        Input: Earthquake magnitude = 9.0
        Expected Result: CATASTROPHIC severity
        """
        severity = SeverityLevel.from_value(9.0, DisasterType.EARTHQUAKE)
        assert severity == SeverityLevel.CATASTROPHIC
    
    # =========================================================================
    # FT-008: All Severity Levels for Earthquake
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("magnitude,expected", [
        (2.0, SeverityLevel.LOW),
        (3.0, SeverityLevel.LOW),
        (5.0, SeverityLevel.MEDIUM),
        (6.5, SeverityLevel.HIGH),
        (7.5, SeverityLevel.CRITICAL),
        (8.5, SeverityLevel.CATASTROPHIC),
    ])
    def test_ft008_earthquake_severity_levels(self, magnitude, expected):
        """
        Test ID: FT-008
        Priority: P2 - High
        Tests all severity levels for earthquake
        """
        severity = SeverityLevel.from_value(magnitude, DisasterType.EARTHQUAKE)
        assert severity == expected


class TestAlertAcknowledgment:
    """
    Test Suite: Alert Acknowledgment Flow
    Validates alert acknowledgment functionality.
    """
    
    # =========================================================================
    # FT-009: Acknowledge Alert
    # Priority: P2 (High)
    # =========================================================================
    def test_ft009_acknowledge_alert(self, alert_manager):
        """
        Test ID: FT-009
        Priority: P2 - High
        Pre-conditions: An active alert exists
        Input: Alert ID
        Expected Result: Alert marked as acknowledged
        """
        # Arrange - Create an alert
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.0,
            location="Test Location"
        )
        assert alert is not None
        alert_id = alert.alert_id
        
        # Act
        result = alert_manager.acknowledge_alert(alert_id)
        
        # Assert
        assert result is True
        assert alert.acknowledged is True
    
    # =========================================================================
    # FT-010: Acknowledge Non-existent Alert
    # Priority: P3 (Medium)
    # =========================================================================
    def test_ft010_acknowledge_nonexistent_alert(self, alert_manager):
        """
        Test ID: FT-010
        Priority: P3 - Medium
        Input: Non-existent alert ID
        Expected Result: Returns False
        """
        result = alert_manager.acknowledge_alert("NONEXISTENT-ID")
        assert result is False


class TestNotificationCallbacks:
    """
    Test Suite: Notification Callback System
    Validates callback registration and invocation.
    """
    
    # =========================================================================
    # FT-011: Callback Invoked on Alert
    # Priority: P1 (Critical)
    # =========================================================================
    def test_ft011_callback_invoked_on_alert(self, alert_manager, mock_notification_callback):
        """
        Test ID: FT-011
        Priority: P1 - Critical
        Pre-conditions: Callback registered
        Expected Result: Callback invoked when alert generated
        """
        # Arrange
        alert_manager.register_notification_callback(mock_notification_callback)
        
        # Act
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.0,
            location="Test Location"
        )
        
        # Assert
        mock_notification_callback.assert_called_once()
        assert alert.notification_sent is True
    
    # =========================================================================
    # FT-012: Multiple Callbacks
    # Priority: P2 (High)
    # =========================================================================
    def test_ft012_multiple_callbacks(self, alert_manager):
        """
        Test ID: FT-012
        Priority: P2 - High
        Pre-conditions: Multiple callbacks registered
        Expected Result: All callbacks invoked
        """
        # Arrange
        callback1 = Mock(return_value=True)
        callback2 = Mock(return_value=True)
        alert_manager.register_notification_callback(callback1)
        alert_manager.register_notification_callback(callback2)
        
        # Act
        alert_manager.process_sensor_data(
            disaster_type=DisasterType.TSUNAMI,
            sensor_value=5.0,
            location="Test Coast"
        )
        
        # Assert
        callback1.assert_called_once()
        callback2.assert_called_once()


class TestAlertStatistics:
    """
    Test Suite: Alert Statistics Calculation
    Validates statistics are calculated correctly.
    """
    
    # =========================================================================
    # FT-013: Statistics Calculation
    # Priority: P3 (Medium)
    # =========================================================================
    def test_ft013_statistics_calculation(self, alert_manager):
        """
        Test ID: FT-013
        Priority: P3 - Medium
        Pre-conditions: Multiple alerts generated
        Expected Result: Accurate statistics
        """
        # Arrange - Generate multiple alerts
        alert_manager.process_sensor_data(DisasterType.EARTHQUAKE, 7.0, "Location A")
        alert_manager.process_sensor_data(DisasterType.TSUNAMI, 5.0, "Location B")
        alert_manager.process_sensor_data(DisasterType.FLOOD, 6.0, "Location C")
        
        # Act
        stats = alert_manager.get_alert_statistics()
        
        # Assert
        assert stats["total_alerts"] == 3
        assert stats["by_disaster_type"]["EARTHQUAKE"] == 1
        assert stats["by_disaster_type"]["TSUNAMI"] == 1
        assert stats["by_disaster_type"]["FLOOD"] == 1
