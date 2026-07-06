"""Backend launcher that reads host/port from app settings."""

import argparse

import uvicorn

from app.config import settings


def run_server(reload: bool = False, host: str | None = None, port: int | None = None) -> None:
    """Start uvicorn using .env-driven defaults with optional CLI overrides."""
    uvicorn.run(
        "app.main:app",
        host=host or settings.app_host,
        port=port if port is not None else settings.server_port,
        reload=reload,
    )


def main() -> None:
    """CLI entrypoint for local development and testing."""
    parser = argparse.ArgumentParser(description="Run ComfyUI API backend")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--host", default=None, help="Override bind host")
    parser.add_argument("--port", type=int, default=None, help="Override bind port")
    args = parser.parse_args()

    run_server(reload=args.reload, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
