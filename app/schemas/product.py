"""Pydantic schemas for product operations."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.product import FinanceType, PropertyType


class ProductCriteriaCreate(BaseModel):
    """Schema for creating product criteria."""
    min_experience_units: Optional[int] = None
    accepts_first_time_developers: Optional[bool] = None
    accepts_foreign_nationals: Optional[bool] = None
    accepts_spv: Optional[bool] = None
    accepts_ltd_company: Optional[bool] = None
    accepts_llp: Optional[bool] = None
    accepts_individuals: Optional[bool] = None
    accepts_pension_funds: Optional[bool] = None
    min_units: Optional[int] = None
    max_units: Optional[int] = None
    min_gdv: Optional[int] = None
    max_gdv: Optional[int] = None
    excluded_postcodes: Optional[List[str]] = None
    excluded_regions: Optional[List[str]] = None
    requires_personal_guarantee: Optional[bool] = None
    pg_percentage: Optional[float] = None
    requires_debenture: Optional[bool] = None
    accepts_no_planning: Optional[bool] = None
    accepts_outline_planning: Optional[bool] = None
    accepts_full_planning: Optional[bool] = None
    accepts_permitted_development: Optional[bool] = None
    additional_criteria: Optional[dict] = None
    criteria_notes: Optional[str] = None


class ProductCriteriaResponse(BaseModel):
    """Schema for product criteria response."""
    id: int
    min_experience_units: Optional[int]
    accepts_first_time_developers: Optional[bool]
    accepts_foreign_nationals: Optional[bool]
    accepts_spv: Optional[bool]
    accepts_ltd_company: Optional[bool]
    accepts_llp: Optional[bool]
    accepts_individuals: Optional[bool]
    accepts_pension_funds: Optional[bool]
    min_units: Optional[int]
    max_units: Optional[int]
    min_gdv: Optional[int]
    max_gdv: Optional[int]
    excluded_postcodes: Optional[List[str]]
    excluded_regions: Optional[List[str]]
    requires_personal_guarantee: Optional[bool]
    pg_percentage: Optional[float]
    requires_debenture: Optional[bool]
    accepts_no_planning: Optional[bool]
    accepts_outline_planning: Optional[bool]
    accepts_full_planning: Optional[bool]
    accepts_permitted_development: Optional[bool]
    additional_criteria: Optional[dict]
    criteria_notes: Optional[str]

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str = Field(..., min_length=1, max_length=255)
    finance_type: FinanceType
    description: Optional[str] = None
    rate_from: Optional[float] = None
    rate_to: Optional[float] = None
    rate_type: Optional[str] = None
    arrangement_fee_percent: Optional[float] = None
    arrangement_fee_min: Optional[int] = None
    exit_fee_percent: Optional[float] = None
    valuation_fee: Optional[str] = None
    legal_fee: Optional[str] = None
    min_loan: Optional[int] = None
    max_loan: Optional[int] = None
    max_ltv: Optional[float] = None
    max_ltc: Optional[float] = None
    max_ltgdv: Optional[float] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    property_types: Optional[List[str]] = None
    geographic_areas: Optional[List[str]] = None
    source_url: Optional[str] = None
    criteria: Optional[ProductCriteriaCreate] = None


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    finance_type: Optional[FinanceType] = None
    description: Optional[str] = None
    rate_from: Optional[float] = None
    rate_to: Optional[float] = None
    rate_type: Optional[str] = None
    arrangement_fee_percent: Optional[float] = None
    arrangement_fee_min: Optional[int] = None
    exit_fee_percent: Optional[float] = None
    valuation_fee: Optional[str] = None
    legal_fee: Optional[str] = None
    min_loan: Optional[int] = None
    max_loan: Optional[int] = None
    max_ltv: Optional[float] = None
    max_ltc: Optional[float] = None
    max_ltgdv: Optional[float] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    property_types: Optional[List[str]] = None
    geographic_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    source_url: Optional[str] = None


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    lender_id: int
    name: str
    slug: str
    finance_type: FinanceType
    description: Optional[str]
    rate_from: Optional[float]
    rate_to: Optional[float]
    rate_type: Optional[str]
    arrangement_fee_percent: Optional[float]
    arrangement_fee_min: Optional[int]
    exit_fee_percent: Optional[float]
    valuation_fee: Optional[str]
    legal_fee: Optional[str]
    min_loan: Optional[int]
    max_loan: Optional[int]
    max_ltv: Optional[float]
    max_ltc: Optional[float]
    max_ltgdv: Optional[float]
    min_term_months: Optional[int]
    max_term_months: Optional[int]
    property_types: Optional[List[str]]
    geographic_areas: Optional[List[str]]
    is_active: bool
    is_featured: bool
    source_url: Optional[str]
    last_verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    criteria: Optional[ProductCriteriaResponse] = None

    class Config:
        from_attributes = True


class ProductSearchParams(BaseModel):
    """Parameters for searching products."""
    finance_type: Optional[FinanceType] = None
    property_type: Optional[str] = None
    min_loan: Optional[int] = None
    max_loan: Optional[int] = None
    loan_amount: Optional[int] = None
    ltv: Optional[float] = None
    region: Optional[str] = None
    accepts_first_time: Optional[bool] = None
    lender_type: Optional[str] = None
    max_rate: Optional[float] = None
    page: int = 1
    page_size: int = 20


class ProductComparisonResponse(BaseModel):
    """Response for product comparison."""
    products: List[ProductResponse]
    comparison_metrics: dict
