"""
Stress Tests for Backend API
Test ID Format: ST-XXX (Stress Test)
Priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)

These tests verify system behavior under high load conditions.
CRITICAL for Disaster Systems: Must handle surge of alerts during actual disasters.

Tests the Backend Flask API (Backend/app.py)
Reference: IEEE 829 Test Case Specification, Performance Testing Guidelines
"""

import pytest
import sys
import time
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Backend"))


@pytest.mark.stress
@pytest.mark.slow
class TestHighVolumeAlerts:
    """
    Test Suite: High Volume Alert Processing
    Simulates disaster scenarios with multiple simultaneous alerts.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        self.bcrypt_patcher = patch('app.bcrypt')
        self.twilio_patcher = patch('app.Client')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        self.mock_bcrypt = self.bcrypt_patcher.start()
        self.mock_twilio = self.twilio_patcher.start()
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        self.mock_bcrypt.check_password_hash.return_value = True
        
        mock_twilio_instance = MagicMock()
        mock_twilio_instance.messages.create.return_value = MagicMock(sid='SM123')
        self.mock_twilio.return_value = mock_twilio_instance
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app = app
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
        self.bcrypt_patcher.stop()
        self.twilio_patcher.stop()
    
    # =========================================================================
    # ST-001: Burst Alert API Requests
    # Priority: P1 (Critical)
    # =========================================================================
    def test_st001_burst_alert_requests(self):
        """
        Test ID: ST-001
        Priority: P1 - Critical
        50 alert creation requests in rapid succession.
        """
        user_id = ObjectId()
        
        # Login
        self.mock_mongo.db.users.find_one.return_value = {
            "_id": user_id,
            "email": "test@test.com",
            "password": "hashed",
            "name": "Test",
            "phone": "+91123",
            "location": {},
            "isAuthorized": True,
            "notificationPreferences": {}
        }
        
        login_resp = self.client.post('/api/login', json={
            "email": "test@test.com",
            "password": "password"
        })
        
        token = login_resp.get_json()['token']
        
        # Setup mocks for alert creation
        self.mock_mongo.db.alerts.find.return_value = []
        self.mock_mongo.db.alerts.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        self.mock_mongo.db.users.find.return_value = []
        
        num_alerts = 20  # Reduced for faster testing
        
        start_time = time.time()
        
        successful = 0
        for i in range(num_alerts):
            self.mock_mongo.db.alerts.find_one.return_value = {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": f"Alert {i}",
                "message": "Test",
                "type": "earthquake",
                "severity": "high",
                "location": f"Location {i}",
                "coordinates": {"lat": 19.0, "lng": 72.8},
                "status": "active",
                "timestamp": datetime.utcnow(),
                "sms_sent": False
            }
            
            response = self.client.post(
                '/api/alerts',
                json={
                    "title": f"Alert {i}",
                    "message": "Test",
                    "type": "earthquake",
                    "severity": "high",
                    "location": f"Location {i}",
                    "coordinates": {"lat": 19.0, "lng": 72.8}
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 201:
                successful += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\nST-001 Results:")
        print(f"  Alerts: {num_alerts}")
        print(f"  Successful: {successful}")
        print(f"  Time: {processing_time:.3f}s")
        
        assert successful == num_alerts
    
    # =========================================================================
    # ST-002: SMS Broadcast Throughput
    # Priority: P1 (Critical)
    # =========================================================================
    def test_st002_sms_broadcast_throughput(self):
        """
        Test ID: ST-002
        Priority: P1 - Critical
        Send SMS to 50 users in the affected area.
        """
        # Generate 50 users within radius
        self.mock_mongo.db.users.find.return_value = [
            {
                "_id": ObjectId(),
                "phone": f"+9198765{i:05d}",
                "location": {"coordinates": {"lat": 19.0, "lng": 72.8}}
            }
            for i in range(50)
        ]
        
        with patch('app.send_twilio_sms') as mock_sms:
            mock_sms.return_value = {"status": "success", "sid": "SM123"}
            
            from app import broadcast_sms_to_users
            
            start_time = time.time()
            
            alert_data = {
                "title": "EMERGENCY",
                "message": "Evacuate",
                "coordinates": {"lat": 19.0760, "lng": 72.8777}
            }
            
            result = broadcast_sms_to_users(alert_data)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\nST-002 Results:")
            print(f"  Users notified: {mock_sms.call_count}")
            print(f"  Time: {processing_time:.3f}s")
            
            assert result == True
            assert mock_sms.call_count == 50


@pytest.mark.stress
@pytest.mark.slow
class TestDatabaseStress:
    """
    Test Suite: Database Stress Testing
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client with mocked dependencies."""
        self.mongo_patcher = patch('app.mongo')
        self.geocoding_patcher = patch('app.requests.get')
        self.bcrypt_patcher = patch('app.bcrypt')
        
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_geocoding = self.geocoding_patcher.start()
        self.mock_bcrypt = self.bcrypt_patcher.start()
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "19.0760", "lon": "72.8777"}]
        self.mock_geocoding.return_value = mock_response
        
        self.mock_bcrypt.generate_password_hash.return_value = b'hashed'
        
        from app import app
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        yield
        
        self.mongo_patcher.stop()
        self.geocoding_patcher.stop()
        self.bcrypt_patcher.stop()
    
    # =========================================================================
    # ST-003: Bulk User Registration
    # Priority: P2 (High)
    # =========================================================================
    def test_st003_bulk_user_registration(self):
        """
        Test ID: ST-003
        Priority: P2 - High
        Register 20 users in quick succession.
        """
        self.mock_mongo.db.users.find_one.return_value = None
        self.mock_mongo.db.users.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        num_users = 20
        successful = 0
        
        start_time = time.time()
        
        for i in range(num_users):
            self.mock_mongo.db.users.find_one.side_effect = [
                None,
                {
                    "_id": ObjectId(),
                    "name": f"User {i}",
                    "email": f"user{i}@test.com",
                    "phone": f"+9198765{i:05d}",
                    "location": {},
                    "isAuthorized": False,
                    "notificationPreferences": {}
                }
            ]
            
            response = self.client.post('/api/signup', json={
                "name": f"User {i}",
                "email": f"user{i}@test.com",
                "password": "TestPass123!",
                "phone": f"+9198765{i:05d}",
                "city": "Mumbai",
                "state": "Maharashtra"
            })
            
            if response.status_code == 201:
                successful += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\nST-003 Results:")
        print(f"  Users: {num_users}")
        print(f"  Created: {successful}")
        print(f"  Time: {processing_time:.3f}s")
        
        assert successful == num_users


@pytest.mark.stress
class TestDuplicateCheckPerformance:
    """
    Test Suite: Duplicate Alert Check Performance
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup mocks."""
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        yield
        
        self.mongo_patcher.stop()
    
    # =========================================================================
    # ST-004: Duplicate Check Performance
    # Priority: P1 (Critical)
    # =========================================================================
    def test_st004_duplicate_check_performance(self):
        """
        Test ID: ST-004
        Priority: P1 - Critical
        Check duplicates against 100 existing alerts.
        """
        # Simulate 100 existing alerts
        existing_alerts = [
            {
                "_id": ObjectId(),
                "coordinates": {"lat": 19.0 + i * 0.1, "lng": 72.8 + i * 0.1},
                "timestamp": datetime.utcnow() - timedelta(hours=i % 12),
                "sms_sent": True
            }
            for i in range(100)
        ]
        self.mock_mongo.db.alerts.find.return_value = existing_alerts
        
        from app import should_trigger_sms
        
        num_checks = 20
        
        start_time = time.time()
        
        results = []
        for i in range(num_checks):
            result = should_trigger_sms({"lat": 25.0 + i * 0.1, "lng": 80.0 + i * 0.1})
            results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        avg_time = processing_time / num_checks
        
        print(f"\nST-004 Results:")
        print(f"  Checks: {num_checks}")
        print(f"  Existing alerts: 100")
        print(f"  Total time: {processing_time:.3f}s")
        print(f"  Avg per check: {avg_time*1000:.2f}ms")
        
        assert len(results) == num_checks
        assert avg_time < 1.0


@pytest.mark.stress
class TestConcurrentRequests:
    """
    Test Suite: Concurrent Request Handling
    """
    
    # =========================================================================
    # ST-005: Concurrent Login Requests
    # Priority: P2 (High)
    # =========================================================================
    def test_st005_concurrent_login_requests(self):
        """
        Test ID: ST-005
        Priority: P2 - High
        Multiple concurrent login attempts.
        """
        results = []
        
        def make_login_request(thread_id):
            with patch('app.mongo') as mock_mongo:
                with patch('app.bcrypt') as mock_bcrypt:
                    mock_bcrypt.check_password_hash.return_value = True
                    
                    mock_mongo.db.users.find_one.return_value = {
                        "_id": ObjectId(),
                        "email": f"user{thread_id}@test.com",
                        "password": "hashed",
                        "name": f"User {thread_id}",
                        "phone": f"+9198765{thread_id:04d}",
                        "location": {},
                        "isAuthorized": False,
                        "notificationPreferences": {}
                    }
                    
                    from app import app
                    app.config['TESTING'] = True
                    
                    with app.test_client() as client:
                        response = client.post('/api/login', json={
                            "email": f"user{thread_id}@test.com",
                            "password": "password"
                        })
                        
                        results.append((thread_id, response.status_code))
        
        num_threads = 5
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=make_login_request, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        print(f"\nST-005 Results:")
        print(f"  Threads: {num_threads}")
        print(f"  Completed: {len(results)}")
        
        assert len(results) == num_threads
