from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database.connection import init_db_pool, close_db_pool
from app.scheduler import start_scheduler
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Ops Excellence AI...")
    await init_db_pool()
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_db_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

from app.api.v1 import transactions, issues, feedback
# from app.api.v1 import merchants, anomalies
app.include_router(transactions.router, prefix=f"{settings.API_V1_STR}/transactions", tags=["transactions"])
app.include_router(issues.router, prefix=f"{settings.API_V1_STR}/issues", tags=["issues"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["feedback"])
# app.include_router(merchants.router, prefix=settings.API_V1_STR)
# app.include_router(anomalies.router, prefix=settings.API_V1_STR)
# app.include_router(feedback.router, prefix=settings.API_V1_STR)
