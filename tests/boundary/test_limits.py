"""
Boundary Value Analysis Tests for DAS Alert System
Test ID Format: BVA-XXX (Boundary Value Analysis)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify system behavior at boundary conditions.
Reference: IEEE 829 Test Case Specification, ISTQB Boundary Value Analysis
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alerts.alert_manager import AlertManager, DisasterType, SeverityLevel
from src.api.messaging import SMSGateway, EmailGateway
from src.core.config import Config


class TestEarthquakeMagnitudeBoundaries:
    """
    Test Suite: Earthquake Magnitude Boundary Values
    Threshold: 5.0 (default)
    Test points: 4.9, 5.0, 5.1, 0, -1, 10, 10.1
    """
    
    # =========================================================================
    # BVA-001: Just Below Threshold
    # Priority: P1 (Critical)
    # =========================================================================
    def test_bva001_earthquake_just_below_threshold(self, alert_manager):
        """
        Test ID: BVA-001
        Priority: P1 - Critical
        Input: Magnitude = 4.99 (just below threshold of 5.0)
        Expected Result: No alert generated
        Boundary Type: Lower boundary - valid, no trigger
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=4.99,
            location="Test Location"
        )
        assert alert is None, "Alert should NOT be triggered for values just below threshold"
    
    # =========================================================================
    # BVA-002: Exactly At Threshold
    # Priority: P1 (Critical)
    # =========================================================================
    def test_bva002_earthquake_exactly_at_threshold(self, alert_manager):
        """
        Test ID: BVA-002
        Priority: P1 - Critical
        Input: Magnitude = 5.0 (exactly at threshold)
        Expected Result: Alert generated
        Boundary Type: ON point
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=5.0,
            location="Test Location"
        )
        assert alert is not None, "Alert SHOULD be triggered at exact threshold"
        assert alert.sensor_value == 5.0
    
    # =========================================================================
    # BVA-003: Just Above Threshold
    # Priority: P1 (Critical)
    # =========================================================================
    def test_bva003_earthquake_just_above_threshold(self, alert_manager):
        """
        Test ID: BVA-003
        Priority: P1 - Critical
        Input: Magnitude = 5.01 (just above threshold)
        Expected Result: Alert generated
        Boundary Type: Upper boundary - valid trigger
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=5.01,
            location="Test Location"
        )
        assert alert is not None, "Alert should be triggered for values above threshold"
    
    # =========================================================================
    # BVA-004: Zero Value
    # Priority: P2 (High)
    # =========================================================================
    def test_bva004_earthquake_zero_value(self, alert_manager):
        """
        Test ID: BVA-004
        Priority: P2 - High
        Input: Magnitude = 0
        Expected Result: No alert (valid input, below threshold)
        Boundary Type: Minimum valid value
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=0,
            location="Test Location"
        )
        assert alert is None
    
    # =========================================================================
    # BVA-005: Negative Value (Invalid)
    # Priority: P1 (Critical)
    # =========================================================================
    def test_bva005_earthquake_negative_value(self, alert_manager):
        """
        Test ID: BVA-005
        Priority: P1 - Critical
        Input: Magnitude = -1.0 (invalid input)
        Expected Result: No alert, handled gracefully
        Boundary Type: Invalid input
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=-1.0,
            location="Test Location"
        )
        assert alert is None, "Negative values should not trigger alerts"
    
    # =========================================================================
    # BVA-006: Maximum Valid Value
    # Priority: P2 (High)
    # =========================================================================
    def test_bva006_earthquake_maximum_value(self, alert_manager):
        """
        Test ID: BVA-006
        Priority: P2 - High
        Input: Magnitude = 10.0 (Richter scale max)
        Expected Result: Alert with CATASTROPHIC severity
        Boundary Type: Maximum valid value
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=10.0,
            location="Test Location"
        )
        assert alert is not None
        assert alert.severity == SeverityLevel.CATASTROPHIC
    
    # =========================================================================
    # BVA-007: Beyond Maximum (Edge Case)
    # Priority: P3 (Medium)
    # =========================================================================
    def test_bva007_earthquake_beyond_maximum(self, alert_manager):
        """
        Test ID: BVA-007
        Priority: P3 - Medium
        Input: Magnitude = 12.0 (beyond Richter scale)
        Expected Result: System handles gracefully
        Boundary Type: Edge case / stress value
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=12.0,
            location="Test Location"
        )
        # Should still work - sensor error or future scale
        assert alert is not None
        assert alert.severity == SeverityLevel.CATASTROPHIC


