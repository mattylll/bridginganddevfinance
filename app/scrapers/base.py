"""
Base Scraper Class

Provides foundation for building lender-specific scrapers.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings


@dataclass
class ScrapedProduct:
    """Data structure for a scraped product."""
    name: str
    finance_type: str
    rate_from: Optional[float] = None
    rate_to: Optional[float] = None
    rate_type: Optional[str] = None  # 'monthly' or 'annual'
    arrangement_fee_percent: Optional[float] = None
    exit_fee_percent: Optional[float] = None
    max_ltv: Optional[float] = None
    max_ltc: Optional[float] = None
    max_ltgdv: Optional[float] = None
    min_loan: Optional[int] = None
    max_loan: Optional[int] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    property_types: List[str] = field(default_factory=list)
    description: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapeResult:
    """Result of a scrape operation."""
    success: bool
    lender_slug: str
    timestamp: datetime
    products: List[ScrapedProduct] = field(default_factory=list)
    urls_scraped: List[str] = field(default_factory=list)
    content_hash: Optional[str] = None
    error_message: Optional[str] = None
    raw_html: Optional[str] = None


class BaseScraper(ABC):
    """
    Base class for lender-specific scrapers.

    Each lender needs its own scraper implementation because
    website structures vary significantly.
    """

    def __init__(self, lender_slug: str):
        self.lender_slug = lender_slug
        self.settings = get_settings()
        self.client = httpx.Client(
            headers={
                "User-Agent": self.settings.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
            },
            follow_redirects=True,
            timeout=30.0,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the lender's website."""
        pass

    @property
    @abstractmethod
    def rates_urls(self) -> List[str]:
        """URLs to scrape for rate information."""
        pass

    @abstractmethod
    def parse_products(self, soup: BeautifulSoup, url: str) -> List[ScrapedProduct]:
        """
        Parse products from a page.

        Args:
            soup: BeautifulSoup object of the page
            url: URL of the page

        Returns:
            List of scraped products
        """
        pass

    def scrape(self) -> ScrapeResult:
        """
        Execute the scrape for this lender.

        Returns:
            ScrapeResult with all scraped data
        """
        timestamp = datetime.utcnow()
        all_products = []
        urls_scraped = []
        all_html = []

        try:
            for url in self.rates_urls:
                html = self._fetch_page(url)
                if html:
                    all_html.append(html)
                    urls_scraped.append(url)

                    soup = BeautifulSoup(html, "lxml")
                    products = self.parse_products(soup, url)
                    all_products.extend(products)

            # Calculate content hash for change detection
            combined_html = "\n".join(all_html)
            content_hash = hashlib.sha256(combined_html.encode()).hexdigest()

            return ScrapeResult(
                success=True,
                lender_slug=self.lender_slug,
                timestamp=timestamp,
                products=all_products,
                urls_scraped=urls_scraped,
                content_hash=content_hash,
                raw_html=combined_html if len(combined_html) < 500000 else None,
            )

        except Exception as e:
            return ScrapeResult(
                success=False,
                lender_slug=self.lender_slug,
                timestamp=timestamp,
                error_message=str(e),
            )

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page and return HTML content."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _extract_rate(self, text: str) -> Optional[float]:
        """Extract a rate from text like '0.75%' or '7.5%'."""
        import re
        match = re.search(r"(\d+\.?\d*)%", text)
        if match:
            return float(match.group(1))
        return None

    def _extract_amount(self, text: str) -> Optional[int]:
        """Extract an amount from text like '£500,000' or '£5m'."""
        import re

        # Handle millions (e.g., '£5m', '£5 million')
        match = re.search(r"£(\d+\.?\d*)\s*m", text.lower())
        if match:
            return int(float(match.group(1)) * 1_000_000)

        # Handle thousands (e.g., '£500k')
        match = re.search(r"£(\d+\.?\d*)\s*k", text.lower())
        if match:
            return int(float(match.group(1)) * 1_000)

        # Handle regular amounts (e.g., '£500,000')
        match = re.search(r"£([\d,]+)", text)
        if match:
            return int(match.group(1).replace(",", ""))

        return None

    def _clean_text(self, text: str) -> str:
        """Clean whitespace from text."""
        return " ".join(text.split())


class GenericScraper(BaseScraper):
    """
    Generic scraper that can work with any lender.

    Uses heuristics to find rate information on pages.
    Less accurate than custom scrapers but works as a fallback.
    """

    def __init__(self, lender_slug: str, website_url: str, rates_url: Optional[str] = None):
        super().__init__(lender_slug)
        self._base_url = website_url
        self._rates_urls = [rates_url] if rates_url else [website_url]

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def rates_urls(self) -> List[str]:
        return self._rates_urls

    def parse_products(self, soup: BeautifulSoup, url: str) -> List[ScrapedProduct]:
        """
        Generic parsing using heuristics.

        Looks for common patterns in rate pages.
        """
        products = []

        # Look for tables with rate information
        tables = soup.find_all("table")
        for table in tables:
            product = self._parse_rate_table(table, url)
            if product:
                products.append(product)

        # Look for common product sections
        sections = soup.find_all(["div", "section"], class_=lambda x: x and any(
            term in str(x).lower() for term in ["product", "rate", "loan", "bridging", "development"]
        ))

        for section in sections:
            product = self._parse_product_section(section, url)
            if product:
                products.append(product)

        return products

    def _parse_rate_table(self, table, url: str) -> Optional[ScrapedProduct]:
        """Parse a rate table."""
        text = table.get_text()

        # Look for rate patterns
        rate = self._extract_rate(text)
        if not rate:
            return None

        # Try to identify product name
        headers = table.find_all(["th", "caption"])
        name = "Unknown Product"
        if headers:
            name = self._clean_text(headers[0].get_text())

        return ScrapedProduct(
            name=name,
            finance_type="bridging",  # Default
            rate_from=rate,
            source_url=url,
            raw_data={"table_html": str(table)[:1000]},
        )

    def _parse_product_section(self, section, url: str) -> Optional[ScrapedProduct]:
        """Parse a product section."""
        text = section.get_text()

        # Look for rate patterns
        rate = self._extract_rate(text)
        if not rate:
            return None

        # Try to identify finance type
        finance_type = "bridging"
        text_lower = text.lower()
        if "development" in text_lower:
            finance_type = "development"
        elif "mezzanine" in text_lower:
            finance_type = "mezzanine"

        # Try to find product name
        heading = section.find(["h1", "h2", "h3", "h4"])
        name = self._clean_text(heading.get_text()) if heading else "Unknown Product"

        return ScrapedProduct(
            name=name,
            finance_type=finance_type,
            rate_from=rate,
            max_loan=self._extract_amount(text),
            source_url=url,
        )
