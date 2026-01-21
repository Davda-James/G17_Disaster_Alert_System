# Disaster Alert System (DAS) - QA Suite

[![Tests](https://github.com/your-org/das-project/actions/workflows/main.yml/badge.svg)](https://github.com/your-org/das-project/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)](reports/)

## 🚨 Overview

A comprehensive testing suite for a mission-critical Disaster Alert System. This project demonstrates industry-level software testing practices including:

- **Functional Testing** (FT-001 to FT-013)
- **Integration Testing** (IT-001 to IT-006)
- **Boundary Value Analysis** (BVA-001 to BVA-015)
- **Stress/Performance Testing** (ST-001 to ST-006)
- **Risk-Based Safety Testing** (RBT-001 to RBT-009)

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
├── src/                      # Source code (mock implementation)
│   ├── core/                 # Logging, Configuration
│   ├── alerts/               # Alert Manager
│   ├── api/                  # SMS/Email Gateways
│   └── db/                   # Database Manager
├── tests/                    # Test suite
│   ├── functional/           # Unit & Functional tests
│   ├── integration/          # End-to-end tests
│   ├── boundary/             # Boundary value tests
│   ├── stress/               # Performance tests
│   └── safety/               # Risk-based tests
├── tools/                    # Evaluation framework
│   └── evaluator.py          # Test metrics calculator
├── docs/                     # Documentation
│   ├── latex/                # LaTeX report
│   └── GIT_WORKFLOW.md       # Git strategy
└── .github/workflows/        # CI/CD pipeline
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/das-project.git
cd DAS_Project

# Install dependencies
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/functional -v
pytest tests/safety -m safety
pytest tests/stress -m stress

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Evaluation

```bash
# Full evaluation with report
python tools/evaluator.py

# Evaluate specific test categories
python tools/evaluator.py -m functional integration
```

## 📊 Evaluation Metrics

The evaluator calculates:

| Metric | Description | Target |
|--------|-------------|--------|
| Success Rate | % of passing tests | ≥95% for PROD_READY |
| Code Coverage | % of code covered | ≥80% for PROD_READY |
| Defect Density | Failed tests / Total | ≤0.05 for PROD_READY |

### Status Levels

- 🟢 **PROD_READY**: All metrics meet production thresholds
- 🟡 **STABLE**: Metrics meet minimum requirements
- 🔴 **CRITICAL_FAILURE**: System not safe for deployment

## 🧪 Test Categories

### Functional Tests (tests/functional)
Core logic validation for alert triggers, severity classification, and acknowledgment flows.

### Boundary Tests (tests/boundary)
Edge case testing for all thresholds (earthquake magnitude, tsunami height, etc.)

### Integration Tests (tests/integration)
End-to-end flows: Sensor → Alert → Notification → Database

### Stress Tests (tests/stress)
Performance under high load: 100+ concurrent alerts, bulk notifications

### Safety Tests (tests/safety)
**Risk-Based Testing** for failure modes:
- Network failure during alerts
- Database corruption fallback
- Cascade failure prevention

## 📝 Documentation

Full LaTeX documentation available in `docs/latex/das_report.tex` including:
- Executive Summary
- IEEE 829 Test Methodology
- Detailed Test Case Tables
- Risk Matrix
- Evaluation Results
- Bibliography (ISO/IEC standards)

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/main.yml`):

1. **Functional Tests** → Must pass first
2. **Integration Tests** → Runs after functional
3. **Safety Tests** → Runs in parallel
4. **Stress Tests** → Only on main branch
5. **Evaluation** → Generates report
6. **Quality Gate** → Blocks deployment if CRITICAL_FAILURE

## 📜 License

MIT License - See LICENSE file

## 👥 Team

DAS Development Team - Software Engineering Assignment 1
