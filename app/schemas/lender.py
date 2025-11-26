"""Pydantic schemas for lender operations."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl

from app.models.lender import LenderStatus, LenderType


class LenderContactCreate(BaseModel):
    """Schema for creating a lender contact."""
    contact_type: str = Field(..., description="Type: broker_desk, general, bdm")
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    region: Optional[str] = None
    is_primary: bool = False


class LenderContactResponse(BaseModel):
    """Schema for lender contact response."""
    id: int
    contact_type: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    region: Optional[str]
    is_primary: bool

    class Config:
        from_attributes = True


class LenderCreate(BaseModel):
    """Schema for creating a new lender."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    lender_type: LenderType
    website_url: Optional[str] = None
    rates_page_url: Optional[str] = None
    criteria_page_url: Optional[str] = None
    fca_number: Optional[str] = None
    is_fca_regulated: bool = True
    founded_year: Optional[int] = None
    headquarters_location: Optional[str] = None
    min_loan_amount: Optional[int] = None
    max_loan_amount: Optional[int] = None
    geographic_coverage: Optional[List[str]] = None
    contacts: Optional[List[LenderContactCreate]] = None


class LenderUpdate(BaseModel):
    """Schema for updating a lender."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    lender_type: Optional[LenderType] = None
    status: Optional[LenderStatus] = None
    website_url: Optional[str] = None
    rates_page_url: Optional[str] = None
    criteria_page_url: Optional[str] = None
    fca_number: Optional[str] = None
    is_fca_regulated: Optional[bool] = None
    founded_year: Optional[int] = None
    headquarters_location: Optional[str] = None
    min_loan_amount: Optional[int] = None
    max_loan_amount: Optional[int] = None
    geographic_coverage: Optional[List[str]] = None


class LenderResponse(BaseModel):
    """Schema for lender response."""
    id: int
    name: str
    slug: str
    description: Optional[str]
    lender_type: LenderType
    status: LenderStatus
    website_url: Optional[str]
    rates_page_url: Optional[str]
    criteria_page_url: Optional[str]
    fca_number: Optional[str]
    is_fca_regulated: bool
    founded_year: Optional[int]
    headquarters_location: Optional[str]
    min_loan_amount: Optional[int]
    max_loan_amount: Optional[int]
    geographic_coverage: Optional[List[str]]
    contacts: List[LenderContactResponse] = []
    created_at: datetime
    updated_at: datetime
    last_scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class LenderListResponse(BaseModel):
    """Schema for paginated lender list."""
    items: List[LenderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LenderSummary(BaseModel):
    """Brief lender summary for search results."""
    id: int
    name: str
    slug: str
    lender_type: LenderType
    min_loan_amount: Optional[int]
    max_loan_amount: Optional[int]

    class Config:
        from_attributes = True
