"""Pydantic schemas for loan search and matching."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.product import FinanceType, PropertyType
from app.schemas.lender import LenderSummary


class LoanSearchRequest(BaseModel):
    """
    Request schema for searching/matching loans.

    This represents a deal that needs financing.
    """
    # Deal Type
    finance_type: FinanceType = Field(..., description="Type of finance required")
    property_type: Optional[str] = Field(None, description="Type of property/development")

    # Location
    postcode: Optional[str] = Field(None, description="Property postcode")
    region: Optional[str] = Field(None, description="Region name")

    # Loan Requirements
    loan_amount: int = Field(..., gt=0, description="Loan amount required in GBP")
    property_value: Optional[int] = Field(None, description="Current property value")
    purchase_price: Optional[int] = Field(None, description="Purchase price if acquiring")
    development_costs: Optional[int] = Field(None, description="Total development costs")
    gdv: Optional[int] = Field(None, description="Gross Development Value")

    # Calculated Metrics (optional - will be calculated if not provided)
    ltv: Optional[float] = Field(None, description="Loan to Value percentage")
    ltc: Optional[float] = Field(None, description="Loan to Cost percentage")
    ltgdv: Optional[float] = Field(None, description="Loan to GDV percentage")

    # Term
    term_months: Optional[int] = Field(None, description="Required term in months")

    # Borrower Profile
    borrower_type: Optional[str] = Field(None, description="individual, ltd, spv, llp")
    experience_level: Optional[int] = Field(None, description="Number of completed projects")
    is_first_time_developer: bool = Field(False, description="First time developer?")
    is_foreign_national: bool = Field(False, description="Non-UK national?")

    # Planning Status (for development)
    planning_status: Optional[str] = Field(
        None,
        description="none, outline, full, permitted_development"
    )

    # Preferences
    max_rate: Optional[float] = Field(None, description="Maximum acceptable rate")
    preferred_lender_types: Optional[List[str]] = Field(None, description="Preferred lender types")

    # Search Options
    include_inactive: bool = Field(False, description="Include inactive products")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")


class MatchScore(BaseModel):
    """Breakdown of how well a product matches the search criteria."""
    overall: float = Field(..., ge=0, le=100, description="Overall match score 0-100")
    rate_score: float = Field(..., ge=0, le=100)
    ltv_score: float = Field(..., ge=0, le=100)
    criteria_score: float = Field(..., ge=0, le=100)
    lender_rating_score: float = Field(..., ge=0, le=100)


class MatchedProduct(BaseModel):
    """A product matched to a loan search."""
    # Product Details
    product_id: int
    product_name: str
    finance_type: FinanceType

    # Lender Details
    lender_id: int
    lender_name: str
    lender_type: str

    # Rates
    rate_from: Optional[float]
    rate_to: Optional[float]
    rate_type: Optional[str]
    effective_rate: Optional[float]  # After any geographic/type adjustments

    # Fees
    arrangement_fee_percent: Optional[float]
    exit_fee_percent: Optional[float]
    total_cost_estimate: Optional[float]  # Estimated total cost over term

    # Limits
    max_ltv: Optional[float]
    max_ltc: Optional[float]
    max_ltgdv: Optional[float]
    max_loan: Optional[int]

    # Match Analysis
    match_score: MatchScore
    matches_criteria: bool
    criteria_issues: List[str] = []  # Any criteria not met
    criteria_warnings: List[str] = []  # Things to be aware of

    # Lender Ratings
    lender_overall_rating: Optional[float]
    lender_speed_rating: Optional[float]

    # Source
    source_url: Optional[str]
    last_verified_at: Optional[datetime]


class LoanSearchResponse(BaseModel):
    """Response from a loan search."""
    # Search Summary
    search_id: str
    search_timestamp: datetime
    total_matches: int
    filters_applied: dict

    # Results
    matches: List[MatchedProduct]

    # Aggregated Stats
    rate_range: dict  # min, max, average
    lender_count: int
    product_count: int

    # Recommendations
    best_rate: Optional[MatchedProduct] = None
    best_match: Optional[MatchedProduct] = None
    fastest_lender: Optional[MatchedProduct] = None


class QuickQuoteRequest(BaseModel):
    """Simplified search for quick quotes."""
    finance_type: FinanceType
    loan_amount: int
    property_value: Optional[int] = None
    gdv: Optional[int] = None
    postcode: Optional[str] = None
    is_first_time: bool = False


class QuickQuoteResponse(BaseModel):
    """Quick quote response."""
    indicative_rate_from: Optional[float]
    indicative_rate_to: Optional[float]
    available_lenders: int
    best_ltv_available: Optional[float]
    message: str
