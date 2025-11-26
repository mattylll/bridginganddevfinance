"""Web scraping framework for monitoring lender websites."""

from app.scrapers.base import BaseScraper
from app.scrapers.manager import ScraperManager
from app.scrapers.change_detector import ChangeDetector

__all__ = [
    "BaseScraper",
    "ScraperManager",
    "ChangeDetector",
]
