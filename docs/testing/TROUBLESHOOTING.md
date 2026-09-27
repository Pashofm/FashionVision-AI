# Troubleshooting Guide

Common issues and solutions for testing FashionVision-AI.

## Database Issues

### "could not connect to server"

PostgreSQL is not running or not accessible.

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5433

# Start PostgreSQL if using Docker
docker-compose up -d postgres
```

### "database does not exist"

Test database hasn't been created.

**Solution:**
```bash
./scripts/setup_test_db.sh
```

### "connection refused"

Check the port and host in TEST_DATABASE_URL.

**Solution:**
```bash
export DB_HOST=localhost
export DB_PORT=5433
./scripts/setup_test_db.sh
```

---

## Import Issues

### "No module named 'backend'"

PYTHONPATH not set correctly.

**Solution:**
```bash
export PYTHONPATH=/path/to/FashionVision-AI
```

Or in `conftest.py`, the path is automatically added:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### "cannot import name 'X' from 'backend.app.models'"

Model not exported from `__init__.py`.

**Solution:** Check `backend/app/models/__init__.py` and add the export.

---

## Test Isolation Issues

### "duplicate key value violates unique constraint"

Data from previous test still in database.

**Solution:**
1. Ensure `db_session` fixture is being used (it auto-rollbacks)
2. Don't manually call `commit()` in tests
3. Use factories which generate unique names

### Tests affect each other

Tests are not properly isolated.

**Solution:**
- Use `db_session` fixture which provides automatic rollback
- Don't share fixtures between tests that modify them
- Create fresh data in each test using factories

---

## Async Issues

### "RuntimeError: Event loop is closed"

Event loop handling issue.

**Solution:**
Ensure `pytest-asyncio` is installed and tests use `@pytest.mark.asyncio`:
```python
import pytest
pytestmark = pytest.mark.asyncio
```

### "coroutine 'X' was never awaited"

Forgot to await an async function.

**Solution:**
```python
# Wrong
result = some_async_function()

# Correct
result = await some_async_function()
```

---

## Factory Issues

### "Unique constraint violation" with factories

Factory not generating unique values.

**Solution:**
Factories in `tests/factories/` automatically generate unique suffixes. Make sure you're using `create()` not just building the dict.

```python
# Wrong - might cause conflicts
data = UserFactory.build()

# Correct - saves with unique values
user = await UserFactory.create(db_session)
```

---

## Session Manager Issues

### Session shows as active when it should be expired

Check `last_activity_at` vs `started_at`.

**Note:** The session manager now uses `last_activity_at` for expiration checks, not `started_at`. This was fixed to properly track activity.

```python
# The session is expired based on last_activity_at, not started_at
session.last_activity_at = old_time
# Session will now correctly show as inactive
```

---

## Fixture Issues

### "fixture 'X' not found"

Fixture not in `conftest.py` or not imported.

**Solution:**
1. Check fixture is defined in `tests/conftest.py`
2. Check pytest can find conftest.py (should be in `tests/` directory)
3. Restart pytest

---

## PostgreSQL-Specific Issues

### "permission denied for database"

User doesn't have access to test database.

**Solution:**
```sql
GRANT ALL PRIVILEGES ON DATABASE fashionvision_ai_test TO fashionvision_ai_user;
```

### "schema does not exist"

Database schema not created.

**Solution:**
```bash
# Recreate database and schema
./scripts/teardown_test_db.sh
./scripts/setup_test_db.sh
```

---

## Coverage Issues

### "No data to report"

Coverage not properly configured.

**Solution:**
```bash
# Install coverage packages
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Docker/Container Issues

### Tests pass locally but fail in Docker

Different environment.

**Solution:**
1. Ensure Docker container has correct PYTHONPATH
2. Check environment variables are set in Dockerfile
3. Verify database connection from inside container

---

## Still Having Issues?

1. Check the test output for specific error messages
2. Run tests with `-v` flag for verbose output
3. Run single test to isolate the issue:
   ```bash
   pytest tests/path/to/test.py::TestClass::test_name -v
   ```
4. Check the [TESTING_GUIDE.md](TESTING_GUIDE.md) for configuration details
