# DisasterWatch Test Procedure Document

## Document Information

| Field | Value |
|-------|-------|
| **Document Title** | DisasterWatch System Test Procedures |
| **Version** | 1.0 |
| **Date** | 2026-01-25 |
| **Project** | Disaster Alert System (DAS) |
| **Standard** | IEEE 829 Test Documentation |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Environment Setup](#2-test-environment-setup)
3. [Backend API Tests](#3-backend-api-tests)
4. [Frontend Tests](#4-frontend-tests)
5. [Running All Tests](#5-running-all-tests)
6. [Test Results Interpretation](#6-test-results-interpretation)
7. [Notification System Testing](#7-notification-system-testing)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview

### 1.1 System Under Test

The DisasterWatch application consists of:

| Component | Technology | Port |
|-----------|-----------|------|
| **Backend API** | Flask (Python) | 5000 |
| **Frontend** | React + Vite | 5173 |
| **Database** | MongoDB | 27017 |
| **SMS Gateway** | Twilio API | N/A |

### 1.2 Test Categories

| Category | Test Count | Priority | Description |
|----------|------------|----------|-------------|
| Boundary Value | 55 | P1-P2 | Input validation tests |
| Functional | 12 | P1-P2 | API endpoint tests |
| Integration | 6 | P1-P2 | End-to-end flows |
| Safety | 10 | P1 | Failure mode tests |
| Stress | 5 | P1-P2 | Load testing |
| Frontend | 15 | P2-P3 | UI component tests |

---

## 2. Test Environment Setup

### 2.1 Prerequisites

Before running tests, ensure you have installed:

```
- Python 3.9 or higher
- Node.js 18 or higher
- pip (Python package manager)
- npm (Node package manager)
```

### 2.2 Backend Test Setup

**Step 1: Navigate to project directory**
```cmd
cd d:\Sem6_course\SE\Ass1\DAS_Project
```

**Step 2: Install Backend dependencies**
```cmd
pip install -r Backend\requirements.txt
```

**Step 3: Install Test dependencies**
```cmd
pip install -r tests\backend\requirements.txt
```

**Step 4: Verify installation**
```cmd
pytest --version
```

Expected output:
```
pytest 9.0.2
```

### 2.3 Frontend Test Setup

**Step 1: Navigate to Frontend directory**
```cmd
cd d:\Sem6_course\SE\Ass1\DAS_Project\Frontend
```

**Step 2: Install dependencies**
```cmd
npm install
```

**Step 3: Verify installation**
```cmd
npm run test -- --version
```

---

## 3. Backend API Tests

### 3.1 Running All Backend Tests

**Command:**
```cmd
cd d:\Sem6_course\SE\Ass1\DAS_Project\tests\backend
pytest -v
```

**Expected Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.0.2
collected 88 items

boundary/test_limits.py::TestUserInputBoundaries::test_bva001... PASSED
functional/test_alerts.py::TestUserAuthentication::test_ft001... PASSED
...
============================= 88 passed in 5.63s ==============================
```

### 3.2 Running Specific Test Categories

#### Boundary Value Tests
```cmd
pytest boundary/test_limits.py -v
```

#### Functional Tests
```cmd
pytest functional/test_alerts.py -v
```

#### Integration Tests
```cmd
pytest integration/test_flow.py -v
```

#### Safety Tests
```cmd
pytest safety/test_failures.py -v -m safety
```

#### Stress Tests
```cmd
pytest stress/test_load.py -v -m stress
```

### 3.3 Running Tests with Coverage Report

**Command:**
```cmd
pytest -v --cov=../Backend --cov-report=html
```

**Result:** Opens `htmlcov/index.html` in browser to view coverage report.

### 3.4 Running Specific Test by ID

```cmd
# Run a specific test
pytest -v -k "test_ft001"

# Run tests matching pattern
pytest -v -k "bva001 or bva002"
```

---

## 4. Frontend Tests

### 4.1 Running All Frontend Tests

**Command:**
```cmd
cd d:\Sem6_course\SE\Ass1\DAS_Project\Frontend
npm run test
```

**Expected Output:**
```
 ✓ src/test/example.test.ts (1 test)
 ✓ src/test/utils.test.ts (15 tests)
 ✓ src/test/AuthContext.test.tsx (8 tests)

 Test Files  3 passed (3)
      Tests  24 passed (24)
   Duration  2.5s
```

### 4.2 Running Tests in Watch Mode

```cmd
npm run test:watch
```

This will re-run tests automatically when files change.

### 4.3 Running Specific Test File

```cmd
npm run test -- src/test/AuthContext.test.tsx
```

---

## 5. Running All Tests

### 5.1 Complete Test Suite Script

Create a batch file `run_all_tests.bat`:

```batch
@echo off
echo =====================================
echo DisasterWatch Complete Test Suite
echo =====================================

echo.
echo [1/2] Running Backend Tests...
echo =====================================
cd /d d:\Sem6_course\SE\Ass1\DAS_Project\tests
pytest -v --tb=short

echo.
echo [2/2] Running Frontend Tests...
echo =====================================
cd /d d:\Sem6_course\SE\Ass1\DAS_Project\Frontend
npm run test

echo.
echo =====================================
echo All Tests Complete!
echo =====================================
pause
```

### 5.2 Expected Results Summary

| Test Suite | Expected Pass | Status |
|------------|---------------|--------|
| Backend Tests | 88/88 | ✅ |
| Frontend Tests | 24/24 | ✅ |
| **Total** | **112/112** | **✅** |

---

## 6. Test Results Interpretation

### 6.1 Test Status Meanings

| Status | Symbol | Meaning |
|--------|--------|---------|
| PASSED | ✅ | Test executed successfully |
| FAILED | ❌ | Test assertion failed |
| ERROR | 💥 | Exception during test execution |
| SKIPPED | ⏭️ | Test was skipped (marker/condition) |

### 6.2 Understanding Test Output

**Example Output:**
```
boundary/test_limits.py::TestUserInputBoundaries::test_bva001_email_validation_boundaries[a@b.co-True] PASSED
```

**Breakdown:**
- `boundary/test_limits.py` - Test file
- `TestUserInputBoundaries` - Test class
- `test_bva001_email_validation_boundaries` - Test method
- `[a@b.co-True]` - Parameterized input
- `PASSED` - Result

### 6.3 Test IDs Reference

| ID Format | Category | Example |
|-----------|----------|---------|
| BVA-XXX | Boundary Value Analysis | BVA-001: Email validation |
| FT-XXX | Functional Test | FT-001: User signup |
| IT-XXX | Integration Test | IT-001: Registration flow |
| RBT-XXX | Risk-Based Test | RBT-001: Twilio failure |
| ST-XXX | Stress Test | ST-001: Burst requests |
| FE-XXX | Frontend Test | FE-001: Auth state |

---

## 7. Notification System Testing

### 7.1 SMS Notification Tests

The SMS notification system is tested through **mocking** the Twilio API. No actual SMS messages are sent during testing.

#### Mock Configuration

```python
# Tests mock the Twilio Client
with patch('app.Client') as mock_client:
    mock_instance = MagicMock()
    mock_instance.messages.create.return_value = MagicMock(sid='SM123')
    mock_client.return_value = mock_instance
```

#### Tests Performed

| Test ID | Description | Validates |
|---------|-------------|-----------|
| FT-009 | SMS triggered for new alert | `should_trigger_sms()` returns True |
| FT-010 | SMS suppressed for duplicate | `should_trigger_sms()` returns False |
| IT-003 | SMS to nearby users | Only users within 200km receive SMS |
| IT-006 | Regional distribution | Location-based filtering |
| RBT-001 | Twilio service unavailable | Error handling |
| RBT-002 | Invalid phone number | Error handling |
| ST-002 | Broadcast throughput | 50+ SMS in <10 seconds |

### 7.2 Notification Logic Tested

```
1. New Alert Created
   │
   ├── Check: Any SMS sent in area within 12 hours?
   │   ├── YES → Suppress SMS (sms_sent = False)
   │   └── NO  → Continue to Step 2
   │
   └── Step 2: Find users within 200km radius
       │
       ├── For each user in radius:
       │   └── Send SMS via Twilio API
       │
       └── Update alert.sms_sent = True
```

### 7.3 Verification Points

| Verification | How Tested |
|--------------|------------|
| Distance calculation | Haversine formula with known distances |
| Time window (12h) | Parameterized tests with time offsets |
| Radius boundary (200km) | Tests at 199km, 200km, 201km |
| SMS content formatting | Mock verification of message body |

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue: "Module not found: app"
**Solution:** Ensure you're in the correct directory
```cmd
cd d:\Sem6_course\SE\Ass1\DAS_Project\tests
```

#### Issue: "pytest command not found"
**Solution:** Install pytest
```cmd
pip install pytest
```

#### Issue: "Connection refused to MongoDB"
**Solution:** Tests use mocks - MongoDB is not required

#### Issue: Frontend tests failing
**Solution:** Rebuild node_modules
```cmd
cd Frontend
rd /s /q node_modules
npm install
```

### 8.2 Verbose Error Output

For detailed error messages:
```cmd
pytest -v --tb=long
```

### 8.3 Debug Mode

Run specific test with debug output:
```cmd
pytest -v -s -k "test_ft001"
```

---

## 9. Generating Test Reports

### 9.1 HTML Report

```cmd
pytest --html=reports/test_report.html --self-contained-html
```

### 9.2 JUnit XML (for CI/CD)

```cmd
pytest --junitxml=reports/junit.xml
```

### 9.3 Coverage Report

```cmd
pytest --cov=../Backend --cov-report=html:reports/coverage
```

---

## 10. Quick Reference Commands

| Action | Command |
|--------|---------|
| Run all backend tests | `pytest -v` |
| Run all frontend tests | `npm run test` |
| Run with coverage | `pytest --cov=../Backend` |
| Run specific category | `pytest -m safety` |
| Run single test | `pytest -k "test_name"` |
| Watch mode (frontend) | `npm run test:watch` |
| Generate HTML report | `pytest --html=report.html` |

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Author | Test Engineer | _________ | 2026-01-25 |
| Reviewer | QA Lead | _________ | _________ |
| Approver | Project Manager | _________ | _________ |

---

*End of Document*
