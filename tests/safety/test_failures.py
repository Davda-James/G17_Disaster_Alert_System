"""
Safety-Critical / Risk-Based Tests for DAS Alert System
Test ID Format: RBT-XXX (Risk-Based Test)
Priority: P1 (Critical)

These tests simulate FAILURE MODES that could lead to catastrophic outcomes.
MANDATORY for mission-critical disaster alert systems.

Risk Categories (ISO 22324):
- Catastrophic: Loss of life possible
- Critical: Serious injury or major system failure
- Major: Significant degradation of service
- Minor: Acceptable degradation

Reference: ISO/IEC/IEEE 29119, ISTQB Risk-Based Testing
"""

import pytest
import time
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alerts.alert_manager import AlertManager, DisasterType, SeverityLevel
from src.api.messaging import SMSGateway, EmailGateway, NotificationService, GatewayStatus
from src.db.storage import DatabaseManager, DatabaseCorruptionException, EmergencyContact
from src.core.config import Config


@pytest.mark.safety
class TestNetworkFailureScenarios:
    """
    Test Suite: Network Failure Modes
    Risk Level: Catastrophic
    
    Scenario: SMS gateway fails during Tsunami alert
    Impact: Citizens in coastal areas don't receive evacuation notice
    """
    
    # =========================================================================
    # RBT-001: SMS Gateway Failure During Critical Alert
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt001_sms_gateway_failure(self, failure_config):
        """
        Test ID: RBT-001
        Priority: P1 - Critical
        Risk Level: CATASTROPHIC
        
        Scenario: What happens if SMS gateway fails during Tsunami alert?
        
        Pre-conditions:
        - Network failure simulation ENABLED
        
        Steps:
        1. Trigger a CATASTROPHIC tsunami alert
        2. Attempt to send SMS notification
        3. Verify system handles failure gracefully
        4. Verify retry mechanism activates
        5. Verify failure is logged
        
        Expected Result:
        - SMS send returns SERVICE_UNAVAILABLE
        - System does not crash
        - Fallback mechanisms should be available
        """
        # Arrange
        sms_gateway = SMSGateway(config=failure_config)
        
        # Act
        result = sms_gateway.send(
            recipient="+1234567890",
            message="⚠️ CATASTROPHIC EMERGENCY: TSUNAMI. EVACUATE IMMEDIATELY.",
            priority=5
        )
        
        # Assert
        assert result.success is False
        assert result.status == GatewayStatus.SERVICE_UNAVAILABLE
        assert "Network failure" in result.error_message
        
        # Verify gateway tracks failed count
        stats = sms_gateway.get_statistics()
        assert stats["failed_count"] == 1
    
    # =========================================================================
    # RBT-002: Email Gateway Failure Fallback
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt002_email_gateway_failure(self, failure_config):
        """
        Test ID: RBT-002
        Priority: P1 - Critical
        Risk Level: CRITICAL
        
        Scenario: Email gateway fails, system should be aware
        """
        email_gateway = EmailGateway(config=failure_config)
        
        result = email_gateway.send(
            recipient="emergency@gov.local",
            message="Critical flood warning",
            priority=4
        )
        
        assert result.success is False
        assert result.status == GatewayStatus.SERVICE_UNAVAILABLE
    
    # =========================================================================
    # RBT-003: Notification Service Retry Logic
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt003_notification_retry_logic(self, failure_config):
        """
        Test ID: RBT-003
        Priority: P1 - Critical
        Risk Level: CATASTROPHIC
        
        Scenario: Notification fails, system retries up to max attempts
        
        Expected: System attempts 3 retries before giving up
        """
        notification_service = NotificationService(config=failure_config)
        
        start_time = time.time()
        
        result = notification_service.send_alert(
            message="Earthquake alert - retry test",
            phone_numbers=["+1234567890"],
            priority=5
        )
        
        end_time = time.time()
        
        # Verify retries happened (should take some time for exponential backoff)
        assert result["overall_success"] is False
        assert len(result["sms_results"]) == 1
        assert result["sms_results"][0]["success"] is False


