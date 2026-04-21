"""FastAPI application entry point."""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.presentation.routes import session_routes, chat_routes, image_routes

# Ensure log directory exists
log_file_path = Path(settings.log_file)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# Clear old log file on startup
if log_file_path.exists():
    log_file_path.unlink()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file, mode='w'),  # 'w' mode to overwrite
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ComfyUI AI Chat",
    description="AI-powered image generation chat system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session_routes.router)
app.include_router(chat_routes.router)
app.include_router(image_routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# Serve Vue frontend (production build) — must be AFTER all API routes
frontend_dist = Path(__file__).parent.parent / settings.frontend_dir
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA catch-all: serve index.html for client-side routing."""
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Application starting", extra={
        "host": settings.app_host,
        "port": settings.app_port
    })
    
    # Ensure directories exist
    settings.sessions_path.mkdir(parents=True, exist_ok=True)
    Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Application shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
