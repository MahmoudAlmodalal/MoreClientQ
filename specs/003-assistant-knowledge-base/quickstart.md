# Quickstart Guide: Assistant & Knowledge Base

This document details the commands and steps needed to configure, run, and verify the Assistant and Knowledge Base feature.

---

## 1. Prerequisites and Setup

### 1.1 Add Dependencies
Add `minio>=7.2.0` to the python dependencies:
* File: `backend/requirements.txt`
* Command to install:
```bash
pip install -r backend/requirements.txt
```

### 1.2 Database Migrations
Apply alembic migrations to update the PostgreSQL schema with new constraints, unique indices, and cascade settings:
```bash
cd backend
alembic revision --autogenerate -m "add_assistants_and_documents_constraints"
alembic upgrade head
```

### 1.3 Start Infrastructure Services
Make sure Postgres, Redis, ChromaDB, MinIO, and Celery are running:
```bash
# Start all support containers
docker-compose up -d postgres redis chromadb minio

# Run Celery worker locally for development (from the backend directory)
cd backend
celery -A app.tasks.celery_app worker -Q ingestion,maintenance -l info
```

---

## 2. Running the Backend
From the `backend` directory:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Running the Frontend
From the `frontend` directory:
```bash
npm install
npm run dev
```

---

## 4. Verification & Testing

### 4.1 Running Automated Tests
Run pytest to verify the model validations, API behavior, and database policies:
```bash
cd backend
pytest tests/api/test_assistants.py
pytest tests/api/test_documents.py
```

### 4.2 Manual Verification Checklist
1. **Create Assistant**:
   - Access the dashboard (`http://client1.localhost:3000/dashboard/assistants`).
   - Create an assistant. Verify that leaving the name blank yields validation errors.
   - Edit the assistant and verify changes persist.
2. **Upload Document**:
   - Navigate to the knowledge base of the assistant.
   - Upload a PDF, DOCX, or TXT file. Verify the document transitions through `pending` -> `processing` -> `ready`.
   - Re-upload the same file; verify that upload is blocked with "This file already exists in this assistant's knowledge base."
3. **Ingest URL**:
   - Submit a valid public URL.
   - Submit an invalid or private URL (e.g. `http://localhost:9999` or redirect-to-login link); verify the request is blocked synchronously with an error message.
4. **Delete Assistant with active conversations**:
   - Verify that deleting an assistant fails if there are open conversations.
5. **Delete Document**:
   - Delete a document; check that it is purged from both the database and ChromaDB collection.
