# FashionVision AI - Backend Setup

## Database Setup

### Option 1: Using the setup script

```bash
cd backend
chmod +x setup_database.sh
./setup_database.sh
```

### Option 2: Manual setup

```bash
# 1. Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Or (macOS)
brew services start postgresql

# 2. Create user (run as postgres)
sudo -u postgres createuser --superuser $USER

# 3. Create database
sudo -u postgres createdb fashionvision

# 4. Load schema
sudo -u postgres psql -d fashionvision -f database/schema.sql
```

### Option 3: Using existing postgres user

```bash
# If you have postgres user password
createdb -U postgres fashionvision
psql -U postgres -d fashionvision -f database/schema.sql
```

## Running the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000
```

## Environment Variables

Create a `.env` file in `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/fashionvision
```

## Verify Setup

```bash
# Check if API is running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected"}
```

## Quick Test - Create a Product

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Camiseta Roja", "cantidad": 10, "precio": 299.99, "color": "Rojo"}'
```

## API Documentation

Once running, visit: http://localhost:8000/docs

This provides an interactive Swagger UI to test all endpoints.