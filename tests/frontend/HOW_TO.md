# Frontend Testing Guide

## Overview

The frontend tests verify the React components, context providers (AuthContext), and utility functions. They use **Vitest** + **React Testing Library**.

## Prerequisites

1.  Navigate to the `Frontend` directory.
    ```bash
    cd d:\Sem6_course\SE\Ass1\DAS_Project\Frontend
    ```
2.  Install dependencies (if not already done):
    ```bash
    npm install
    ```

## Running Tests

Tests are located in `tests/frontend` but must be run via the `Frontend` package setup.

### Run All Frontend Tests

```bash
cd Frontend
npm run test
```

### Watch Mode (Development)

Run tests continuously as you edit files:

```bash
cd Frontend
npm run test:watch
```

### Running Specific Test File

```bash
cd Frontend
npm run test -- ../tests/frontend/AuthContext.test.tsx
```

## Test Structure

*   `AuthContext.test.tsx`: Tests authentication logic (login/signup/token).
*   `utils.test.ts`: Tests utility helpers (validation, formatting).
*   `setup.ts`: Test environment setup (e.g., mocking browser APIs).
