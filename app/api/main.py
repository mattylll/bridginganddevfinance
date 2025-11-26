"""
FastAPI Application

Main entry point for the Developer Finance Engine API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import lenders, products, search, scraping, dashboard, web


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: Clean up resources


app = FastAPI(
    title="Developer Finance Engine",
    description="""
    A comprehensive loan comparison and matching platform for UK property development finance.

    ## Features

    - **Loan Matching**: Find the best finance options for your development
    - **Lender Database**: Comprehensive database of UK bridging and development lenders
    - **Rate Tracking**: Monitor lender rates and terms over time
    - **Change Detection**: Get alerts when lenders change their offerings

    ## Finance Types

    - Bridging Finance
    - Development Finance
    - Mezzanine Finance
    - Equity / JV Finance
    - Developer Exit Finance
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
router = app.router

app.include_router(lenders.router, prefix="/api/v1/lenders", tags=["Lenders"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["Scraping"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

# Web dashboard routes
app.include_router(web.router, tags=["Web"])


@app.get("/api", tags=["Root"])
async def api_root():
    """API root endpoint."""
    return {
        "name": "Developer Finance Engine",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
