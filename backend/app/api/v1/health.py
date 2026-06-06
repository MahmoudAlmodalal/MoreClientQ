import time
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, check_db_health
from app.core.redis_client import redis_client
from app.services.rag.chroma_client import chroma_client

router = APIRouter()

@router.get("/health")
async def health_check(response: Response, db: AsyncSession = Depends(get_db)):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # 1. Database Check
    db_ok, db_lat, db_err = await check_db_health(db)
    
    # 2. Redis Check
    redis_ok, redis_lat, redis_err = await redis_client.ping()
    
    # 3. ChromaDB Check
    chroma_ok, chroma_lat, chroma_err = await chroma_client.ping()

    # Determine general status
    all_healthy = db_ok and redis_ok and chroma_ok
    status_str = "ok" if all_healthy else "error"
    
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": status_str,
        "timestamp": timestamp,
        "services": {
            "database": {
                "status": "healthy" if db_ok else "unhealthy",
                "latency_ms": db_lat,
                "error": db_err
            },
            "redis": {
                "status": "healthy" if redis_ok else "unhealthy",
                "latency_ms": redis_lat,
                "error": redis_err
            },
            "chromadb": {
                "status": "healthy" if chroma_ok else "unhealthy",
                "latency_ms": chroma_lat,
                "error": chroma_err
            }
        }
    }
