# Quickstart Guide: MoreClient AI Enterprise Platform

This guide outlines steps to configure, run, and test the MoreClient AI application locally.

## Prerequisites
- **Python**: v3.11+
- **Node.js**: v18+ with `npm`
- **Docker**: For running PostgreSQL, Qdrant, Redis, and ClamAV locally

---

## 1. Local Infrastructure Setup

Launch the required services using Docker Compose:

```bash
# Spin up PostgreSQL, Qdrant, Redis, and ClamAV (scanner)
docker compose -f docker-compose.local.yml up -d
```

---

## 2. Backend Setup

1. **Navigate to backend and create a virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file under the `backend/` directory:
   ```ini
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/moreclient
   REDIS_URL=redis://localhost:6379/0
   QDRANT_URL=http://localhost:6333
   CLAMAV_HOST=localhost
   CLAMAV_PORT=3310
   JWT_SECRET=supersecretjwtkeychangeinprod
   STRIPE_API_KEY=sk_test_...
   OPENAI_API_KEY=sk-proj-...
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Launch the FastAPI backend server**:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```
   *The API documentation will be available at `http://localhost:8000/docs`.*

---

## 3. Frontend Setup

1. **Navigate to frontend and install dependencies**:
   ```bash
   cd ../frontend
   npm install
   ```

2. **Configure environment variables**:
   Create a `.env` file under the `frontend/` directory:
   ```ini
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. **Launch the React development server**:
   ```bash
   npm run dev
   ```
   *The application dashboard will be running at `http://localhost:5173`.*

---

## 4. Running Tests

To validate the configuration and test logic:

### Backend Tests (pytest)
```bash
cd ../backend
pytest
```

### Frontend Tests (Vitest)
```bash
cd ../frontend
npm run test
```
