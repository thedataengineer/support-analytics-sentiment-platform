from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from api import auth, ingest_csv, report_api, search_api, jira_ingest, ticket_detail_api, support_analytics_api, nlq_api, parquet_ingest, upload_api, dashboard_api, advanced_analytics_api
from database import init_database, check_database_connection
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a') if not settings.debug else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Sentiment Analysis Platform API")

    # Initialize database
    try:
        init_database()
        if check_database_connection():
            logger.info("Database initialized successfully")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Sentiment Analysis Platform API")

app = FastAPI(
    title="Sentiment Analysis Platform API",
    description="API for sentiment analysis and reporting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"{request.method} {request.url.path} - Client: {request.client.host}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"{request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_id": str(time.time())}
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(ingest_csv.router, prefix="/api", tags=["ingestion"])
app.include_router(jira_ingest.router, prefix="/api", tags=["jira"])
app.include_router(report_api.router, prefix="/api", tags=["reports"])
app.include_router(search_api.router, prefix="/api", tags=["search"])
app.include_router(ticket_detail_api.router, prefix="/api", tags=["tickets"])
app.include_router(support_analytics_api.router, prefix="/api", tags=["analytics"])
app.include_router(nlq_api.router, prefix="/api", tags=["nlq"])
app.include_router(parquet_ingest.router, prefix="/api", tags=["parquet"])
app.include_router(upload_api.router, prefix="/api/upload", tags=["upload"])
app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(advanced_analytics_api.router, prefix="/api/analytics", tags=["advanced-analytics"])

@app.get("/")
async def root():
    """API root endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Sentiment Analysis Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "storage": "parquet",
        "auth_db": check_database_connection(),
        "timestamp": time.time()
    }

    logger.info(f"Health check: {health_status}")
    return health_status
