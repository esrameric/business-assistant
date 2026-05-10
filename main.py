"""
FastAPI application initialization and router setup.
Main entry point for the RAG-based business assistant API.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared_utils import init_db, start_simulation_scheduler, stop_simulation_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    """
    # Startup
    try:
        logger.info("Application starting up...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Start business simulation
        start_simulation_scheduler()
        logger.info("Business simulation started")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    stop_simulation_scheduler()
    logger.info("Business simulation stopped")


# Create FastAPI application
app = FastAPI(
    title="RAG Business Assistant API",
    description="Retrieval-Augmented Generation based business assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "service": "RAG Business Assistant API",
        "version": "1.0.0"
    }


# ==================== Router Mounting Points ====================
# Developer B: Uncomment and add chat router
# from routers import chat_router
# app.include_router(chat_router.router, prefix="/api/chat", tags=["Chat"])

# Developer C: Uncomment and add automation router
# from routers import automation_router
# app.include_router(automation_router.router, prefix="/api/automation", tags=["Automation"])

# Additional routers can be added here following the same pattern


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Load configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