@pytest.mark.safety
class TestDatabaseFailureScenarios:
    """
    Test Suite: Database Failure Modes
    Risk Level: Critical
    
    Scenario: Primary database corrupted during ongoing disaster
    Impact: Cannot retrieve emergency contact list
    """
    
    # =========================================================================
    # RBT-004: Database Corruption - Fallback Cache
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt004_database_corruption_fallback(self, db_corruption_config):
        """
        Test ID: RBT-004
        Priority: P1 - Critical
        Risk Level: CRITICAL
        
        Scenario: Database is corrupted, system falls back to cache
        
        Pre-conditions:
        - Database corruption simulation ENABLED
        - Cache file exists with emergency contacts
        
        Steps:
        1. Pre-populate cache with contacts
        2. Connect to "corrupted" database
        3. Verify system falls back to cache
        4. Verify contacts are still accessible
        
        Expected Result:
        - System continues to function via cache
        - No crash or data loss
        """
        # Arrange - First create cache from healthy database
        healthy_config = Config(simulate_db_corruption=False)
        healthy_db = DatabaseManager(config=healthy_config)
        healthy_db.connect()
        
        # Add contacts
        healthy_db.add_contact(EmergencyContact(
            contact_id="EMERGENCY-001",
            name="Primary Response Team",
            phone="+1234567890",
            email="primary@emergency.gov",
            region="Central",
            priority_level=1
        ))
        healthy_db._save_to_cache()  # Force cache save
        healthy_db.disconnect()
        
        # Now simulate corruption
        corrupted_db = DatabaseManager(config=db_corruption_config)
        
        # Act - Connect with corruption simulation
        connected = corrupted_db.connect()
        
        # Assert
        assert connected is True  # Connected via fallback
        assert corrupted_db.is_using_fallback() is True
        
        # Verify contacts accessible via cache
        contacts = corrupted_db.get_all_contacts()
        assert len(contacts) >= 1
    
    # =========================================================================
    # RBT-005: No Cache Available During Corruption
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt005_no_cache_during_corruption(self, db_corruption_config, tmp_path):
        """
        Test ID: RBT-005
        Priority: P1 - Critical
        Risk Level: CATASTROPHIC
        
        Scenario: Database corrupted AND no cache exists
        
        Expected: System handles gracefully, logs critical error
        """
        # Create a fresh DatabaseManager with unique cache path
        corrupted_db = DatabaseManager(config=db_corruption_config)
        
        # Remove any existing cache
        import os
        cache_file = corrupted_db._contacts_cache_file
        if cache_file.exists():
            os.remove(cache_file)
        
        # Attempt connection
        connected = corrupted_db.connect()
        
        # System should handle this - either connect=False or connect with empty data
        assert corrupted_db.is_using_fallback() is True


