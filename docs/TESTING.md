# Testing Guide - FashionVision AI

## Overview

This document describes the testing strategy and procedures for the FashionVision AI system.

## Testing Stack

### Backend
- **pytest** - Testing framework
- **pytest-asyncio** - Async support
- **httpx** - HTTP client for API testing

### Frontend
- **Vitest** - Testing framework (already in package.json)
- **React Testing Library** - Component testing

## Running Tests

### Backend Tests

```bash
cd backend

# Create virtual environment if needed
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestPasswordHashing

# Run tests matching pattern
pytest -k "test_login"
```

### Frontend Tests

```bash
cd frontend

# Install dependencies
npm install

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/hooks/useCamera.test.js
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation.

**Backend:**
- `test_auth.py` - Password hashing, JWT token creation/validation
- `test_pos_terminal.py` - Mock POS terminal service
- `test_session_manager.py` - Session management logic

**Frontend:**
- Hook tests (useCamera, useSessionTimeout)
- Utility function tests

### Integration Tests

Integration tests verify that components work together correctly.

**API Tests (`test_api.py`):**
- Health endpoints
- Authentication flow (login, token refresh)
- Category CRUD operations
- Product endpoints
- Inventory endpoints
- Cart operations
- POS terminal endpoints
- Analytics endpoints

### End-to-End Tests

E2E tests verify the complete user flows.

**Planned E2E Scenarios:**
1. Login → Detect clothing → Add to cart → Submit → Approve → Pay → Receipt
2. Admin: Login → Create product → Add variant → Adjust stock
3. Session timeout and token refresh

## Test Database

Tests use a separate database to avoid affecting development data:

```python
TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/fashionvision_ai_test"
```

**Setup test database:**
```bash
# Create database
psql -U postgres -c "CREATE DATABASE fashionvision_ai_test;"

# Run migrations (if using Alembic)
alembic upgrade head -d "postgresql://user:pass@localhost:5432/fashionvision_ai_test"
```

## Writing Tests

### Backend Test Example

```python
import pytest

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_something(self, authenticated_client):
        response = await authenticated_client.get("/api/endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

### Frontend Test Example

```javascript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('should do something', async () => {
  render(<MyComponent />);
  const button = screen.getByRole('button');
  await userEvent.click(button);
  expect(screen.getByText('Result')).toBeInTheDocument();
});
```

## Coverage Targets

| Component | Target |
|------------|--------|
| Backend overall | 70% |
| Auth service | 90% |
| POS terminal | 90% |
| API endpoints | 60% |
| Frontend overall | 50% |
| Critical hooks | 80% |

## CI/CD

Tests run automatically on:
- Pull requests
- Push to main branch
- Scheduled daily run at midnight

## Troubleshooting

### Tests hanging
- Check for unclosed async resources
- Ensure event loops are properly set up

### Database connection errors
- Verify PostgreSQL is running
- Check database credentials
- Ensure test database exists

### Import errors
- Verify PYTHONPATH includes backend directory
- Check __init__.py files exist