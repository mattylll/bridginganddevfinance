"""
Scraper Manager

Orchestrates scraping operations across all lenders.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Type
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.lender import Lender, LenderStatus
from app.scrapers.base import BaseScraper, GenericScraper, ScrapeResult
from app.scrapers.change_detector import ChangeDetector, DetectedChange
from app.core.config import get_settings


@dataclass
class ScrapeSummary:
    """Summary of a scrape run."""
    timestamp: datetime
    lenders_scraped: int
    lenders_failed: int
    total_changes: int
    critical_changes: int
    errors: List[str]


class ScraperManager:
    """
    Manages scraping operations for all lenders.

    Responsibilities:
    - Determine which lenders need scraping
    - Execute scrapers (generic or custom)
    - Coordinate change detection
    - Handle errors and retries
    """

    # Registry of custom scrapers by lender slug
    _custom_scrapers: Dict[str, Type[BaseScraper]] = {}

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.change_detector = ChangeDetector(db)

    @classmethod
    def register_scraper(cls, lender_slug: str, scraper_class: Type[BaseScraper]):
        """Register a custom scraper for a lender."""
        cls._custom_scrapers[lender_slug] = scraper_class

    def get_lenders_due_for_scrape(self) -> List[Lender]:
        """Get lenders that haven't been scraped recently."""
        cutoff = datetime.utcnow() - timedelta(days=self.settings.scrape_interval_days)

        return (
            self.db.query(Lender)
            .filter(Lender.status == LenderStatus.ACTIVE)
            .filter(Lender.website_url != None)
            .filter(
                (Lender.last_scraped_at == None) |
                (Lender.last_scraped_at < cutoff)
            )
            .all()
        )

    def scrape_lender(
        self,
        lender: Lender,
        auto_apply_changes: bool = False
    ) -> tuple[ScrapeResult, List[DetectedChange]]:
        """
        Scrape a single lender.

        Args:
            lender: Lender to scrape
            auto_apply_changes: Whether to automatically apply detected changes

        Returns:
            Tuple of (ScrapeResult, list of changes)
        """
        # Get appropriate scraper
        if lender.slug in self._custom_scrapers:
            scraper_class = self._custom_scrapers[lender.slug]
            scraper = scraper_class(lender.slug)
        else:
            # Use generic scraper
            scraper = GenericScraper(
                lender_slug=lender.slug,
                website_url=lender.website_url,
                rates_url=lender.rates_page_url,
            )

        # Execute scrape
        with scraper:
            result = scraper.scrape()

        # Detect changes
        changes = []
        if result.success:
            changes = self.change_detector.detect_changes(lender, result)

            # Apply changes if requested
            if auto_apply_changes and changes:
                self.change_detector.apply_changes(changes, auto_apply=True)

        # Record scrape
        self.change_detector.record_scrape(lender, result, changes)

        return result, changes

    def scrape_all(
        self,
        force: bool = False,
        auto_apply_changes: bool = False,
    ) -> ScrapeSummary:
        """
        Scrape all lenders due for scraping.

        Args:
            force: If True, scrape all lenders regardless of last scrape time
            auto_apply_changes: Whether to automatically apply detected changes

        Returns:
            ScrapeSummary with results
        """
        timestamp = datetime.utcnow()

        if force:
            lenders = (
                self.db.query(Lender)
                .filter(Lender.status == LenderStatus.ACTIVE)
                .filter(Lender.website_url != None)
                .all()
            )
        else:
            lenders = self.get_lenders_due_for_scrape()

        lenders_scraped = 0
        lenders_failed = 0
        total_changes = 0
        critical_changes = 0
        errors = []

        for lender in lenders:
            try:
                print(f"Scraping {lender.name}...")
                result, changes = self.scrape_lender(lender, auto_apply_changes)

                if result.success:
                    lenders_scraped += 1
                    total_changes += len(changes)
                    critical_changes += sum(1 for c in changes if c.significance == "critical")
                else:
                    lenders_failed += 1
                    errors.append(f"{lender.name}: {result.error_message}")

            except Exception as e:
                lenders_failed += 1
                errors.append(f"{lender.name}: {str(e)}")

        return ScrapeSummary(
            timestamp=timestamp,
            lenders_scraped=lenders_scraped,
            lenders_failed=lenders_failed,
            total_changes=total_changes,
            critical_changes=critical_changes,
            errors=errors,
        )

    def scrape_by_slug(
        self,
        slug: str,
        auto_apply_changes: bool = False
    ) -> Optional[tuple[ScrapeResult, List[DetectedChange]]]:
        """Scrape a specific lender by slug."""
        lender = (
            self.db.query(Lender)
            .filter(Lender.slug == slug)
            .first()
        )

        if not lender:
            return None

        return self.scrape_lender(lender, auto_apply_changes)

    def get_scrape_status(self) -> Dict:
        """Get overall scraping status."""
        total_lenders = (
            self.db.query(Lender)
            .filter(Lender.status == LenderStatus.ACTIVE)
            .filter(Lender.website_url != None)
            .count()
        )

        due_for_scrape = len(self.get_lenders_due_for_scrape())

        # Get recent scrape stats
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        from app.models.scrape_history import ScrapeHistory, ScrapeStatus

        recent_scrapes = (
            self.db.query(ScrapeHistory)
            .filter(ScrapeHistory.created_at >= recent_cutoff)
            .all()
        )

        successful = sum(1 for s in recent_scrapes if s.status == ScrapeStatus.SUCCESS)
        failed = sum(1 for s in recent_scrapes if s.status == ScrapeStatus.FAILED)

        return {
            "total_lenders": total_lenders,
            "due_for_scrape": due_for_scrape,
            "scrape_interval_days": self.settings.scrape_interval_days,
            "recent_scrapes": {
                "total": len(recent_scrapes),
                "successful": successful,
                "failed": failed,
            },
        }
