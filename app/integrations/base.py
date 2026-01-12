"""
Base Lender API Integration

Abstract base class for all lender API integrations.
Each lender with an API gets their own implementation.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import httpx


class QuoteStatus(Enum):
    """Status of a quote request."""
    SUCCESS = "success"
    DECLINED = "declined"
    REFER = "refer"
    ERROR = "error"
    OUTSIDE_CRITERIA = "outside_criteria"


@dataclass
class QuoteRequest:
    """
    Standardised quote request across all lender APIs.

    Each lender integration maps this to their specific API format.
    """
    # Loan Details
    loan_amount: int
    loan_purpose: str  # "purchase", "refinance", "equity_release", "development"
    term_months: int

    # Property Details
    property_value: Optional[int] = None
    purchase_price: Optional[int] = None
    property_type: str = "residential"  # "residential", "commercial", "mixed", "land"
    property_postcode: Optional[str] = None
    property_address: Optional[str] = None

    # Development Specific
    gdv: Optional[int] = None
    build_costs: Optional[int] = None
    current_value: Optional[int] = None

    # Borrower Details
    borrower_type: str = "individual"  # "individual", "spv", "ltd", "llp"
    experience_projects: Optional[int] = None
    is_first_time_developer: bool = False

    # Planning (for development)
    planning_status: Optional[str] = None  # "none", "outline", "full", "permitted_development"

    # Exit Strategy
    exit_strategy: Optional[str] = None  # "sale", "refinance", "term_loan"

    # Additional Info
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateQuote:
    """Individual rate option returned by a lender."""
    rate: float
    rate_type: str  # "monthly" or "annual"
    max_ltv: Optional[float] = None
    max_ltc: Optional[float] = None
    max_ltgdv: Optional[float] = None
    arrangement_fee_percent: Optional[float] = None
    arrangement_fee_amount: Optional[int] = None
    exit_fee_percent: Optional[float] = None
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class QuoteResponse:
    """
    Standardised quote response from lender APIs.
    """
    status: QuoteStatus
    lender_name: str
    lender_id: int

    # Timestamp
    quoted_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None

    # Quote Details
    quotes: List[RateQuote] = field(default_factory=list)
    best_rate: Optional[float] = None
    max_loan_offered: Optional[int] = None

    # If declined/referred
    decline_reason: Optional[str] = None
    refer_reason: Optional[str] = None

    # Raw response for debugging
    raw_response: Optional[Dict[str, Any]] = None

    # Error info
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class BaseLenderAPI(ABC):
    """
    Abstract base class for lender API integrations.

    Each lender needs their own implementation that:
    1. Maps QuoteRequest to their API format
    2. Calls their API
    3. Maps response back to QuoteResponse
    """

    def __init__(self, lender_id: int, lender_name: str):
        self.lender_id = lender_id
        self.lender_name = lender_name
        self._client: Optional[httpx.AsyncClient] = None

    @property
    @abstractmethod
    def api_base_url(self) -> str:
        """Base URL for the lender's API."""
        pass

    @property
    @abstractmethod
    def api_key_env_var(self) -> str:
        """Environment variable name containing API key."""
        pass

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment."""
        return os.getenv(self.api_key_env_var)

    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured."""
        return self.api_key is not None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers=self._get_auth_headers(),
                timeout=30.0,
            )
        return self._client

    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls."""
        pass

    @abstractmethod
    async def get_indicative_quote(self, request: QuoteRequest) -> QuoteResponse:
        """
        Get an indicative quote from this lender.

        Args:
            request: Standardised quote request

        Returns:
            QuoteResponse with rates or decline reason
        """
        pass

    @abstractmethod
    async def check_eligibility(self, request: QuoteRequest) -> bool:
        """
        Quick eligibility check before full quote.

        Args:
            request: Quote request to check

        Returns:
            True if likely eligible, False otherwise
        """
        pass

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def __repr__(self):
        return f"<{self.__class__.__name__}(lender={self.lender_name}, configured={self.is_configured})>"
