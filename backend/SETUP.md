# FashionVision AI - Database Setup Guide

This guide explains how to set up the PostgreSQL database for FashionVision AI.

---

## Prerequisites

| Requirement | Version |
|--------------|---------|
| PostgreSQL | 12+ |
| Python | 3.9+ |
| pip | Latest |

---

## Quick Setup (5 minutes)

### Step 1: Install PostgreSQL

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install postgresql-server postgresql
sudo postgresql-setup --initdb
sudo systemctl start postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from: https://www.postgresql.org/download/windows/

---

### Step 2: Create Database

**Option A: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Right-click "Databases" → "Create..."
3. Name: `fashionvision`
4. Save

**Option B: Using command line**
```bash
# Connect as postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE fashionvision;

# Exit
\q
```

**Option C: Using createdb**
```bash
createdb fashionvision
```

---

### Step 3: Load Schema

```bash
cd /path/to/FashionVision-AI/backend
psql -d fashionvision -f database/schema.sql
```

Expected output:
```
CREATE TYPE
CREATE TABLE
...
CREATE INDEX
INSERT
```

---

### Step 4: Install Python Dependencies

```bash
cd /path/to/FashionVision-AI/backend

# Create virtual environment (recommended)
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Step 5: Configure Environment

```bash
# Copy example file
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Local development (default)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fashionvision

# Or with your username
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/fashionvision
```

---

### Step 6: Run the Backend

```bash
uvicorn main:app --reload --port 8000
```

---

## Verify It Works

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status":"healthy","database":"connected"}
```

### 2. API Documentation
Visit: http://localhost:8000/docs

### 3. Test Endpoints

**Create a product:**
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Gorra Roja",
    "cantidad": 25,
    "precio": 999.99,
    "color": "Rojo",
    "tipo_prenda": "gorra"
  }'
```

**List products:**
```bash
curl http://localhost:8000/api/products
```

**Get analytics:**
```bash
curl http://localhost:8000/api/analytics/sales
```

---

## Common Issues

### Error: "Role does not exist"

**Cause:** Your system user doesn't have a PostgreSQL role.

**Solution:**
```bash
sudo -u postgres createuser $USER
```

### Error: "Database does not exist"

**Cause:** Database not created.

**Solution:**
```bash
sudo -u postgres createdb fashionvision
```

### Error: "Connection refused"

**Cause:** PostgreSQL not running.

**Solution:**
```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql

# Windows
Start → Services → PostgreSQL → Start
```

### Error: "Password authentication failed"

**Cause:** Incorrect credentials in DATABASE_URL.

**Solution:**
1. Edit pg_hba.conf to allow trust authentication for local connections
2. Or set a password for your user:
```bash
sudo -u postgres psql
ALTER USER your_user PASSWORD 'your_password';
```

---

## Development Workflow

### Daily Use

```bash
# Terminal 1: Start database (if not running)
sudo systemctl start postgresql

# Terminal 2: Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 3: Start frontend
cd frontend
npm run dev
```

### Reset Database

```bash
# Drop and recreate
sudo -u postgres dropdb fashionvision
sudo -u postgres createdb fashionvision
sudo -u postgres psql -d fashionvision -f database/schema.sql
```

### Backup Database

```bash
pg_dump fashionvision > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql fashionvision < backup_20240101.sql
```

---

## Production Deployment

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@your-host:5432/fashionvision
```

### Security Recommendations

1. Change default postgres password
2. Use SSL connections
3. Restrict pg_hba.conf
4. Use connection pooling (PgBouncer)
5. Regular backups

---

## Next Steps

After setup, see:
- `README.md` - Running the application
- `docs/database.md` - Database documentation
- `docs/api.md` - API reference (if available)

---

## Help

- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **FastAPI Docs:** https://fastapi.tiangolo.com/