"""
Integration Tests for DAS Alert System
Test ID Format: IT-XXX (Integration Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify end-to-end flows across multiple components.
Reference: IEEE 829 Test Case Specification
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alerts.alert_manager import AlertManager, Alert, DisasterType, SeverityLevel
from src.api.messaging import SMSGateway, EmailGateway, NotificationService, GatewayStatus
from src.db.storage import DatabaseManager, EmergencyContact, AlertRecord
from src.core.config import Config


@pytest.mark.integration
class TestEndToEndAlertFlow:
    """
    Test Suite: End-to-End Alert Flow
    Validates complete flow from sensor data to notification delivery.
    """
    
    # =========================================================================
    # IT-001: Complete Alert Flow - Sensor to SMS
    # Priority: P1 (Critical)
    # Pre-conditions: All components initialized and connected
    # =========================================================================
    def test_it001_complete_alert_flow_sensor_to_sms(self, default_config):
        """
        Test ID: IT-001
        Priority: P1 - Critical
        Pre-conditions: AlertManager, NotificationService, and DatabaseManager initialized
        
        Steps:
        1. Initialize all components
        2. Register SMS notification callback
        3. Process earthquake sensor data (magnitude 7.5)
        4. Verify alert is created
        5. Verify SMS notification is triggered
        6. Store alert record in database
        
        Expected Result: 
        - Alert created with CRITICAL severity
        - SMS sent successfully
        - Alert stored in database
        """
        # Step 1: Initialize components
        alert_manager = AlertManager(config=default_config)
        notification_service = NotificationService(config=default_config)
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        # Step 2: Register callback
        sms_results = []
        def sms_callback(alert: Alert) -> bool:
            result = notification_service.sms_gateway.send(
                recipient="+1234567890",
                message=alert.message,
                priority=alert.severity.value
            )
            sms_results.append(result)
            return result.success
        
        alert_manager.register_notification_callback(sms_callback)
        
        # Step 3: Process sensor data
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.EARTHQUAKE,
            sensor_value=7.5,
            location="Los Angeles, USA",
            metadata={"sensor_id": "SENSOR-001", "source": "USGS"}
        )
        
        # Step 4: Verify alert
        assert alert is not None
        assert alert.severity == SeverityLevel.CRITICAL
        assert alert.disaster_type == DisasterType.EARTHQUAKE
        
        # Step 5: Verify SMS sent
        assert len(sms_results) == 1
        assert sms_results[0].success is True
        assert sms_results[0].status == GatewayStatus.SUCCESS
        
        # Step 6: Store in database
        record = AlertRecord(
            record_id=str(uuid4()),
            alert_id=alert.alert_id,
            disaster_type=alert.disaster_type.value,
            severity=alert.severity.name,
            location=alert.location,
            sensor_value=alert.sensor_value,
            timestamp=alert.timestamp,
            notifications_sent=1,
            notifications_failed=0,
        )
        stored = db_manager.store_alert(record)
        assert stored is True
        
        # Verify retrieval
        retrieved = db_manager.get_alert(record.record_id)
        assert retrieved is not None
        assert retrieved.alert_id == alert.alert_id
        
        db_manager.disconnect()
    
    # =========================================================================
    # IT-002: Multi-Channel Notification
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it002_multi_channel_notification(self, default_config, sample_contacts):
        """
        Test ID: IT-002
        Priority: P1 - Critical
        Pre-conditions: Multiple contacts in database
        
        Steps:
        1. Add emergency contacts to database
        2. Trigger tsunami alert
        3. Send notifications via both SMS and Email
        4. Verify all channels received notification
        
        Expected Result: All contacts notified via all channels
        """
        # Step 1: Setup database with contacts
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        for contact in sample_contacts:
            db_manager.add_contact(contact)
        
        # Step 2: Create notification service
        notification_service = NotificationService(config=default_config)
        
        # Step 3: Trigger alert
        alert_manager = AlertManager(config=default_config)
        alert = alert_manager.process_sensor_data(
            disaster_type=DisasterType.TSUNAMI,
            sensor_value=8.0,
            location="Pacific Coast"
        )
        
        # Step 4: Send notifications
        contacts = db_manager.get_all_contacts()
        phone_numbers = [c.phone for c in contacts]
        email_addresses = [c.email for c in contacts]
        
        results = notification_service.send_alert(
            message=alert.message,
            phone_numbers=phone_numbers,
            email_addresses=email_addresses,
            priority=alert.severity.value
        )
        
        # Verify
        assert results["overall_success"] is True
        assert len(results["sms_results"]) == len(phone_numbers)
        assert len(results["email_results"]) == len(email_addresses)
        assert all(r["success"] for r in results["sms_results"])
        assert all(r["success"] for r in results["email_results"])
        
        db_manager.disconnect()
    
    # =========================================================================
    # IT-003: Database to Alert Manager Link
    # Priority: P2 (High)
    # =========================================================================
    def test_it003_database_alert_manager_link(self, default_config):
        """
        Test ID: IT-003
        Priority: P2 - High
        
        Steps:
        1. Generate multiple alerts through AlertManager
        2. Store each alert in database
        3. Query alerts by location
        4. Verify consistency
        """
        # Setup
        alert_manager = AlertManager(config=default_config)
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        # Generate alerts
        locations = ["Tokyo, Japan", "Tokyo, Japan", "Mumbai, India"]
        disaster_types = [DisasterType.EARTHQUAKE, DisasterType.TSUNAMI, DisasterType.FLOOD]
        values = [6.5, 4.0, 5.0]
        
        created_alerts = []
        for loc, dtype, val in zip(locations, disaster_types, values):
            alert = alert_manager.process_sensor_data(dtype, val, loc)
            if alert:
                record = AlertRecord(
                    record_id=str(uuid4()),
                    alert_id=alert.alert_id,
                    disaster_type=alert.disaster_type.value,
                    severity=alert.severity.name,
                    location=alert.location,
                    sensor_value=alert.sensor_value,
                    timestamp=alert.timestamp,
                    notifications_sent=0,
                    notifications_failed=0,
                )
                db_manager.store_alert(record)
                created_alerts.append(alert)
        
        # Query by location
        tokyo_alerts = db_manager.get_alerts_by_location("Tokyo")
        
        # Verify
        assert len(tokyo_alerts) == 2
        for alert in tokyo_alerts:
            assert "Tokyo" in alert.location
        
        db_manager.disconnect()
    
    # =========================================================================
    # IT-004: Alert Acknowledgment Flow
    # Priority: P2 (High)
    # =========================================================================
    def test_it004_alert_acknowledgment_flow(self, default_config):
        """
        Test ID: IT-004
        Priority: P2 - High
        
        Steps:
        1. Generate alert
        2. Store in database
        3. Acknowledge via database
        4. Verify acknowledgment persists
        """
        # Setup
        alert_manager = AlertManager(config=default_config)
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        # Generate and store alert
        alert = alert_manager.process_sensor_data(
            DisasterType.CYCLONE, 180.0, "Bay of Bengal"
        )
        
        record_id = str(uuid4())
        record = AlertRecord(
            record_id=record_id,
            alert_id=alert.alert_id,
            disaster_type=alert.disaster_type.value,
            severity=alert.severity.name,
            location=alert.location,
            sensor_value=alert.sensor_value,
            timestamp=alert.timestamp,
            notifications_sent=1,
            notifications_failed=0,
        )
        db_manager.store_alert(record)
        
        # Verify unacknowledged
        unack = db_manager.get_unacknowledged_alerts()
        assert len(unack) == 1
        
        # Acknowledge
        db_manager.acknowledge_alert(record_id, "operator@das.gov")
        
        # Verify acknowledged
        unack_after = db_manager.get_unacknowledged_alerts()
        assert len(unack_after) == 0
        
        ack_record = db_manager.get_alert(record_id)
        assert ack_record.acknowledged is True
        assert ack_record.acknowledged_by == "operator@das.gov"
        
        db_manager.disconnect()


@pytest.mark.integration
class TestContactManagementIntegration:
    """
    Test Suite: Contact Management Integration
    Validates database operations with notification service.
    """
    
    # =========================================================================
    # IT-005: Region-Based Alert Distribution
    # Priority: P1 (Critical)
    # =========================================================================
    def test_it005_region_based_alert_distribution(self, default_config, sample_contacts):
        """
        Test ID: IT-005
        Priority: P1 - Critical
        
        Scenario: Alert should only notify contacts in affected region
        """
        # Setup
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        notification_service = NotificationService(config=default_config)
        
        # Add contacts (2 North, 1 South)
        for contact in sample_contacts:
            db_manager.add_contact(contact)
        
        # Get only North region contacts
        north_contacts = db_manager.get_contacts_by_region("North")
        
        # Verify correct filtering
        assert len(north_contacts) == 2
        
        # Send to only affected region
        results = notification_service.send_alert(
            message="Earthquake alert for North region",
            phone_numbers=[c.phone for c in north_contacts],
            priority=4
        )
        
        # Verify only 2 SMSs sent
        assert len(results["sms_results"]) == 2
        
        db_manager.disconnect()
    
    # =========================================================================
    # IT-006: Contact Priority Ordering
    # Priority: P2 (High)
    # =========================================================================
    def test_it006_contact_priority_ordering(self, default_config, sample_contacts):
        """
        Test ID: IT-006
        Priority: P2 - High
        
        Verify contacts are returned in priority order
        """
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        for contact in sample_contacts:
            db_manager.add_contact(contact)
        
        all_contacts = db_manager.get_all_contacts()
        
        # Should be sorted by priority (1 before 2)
        assert all_contacts[0].priority_level <= all_contacts[-1].priority_level
        
        db_manager.disconnect()
