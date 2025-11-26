#!/usr/bin/env python3
"""
Developer Finance Engine - Main Entry Point

Run the API server with: python main.py
Or use the CLI with: python cli.py
"""

import uvicorn

from app.core.config import get_settings
from app.core.database import init_db
from app.scheduler import start_scheduler


def main():
    """Main entry point."""
    settings = get_settings()

    # Initialize database
    print("Initializing database...")
    init_db()

    # Start scheduler for background tasks
    print("Starting scheduler...")
    start_scheduler()

    # Run the API server
    print(f"Starting API server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
