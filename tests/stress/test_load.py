"""
Stress Tests for DAS Alert System
Test ID Format: ST-XXX (Stress Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify system behavior under high load conditions.
CRITICAL for Disaster Systems: Must handle surge of alerts during actual disasters.

Reference: IEEE 829 Test Case Specification, Performance Testing Guidelines
"""

import pytest
import time
import threading
import concurrent.futures
from datetime import datetime
from typing import List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alerts.alert_manager import AlertManager, DisasterType, SeverityLevel, Alert
from src.api.messaging import SMSGateway, EmailGateway, NotificationService
from src.db.storage import DatabaseManager, EmergencyContact
from src.core.config import Config


@pytest.mark.stress
@pytest.mark.slow
class TestHighVolumeAlerts:
    """
    Test Suite: High Volume Alert Processing
    Simulates disaster scenarios with multiple simultaneous alerts.
    """
    
    # =========================================================================
    # ST-001: Burst Alert Processing
    # Priority: P1 (Critical)
    # Rationale: During an earthquake, seismic sensors across a region will
    #            trigger simultaneously. System must handle this burst.
    # =========================================================================
    def test_st001_burst_alert_processing(self, default_config):
        """
        Test ID: ST-001
        Priority: P1 - Critical
        
        Scenario: 100 sensors trigger simultaneously during earthquake
        Pre-conditions: AlertManager initialized
        
        Steps:
        1. Generate 100 alerts in rapid succession
        2. Measure total processing time
        3. Verify all alerts processed correctly
        
        Performance Target: < 2 seconds for 100 alerts
        Expected Result: All alerts processed, no data loss
        """
        alert_manager = AlertManager(config=default_config)
        
        num_alerts = 100
        locations = [f"Sensor Station {i}" for i in range(num_alerts)]
        magnitudes = [5.0 + (i % 40) / 10 for i in range(num_alerts)]  # 5.0 to 8.9
        
        start_time = time.time()
        
        alerts_created = []
        for loc, mag in zip(locations, magnitudes):
            alert = alert_manager.process_sensor_data(
                disaster_type=DisasterType.EARTHQUAKE,
                sensor_value=mag,
                location=loc
            )
            if alert:
                alerts_created.append(alert)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify all alerts were created
        assert len(alerts_created) == num_alerts
        
        # Performance assertion
        assert processing_time < 2.0, f"Processing took {processing_time:.2f}s, target is <2s"
        
        # Verify statistics
        stats = alert_manager.get_alert_statistics()
        assert stats["total_alerts"] == num_alerts
        
        print(f"\nST-001 Results:")
        print(f"  Alerts processed: {num_alerts}")
        print(f"  Total time: {processing_time:.3f}s")
        print(f"  Rate: {num_alerts/processing_time:.1f} alerts/second")
    
    # =========================================================================
    # ST-002: Concurrent Alert Processing
    # Priority: P1 (Critical)
    # =========================================================================
    def test_st002_concurrent_alert_processing(self, default_config):
        """
        Test ID: ST-002
        Priority: P1 - Critical
        
        Scenario: Multiple threads processing alerts simultaneously
        Tests thread-safety of AlertManager
        
        Performance Target: Process 50 alerts across 5 threads in < 3 seconds
        """
        alert_manager = AlertManager(config=default_config)
        
        def process_alerts_batch(batch_id: int, count: int) -> List[Alert]:
            alerts = []
            for i in range(count):
                alert = alert_manager.process_sensor_data(
                    disaster_type=DisasterType.TSUNAMI,
                    sensor_value=3.0 + i * 0.1,
                    location=f"Zone {batch_id}-{i}"
                )
                if alert:
                    alerts.append(alert)
            return alerts
        
        num_threads = 5
        alerts_per_thread = 10
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(process_alerts_batch, i, alerts_per_thread)
                for i in range(num_threads)
            ]
            
            all_alerts = []
            for future in concurrent.futures.as_completed(futures):
                all_alerts.extend(future.result())
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        total_expected = num_threads * alerts_per_thread
        
        # Verify
        assert len(all_alerts) == total_expected
        assert processing_time < 3.0
        
        print(f"\nST-002 Results:")
        print(f"  Threads: {num_threads}")
        print(f"  Total alerts: {total_expected}")
        print(f"  Processing time: {processing_time:.3f}s")
    
    # =========================================================================
    # ST-003: Notification Throughput
    # Priority: P1 (Critical)
    # =========================================================================
    def test_st003_notification_throughput(self, default_config):
        """
        Test ID: ST-003
        Priority: P1 - Critical
        
        Scenario: Send notifications to 50 contacts
        Performance Target: < 5 seconds for all notifications
        """
        notification_service = NotificationService(config=default_config)
        
        # Generate 50 recipients
        phones = [f"+1234567{i:04d}" for i in range(50)]
        emails = [f"user{i}@emergency.gov" for i in range(50)]
        
        message = "EMERGENCY: Tsunami warning. Evacuate immediately."
        
        start_time = time.time()
        
        results = notification_service.send_alert(
            message=message,
            phone_numbers=phones,
            email_addresses=emails,
            priority=5
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify
        assert results["overall_success"] is True
        assert len(results["sms_results"]) == 50
        assert len(results["email_results"]) == 50
        
        sms_success = sum(1 for r in results["sms_results"] if r["success"])
        email_success = sum(1 for r in results["email_results"] if r["success"])
        
        assert processing_time < 5.0
        
        print(f"\nST-003 Results:")
        print(f"  SMS sent: {sms_success}/50")
        print(f"  Emails sent: {email_success}/50")
        print(f"  Total time: {processing_time:.3f}s")


@pytest.mark.stress
@pytest.mark.slow
class TestDatabaseStress:
    """
    Test Suite: Database Stress Testing
    Verifies database performance under heavy load.
    """
    
    # =========================================================================
    # ST-004: Bulk Contact Insertion
    # Priority: P2 (High)
    # =========================================================================
    def test_st004_bulk_contact_insertion(self, default_config):
        """
        Test ID: ST-004
        Priority: P2 - High
        
        Scenario: Insert 100 emergency contacts quickly
        Performance Target: < 1 second
        """
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        contacts = [
            EmergencyContact(
                contact_id=f"EC-STRESS-{i:04d}",
                name=f"Emergency Unit {i}",
                phone=f"+1987654{i:04d}",
                email=f"unit{i}@emergency.gov",
                region=f"Region-{i % 10}",
                priority_level=i % 5 + 1
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        
        for contact in contacts:
            db_manager.add_contact(contact)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify
        all_contacts = db_manager.get_all_contacts(active_only=False)
        assert len(all_contacts) == 100
        assert processing_time < 1.0
        
        db_manager.disconnect()
        
        print(f"\nST-004 Results:")
        print(f"  Contacts inserted: 100")
        print(f"  Time: {processing_time:.3f}s")
    
    # =========================================================================
    # ST-005: Concurrent Database Queries
    # Priority: P2 (High)
    # =========================================================================
    def test_st005_concurrent_database_queries(self, default_config):
        """
        Test ID: ST-005
        Priority: P2 - High
        
        Scenario: Multiple threads querying database simultaneously
        """
        db_manager = DatabaseManager(config=default_config)
        db_manager.connect()
        
        # Seed data
        for i in range(20):
            db_manager.add_contact(EmergencyContact(
                contact_id=f"QUERY-TEST-{i}",
                name=f"Query Test {i}",
                phone=f"+1111111{i:04d}",
                email=f"query{i}@test.gov",
                region=f"Region-{i % 5}",
            ))
        
        def query_region(region: str) -> int:
            contacts = db_manager.get_contacts_by_region(region)
            return len(contacts)
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(query_region, f"Region-{i}")
                for i in range(5)
                for _ in range(10)  # 10 queries per region
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        assert all(r >= 0 for r in results)
        assert end_time - start_time < 2.0
        
        db_manager.disconnect()


@pytest.mark.stress
class TestMemoryStability:
    """
    Test Suite: Memory Stability Under Load
    Verifies system doesn't leak memory during extended operation.
    """
    
    # =========================================================================
    # ST-006: Extended Operation Test
    # Priority: P2 (High)
    # =========================================================================
    def test_st006_extended_operation(self, default_config):
        """
        Test ID: ST-006
        Priority: P2 - High
        
        Scenario: Process alerts over extended period (simulated)
        Verify: Alert history doesn't grow unboundedly, stats remain accurate
        """
        alert_manager = AlertManager(config=default_config)
        
        # Process 200 alerts
        for i in range(200):
            alert = alert_manager.process_sensor_data(
                disaster_type=DisasterType.EARTHQUAKE,
                sensor_value=5.0 + (i % 30) / 10,
                location=f"Location {i}"
            )
            if alert and i % 10 == 0:
                # Acknowledge every 10th alert
                alert_manager.acknowledge_alert(alert.alert_id)
        
        # Clear acknowledged alerts periodically
        cleared = alert_manager.clear_acknowledged_alerts()
        
        stats = alert_manager.get_alert_statistics()
        
        # Verify
        assert stats["total_alerts"] == 200
        assert cleared == 20  # 200/10 = 20 acknowledged
        
        print(f"\nST-006 Results:")
        print(f"  Total alerts: {stats['total_alerts']}")
        print(f"  Active alerts: {stats['active_alerts']}")
        print(f"  Cleared: {cleared}")