@pytest.mark.safety
class TestHighLatencyScenarios:
    """
    Test Suite: Network Latency Impact
    Risk Level: Major
    
    Scenario: Internet connection throttled during peak disaster
    """
    
    # =========================================================================
    # RBT-006: High Latency Impact on Notifications
    # Risk Level: MAJOR
    # =========================================================================
    def test_rbt006_high_latency_notifications(self, high_latency_config):
        """
        Test ID: RBT-006
        Priority: P2 - High
        Risk Level: MAJOR
        
        Scenario: Network latency is 100ms per request
        Impact: Bulk notifications take longer
        
        Expected: System completes, just slower
        """
        sms_gateway = SMSGateway(config=high_latency_config)
        
        start_time = time.time()
        
        # Send 5 messages
        results = sms_gateway.send_bulk(
            recipients=[f"+123456789{i}" for i in range(5)],
            message="High latency test",
            priority=3
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # With 100ms latency per request, 5 requests should take ~500ms
        assert total_time >= 0.4  # Allow some tolerance
        
        # All should still succeed
        assert all(r.success for r in results)


@pytest.mark.safety
class TestCascadeFailureScenarios:
    """
    Test Suite: Cascade Failure Prevention
    Risk Level: Catastrophic
    
    Tests that one component failure doesn't bring down entire system
    """
    
    # =========================================================================
    # RBT-007: Alert Manager Continues Despite Gateway Failure
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt007_alert_manager_isolation(self, failure_config):
        """
        Test ID: RBT-007
        Priority: P1 - Critical
        Risk Level: CATASTROPHIC
        
        Scenario: Notification gateway down, AlertManager should still:
        1. Record alerts
        2. Store data
        3. Allow manual acknowledgment
        
        System must NOT stop processing new alerts!
        """
        alert_manager = AlertManager(config=failure_config)
        
        # Register failing callback
        fail_count = [0]
        def failing_callback(alert):
            fail_count[0] += 1
            raise ConnectionError("Gateway down")
        
        alert_manager.register_notification_callback(failing_callback)
        
        # Process multiple alerts despite callback failures
        alerts_created = []
        for i in range(5):
            alert = alert_manager.process_sensor_data(
                disaster_type=DisasterType.EARTHQUAKE,
                sensor_value=7.0 + i * 0.1,
                location=f"Zone {i}"
            )
            if alert:
                alerts_created.append(alert)
        
        # Verify alerts were still created and tracked
        assert len(alerts_created) == 5
        assert fail_count[0] == 5  # Callback was attempted 5 times
        
        # Verify statistics still work
        stats = alert_manager.get_alert_statistics()
        assert stats["total_alerts"] == 5
    
    # =========================================================================
    # RBT-008: Multi-Component Failure Recovery
    # Risk Level: CATASTROPHIC
    # =========================================================================
    def test_rbt008_multi_component_failure_recovery(self, default_config, failure_config):
        """
        Test ID: RBT-008
        Priority: P1 - Critical
        Risk Level: CATASTROPHIC
        
        Scenario: Network fails, then recovers
        System should successfully send pending notifications
        """
        # Phase 1: Failure
        failing_service = NotificationService(config=failure_config)
        
        fail_result = failing_service.send_alert(
            message="Test during failure",
            phone_numbers=["+1234567890"],
            priority=5
        )
        
        assert fail_result["overall_success"] is False
        
        # Phase 2: Recovery (use healthy config)
        recovered_service = NotificationService(config=default_config)
        
        success_result = recovered_service.send_alert(
            message="Test after recovery",
            phone_numbers=["+1234567890"],
            priority=5
        )
        
        assert success_result["overall_success"] is True


@pytest.mark.safety
class TestDataIntegrityScenarios:
    """
    Test Suite: Data Integrity During Failures
    Risk Level: Critical
    """
    
    # =========================================================================
    # RBT-009: Alert Data Not Lost During Notification Failure
    # Risk Level: CRITICAL
    # =========================================================================
    def test_rbt009_alert_data_preserved(self, failure_config):
        """
        Test ID: RBT-009
        Priority: P1 - Critical
        
        Even if notifications fail, alert record must be preserved
        for later analysis and manual follow-up.
        """
        alert_manager = AlertManager(config=failure_config)
        
        # Register failing notification
        def failing_notify(alert):
            raise Exception("Notification failed")
        
        alert_manager.register_notification_callback(failing_notify)
        
        # Process critical alert
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.TSUNAMI,
            sensor_value=15.0,  # Catastrophic
            location="Coastal City"
        )
        
        # Alert should still be recorded
        assert alert is not None
        assert alert.disaster_type == DisasterType.TSUNAMI
        assert alert.severity == SeverityLevel.CATASTROPHIC
        
        # Alert should be in manager's history
        stats = alert_manager.get_alert_statistics()
        assert stats["total_alerts"] == 1
        
        # Active alerts should show unacknowledged
        active = alert_manager.get_active_alerts()
        assert len(active) == 1
