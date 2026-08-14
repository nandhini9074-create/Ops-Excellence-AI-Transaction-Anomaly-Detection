# Ops Excellence AI – Transaction Anomaly Detection

A comprehensive machine learning-powered system for detecting anomalies in merchant/outlet transactions.

## Architecture
- **Backend**: FastAPI, SQLAlchemy (async)
- **Hot Storage**: PostgreSQL
- **Cold Storage**: Cloudflare D1 (accessed via Cloudflare Worker)
- **ML Engine**: Z-Score, Isolation Forest, Prophet, Bayesian Change-Point Detection
- **Frontend**: React (Vite + TypeScript)

## Prerequisites
- Docker (for PostgreSQL)
- Node.js 18+ (for frontend and Cloudflare Worker)
- Python 3.11+

## Local Setup

1. **Database**
   ```bash
   docker-compose up -d
   ```

2. **Backend Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Cloudflare Worker Setup**
   ```bash
   cd cloudflare/d1-worker
   npm install
   npx wrangler dev
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running the Application
Use the `scripts/` directory for local testing:
- `python scripts/seed_database.py` - seed merchants and outlets
- `python scripts/generate_dataset.py` - generate 2,000 realistic transactions
- `python scripts/seed_database.py --transactions` - load transactions to database
- `python scripts/run_baseline.py` - generate baseline profiles
- `python scripts/run_detection.py` - execute the anomaly detection engine
