# DisasterWatch Backend API - Test Suite

[![Tests](https://github.com/your-org/das-project/actions/workflows/main.yml/badge.svg)](https://github.com/your-org/das-project/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)](reports/)

## 🚨 Overview

A comprehensive testing suite for the **DisasterWatch Backend API** - a mission-critical disaster alert system built with Flask. This project demonstrates industry-level software testing practices including:

- **Functional Testing** (FT-001 to FT-015)
- **Integration Testing** (IT-001 to IT-007)
- **Boundary Value Analysis** (BVA-001 to BVA-011)
- **Stress/Performance Testing** (ST-001 to ST-008)
- **Risk-Based Safety Testing** (RBT-001 to RBT-015)

## 📋 Standards Compliance

| Standard | Application |
|----------|-------------|
| IEEE 829 | Test Documentation |
| ISO/IEC/IEEE 29119 | Software Testing |
| ISTQB | Testing Methodology |
| ISO 22324 | Severity Classification |

## 🏗️ Project Structure

```
DAS_Project/
├── Backend/                  # Flask API (app.py)
│   ├── app.py                # Main Flask application
│   └── requirements.txt      # Python dependencies
├── Frontend/                 # React/TypeScript frontend
│   └── src/                  # Frontend source code
├── tests/                    # Test suite
│   ├── conftest.py           # Shared fixtures
│   ├── functional/           # API endpoint tests
│   │   └── test_alerts.py    # Auth & alert tests
│   ├── integration/          # End-to-end flows
│   │   └── test_flow.py      # User journey tests
│   ├── boundary/             # Boundary value tests
│   │   └── test_limits.py    # Input validation tests
│   ├── stress/               # Performance tests
│   │   └── test_load.py      # Load & throughput tests
│   └── safety/               # Risk-based tests
│       └── test_failures.py  # Failure scenario tests
├── reports/                  # Test reports
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/das-project.git
cd DAS_Project

# Install test dependencies
pip install -r tests/requirements.txt

# Install backend dependencies
pip install -r Backend/requirements.txt
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/functional -v
pytest tests/safety -m safety
pytest tests/stress -m stress
pytest tests/integration -m integration

# Run with coverage (targeting Backend)
pytest tests/ --cov=Backend --cov-report=html

# Run excluding slow tests
pytest tests/ -m "not slow"
```

### Run Specific Test Files

```bash
# Functional tests only
pytest tests/functional/test_alerts.py -v

# Boundary tests only  
pytest tests/boundary/test_limits.py -v

# Safety tests only
pytest tests/safety/test_failures.py -v
```

## 📊 Test Categories

### Functional Tests (`tests/functional/`)
Tests for core API endpoints:
- **User Authentication**: Signup, Login, JWT tokens
- **Alert Management**: Create, Retrieve, Filter alerts
- **SMS Notification Logic**: Trigger & suppression rules
- **Geocoding**: Location to coordinates conversion

### Boundary Tests (`tests/boundary/`)
Edge case testing for all inputs:
- Email, phone, password validation boundaries
- Coordinate value limits (lat/lng)
- Alert severity and type validation
- SMS radius (200km) and time window (12h) boundaries

### Integration Tests (`tests/integration/`)
End-to-end flows:
- User Registration → Login → Create Alert → SMS Notification
- Duplicate alert suppression flow
- Regional alert distribution
- Profile update with re-geocoding

### Stress Tests (`tests/stress/`)
Performance under high load:
- 50+ concurrent API requests
- 100 user SMS broadcast throughput
- Bulk user registration
- Query performance benchmarks

### Safety Tests (`tests/safety/`)
**Risk-Based Testing** for failure modes:
- Twilio SMS gateway failures
- MongoDB connection/write failures
- Geocoding API timeouts
- Authentication failures
- Cascade failure prevention (SMS fails but alert stored)

## 🧪 Key Test Fixtures

Located in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `flask_app` | Flask app configured for testing |
| `client` | Flask test client |
| `mock_mongo` | Mocked MongoDB |
| `mock_twilio` | Mocked Twilio SMS client |
| `mock_geocoding` | Mocked OpenStreetMap API |
| `sample_user_data` | Sample user registration data |
| `sample_alert_data` | Sample flood alert data |

## 📝 API Endpoints Tested

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/signup` | POST | User registration |
| `/api/login` | POST | User authentication |
| `/api/me` | GET | Get current user |
| `/api/user/<id>` | PUT | Update user profile |
| `/api/alerts` | POST | Create new alert |
| `/api/alerts` | GET | Get alerts (with filters) |

## 📈 Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Success Rate | % of passing tests | ≥95% |
| Code Coverage | % of Backend code covered | ≥80% |
| Defect Density | Failed tests / Total | ≤0.05 |

### Status Levels

- 🟢 **PROD_READY**: All metrics meet production thresholds
- 🟡 **STABLE**: Metrics meet minimum requirements
- 🔴 **CRITICAL_FAILURE**: System not safe for deployment

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/main.yml`):

1. **Install Dependencies** → Setup Python & packages
2. **Functional Tests** → Must pass first
3. **Integration Tests** → Runs after functional
4. **Safety Tests** → Runs in parallel
5. **Stress Tests** → Only on main branch
6. **Coverage Report** → Generate HTML report
7. **Quality Gate** → Blocks deployment if CRITICAL_FAILURE

## 🛠️ Backend Technologies Tested

- **Flask** - Web framework
- **Flask-JWT-Extended** - Authentication
- **Flask-PyMongo** - MongoDB integration
- **Flask-Bcrypt** - Password hashing
- **Twilio** - SMS notifications
- **Geopy** - Distance calculations
- **OpenStreetMap Nominatim** - Geocoding

## 📜 License

MIT License - See LICENSE file

## 👥 Team

DisasterWatch Development Team - Software Engineering Assignment 1
