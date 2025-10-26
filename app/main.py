"""FastAPI application entry point."""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.presentation.routes import session_routes, chat_routes, image_routes
from app.infrastructure.logging import get_message_logger, clear_message_log

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

# Initialize and clear message logger on startup
message_logger = get_message_logger(settings.message_log_file)
message_logger.clear_log()
logger.info(f"Message log initialized at {settings.message_log_file}")

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

# Mount static files
static_path = Path(__file__).parent / "presentation" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent / "presentation" / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@app.get("/")
async def root(request: Request):
    """Serve main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


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
