from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.v1.health import health_check

app = FastAPI(title="Multi-Tenant AI Assistant Platform")

# Register versioned API endpoints under /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

# Also map the health check endpoint directly to root /health for docker/k8s probes
app.add_api_route("/health", health_check, methods=["GET"], tags=["health"])

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is operational"}
