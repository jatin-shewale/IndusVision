"""
IndusVision Backend - Main Application Entry Point
=====================================================
Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Docs at:  http://localhost:8000/docs (Swagger) or /redoc
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import perf_counter

from app.config import settings
from app.database import ensure_indexes, machines_collection
from app.routes import auth, users, machines, sensors, detections, inventory, alerts, maintenance, reports, ai_insights

log_path = Path(settings.LOG_FILE_PATH)
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8"),
    ],
    force=True,
)
logger = logging.getLogger("indusvision.http")

app = FastAPI(
    title="IndusVision API",
    description="AI-Powered Smart Industrial Monitoring and Management System — Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_http_request(request, call_next):
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed method=%s path=%s", request.method, request.url.path)
        raise
    elapsed_ms = round((perf_counter() - started) * 1000, 1)
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(machines.router)
app.include_router(sensors.router)
app.include_router(detections.router)
app.include_router(inventory.router)
app.include_router(alerts.router)
app.include_router(maintenance.router)
app.include_router(reports.router)
app.include_router(ai_insights.router)


@app.on_event("startup")
async def on_startup():
    try:
        await ensure_indexes()
        removed = await machines_collection.delete_many({
            "machine_id": {"$in": ["MACHINE_02", "MACHINE_03"]}
        })
    except Exception:
        logging.getLogger(__name__).exception("startup_failed during MongoDB setup")
        raise
    if removed.deleted_count:
        logger.info("removed_old_demo_machines count=%s ids=MACHINE_02,MACHINE_03", removed.deleted_count)
    logger.info("MongoDB indexes ensured; API ready")


@app.get("/")
def root():
    return {
        "message": "IndusVision API is running",
        "docs": "/docs",
        "first_time_setup": "POST /api/auth/bootstrap-admin to create your first admin account",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
