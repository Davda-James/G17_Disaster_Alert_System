# Backend Testing Guide

## Overview

The backend tests cover the Flask API logic, including boundary values, functional requirements, integration flows, safety scenarios, and stress testing.

## Prerequisites

1.  Navigate to the `DAS_Project` root directory.
2.  Install backend dependencies:
    ```bash
    pip install -r Backend/requirements.txt
    ```
3.  Install test dependencies:
    ```bash
    pip install -r tests/backend/requirements.txt
    ```

## Running Tests

### From Project Root (Recommended)

You can run all backend tests from the project root:

```bash
cd d:\Sem6_course\SE\Ass1\DAS_Project
pytest tests/backend
```

### From Backend Test Folder

You can also run tests from inside the `tests/backend` folder:

```bash
cd tests/backend
pytest
```

### Running Specific Categories

*   **Boundary Value Analysis:**
    ```bash
    pytest tests/backend/boundary/test_limits.py
    ```
*   **Functional Tests:**
    ```bash
    pytest tests/backend/functional/test_alerts.py
    ```
*   **Integration Tests:**
    ```bash
    pytest tests/backend/integration/test_flow.py
    ```
*   **Safety Tests:**
    ```bash
    pytest tests/backend/safety/test_failures.py
    ```
*   **Stress Tests:**
    ```bash
    pytest tests/backend/stress/test_load.py
    ```

## Test Structure

*   `boundary/`: Input validation limits (email, phone, coordinates).
*   `functional/`: API endpoint logic (signup, login, alerts).
*   `integration/`: End-to-end user flows.
*   `safety/`: Failure modes (DB down, API timeout) - *critical for disaster systems*.
*   `stress/`: Load testing (burst requests).
*   `conftest.py`: Shared test fixtures (user data, alert data).

