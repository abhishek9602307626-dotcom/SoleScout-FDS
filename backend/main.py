"""
SoleScout FDS - FastAPI Backend Entry Point
Production-grade Sneaker Price Intelligence & Analytics API
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure UTF-8 output encoding for console on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database import init_db
from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("solescout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("Initializing SoleScout database schema...")
    init_db()
    logger.info("SoleScout backend started. Database ready.")
    yield
    logger.info("SoleScout backend shutting down.")


app = FastAPI(
    title="SoleScout API",
    description=(
        "Production-Grade Sneaker Price Intelligence & Analytics — "
        "College Fundamentals of Data Science (FDS) Project"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error": str(exc)},
    )


app.include_router(router, prefix="/api")


STATIC_APP_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "app.html"))


@app.get("/app", response_class=HTMLResponse, tags=["Frontend"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard_app():
    """Serves the interactive single-page SaaS dashboard for demonstration."""
    if os.path.exists(STATIC_APP_FILE):
        return FileResponse(STATIC_APP_FILE)
    return HTMLResponse("<h3>SoleScout Frontend App is ready. Run npm run dev in frontend/.</h3>")


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "project": "SoleScout Sneaker Price Intelligence & Analytics",
        "version": "2.0.0",
        "message": "SoleScout Analytics Backend is operational.",
        "dashboard_ui": "/app",
        "interactive_api_docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