class TestTsunamiBoundaries:
    """
    Test Suite: Tsunami Wave Height Boundary Values
    Threshold: 2.0 meters (default)
    """
    
    # =========================================================================
    # BVA-008: Tsunami Threshold Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("wave_height,should_alert", [
        (1.99, False),  # Just below
        (2.0, True),    # Exactly at
        (2.01, True),   # Just above
        (0.0, False),   # Minimum
        (-0.5, False),  # Invalid
        (20.0, True),   # Extreme
    ])
    def test_bva008_tsunami_boundaries(self, alert_manager, wave_height, should_alert):
        """
        Test ID: BVA-008
        Priority: P1 - Critical
        Parametrized boundary test for tsunami thresholds
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.TSUNAMI,
            sensor_value=wave_height,
            location="Coastal Area"
        )
        if should_alert:
            assert alert is not None
        else:
            assert alert is None


class TestFloodBoundaries:
    """
    Test Suite: Flood Water Level Boundary Values
    Threshold: 3.0 meters (default)
    """
    
    # =========================================================================
    # BVA-009: Flood Threshold Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("water_level,should_alert", [
        (2.99, False),
        (3.0, True),
        (3.01, True),
        (0.0, False),
        (15.0, True),  # Extreme flood
    ])
    def test_bva009_flood_boundaries(self, alert_manager, water_level, should_alert):
        """
        Test ID: BVA-009
        Priority: P1 - Critical
        Parametrized boundary test for flood thresholds
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.FLOOD,
            sensor_value=water_level,
            location="River Basin"
        )
        if should_alert:
            assert alert is not None
        else:
            assert alert is None


class TestCycloneBoundaries:
    """
    Test Suite: Cyclone Wind Speed Boundary Values
    Threshold: 120.0 km/h (default)
    """
    
    # =========================================================================
    # BVA-010: Cyclone Threshold Boundaries
    # Priority: P1 (Critical)
    # =========================================================================
    @pytest.mark.parametrize("wind_speed,should_alert", [
        (119.9, False),
        (120.0, True),
        (120.1, True),
        (0.0, False),
        (350.0, True),  # Extreme cyclone
    ])
    def test_bva010_cyclone_boundaries(self, alert_manager, wind_speed, should_alert):
        """
        Test ID: BVA-010
        Priority: P1 - Critical
        Parametrized boundary test for cyclone thresholds
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.CYCLONE,
            sensor_value=wind_speed,
            location="Coastal City"
        )
        if should_alert:
            assert alert is not None
        else:
            assert alert is None


class TestInputValidationBoundaries:
    """
    Test Suite: Input Validation Boundary Cases
    Tests system behavior with invalid/edge-case inputs
    """
    
    # =========================================================================
    # BVA-011: Empty Location
    # Priority: P1 (Critical)
    # =========================================================================
    def test_bva011_empty_location(self, alert_manager):
        """
        Test ID: BVA-011
        Priority: P1 - Critical
        Input: Empty location string
        Expected: No alert (invalid input)
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.0,
            location=""
        )
        assert alert is None
    
    # =========================================================================
    # BVA-012: Whitespace-only Location
    # Priority: P2 (High)
    # =========================================================================
    def test_bva012_whitespace_location(self, alert_manager):
        """
        Test ID: BVA-012
        Priority: P2 - High
        Input: Whitespace-only location
        Expected: No alert (invalid input)
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.0,
            location="   "
        )
        assert alert is None
    
    # =========================================================================
    # BVA-013: Location with Leading/Trailing Spaces
    # Priority: P3 (Medium)
    # =========================================================================
    def test_bva013_location_trimmed(self, alert_manager):
        """
        Test ID: BVA-013
        Priority: P3 - Medium
        Input: Location with extra spaces
        Expected: Alert created with trimmed location
        """
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.0,
            location="  Tokyo, Japan  "
        )
        assert alert is not None
        assert alert.location == "Tokyo, Japan"


class TestPhoneValidationBoundaries:
    """
    Test Suite: Phone Number Validation Boundaries
    """
    
    # =========================================================================
    # BVA-014: Phone Number Length Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("phone,is_valid", [
        ("+1234567890", True),      # 10 digits - minimum valid
        ("+123456789012345", True), # 15 digits - maximum valid
        ("+123456789", False),      # 9 digits - too short
        ("+1234567890123456", False), # 16 digits - too long
        ("", False),                # Empty
        ("+", False),               # Only prefix
    ])
    def test_bva014_phone_validation_boundaries(self, sms_gateway, phone, is_valid):
        """
        Test ID: BVA-014
        Priority: P2 - High
        Tests phone number length validation boundaries
        """
        result = sms_gateway.send(phone, "Test message")
        assert result.success == is_valid


class TestEmailValidationBoundaries:
    """
    Test Suite: Email Validation Boundaries
    """
    
    # =========================================================================
    # BVA-015: Email Format Boundaries
    # Priority: P2 (High)
    # =========================================================================
    @pytest.mark.parametrize("email,is_valid", [
        ("test@example.com", True),
        ("a@b.c", True),           # Minimum valid
        ("user.name+tag@domain.co.uk", True),
        ("", False),                # Empty
        ("@example.com", False),    # No local part
        ("test@", False),           # No domain
        ("test", False),            # No @ symbol
        ("test@example", False),    # No TLD
    ])
    def test_bva015_email_validation_boundaries(self, email_gateway, email, is_valid):
        """
        Test ID: BVA-015
        Priority: P2 - High
        Tests email format validation boundaries
        """
        result = email_gateway.send(email, "Test message")
        assert result.success == is_valid
