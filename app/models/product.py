"""Product and finance type database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FinanceType(enum.Enum):
    """Types of development finance."""
    BRIDGING = "bridging"
    DEVELOPMENT = "development"
    MEZZANINE = "mezzanine"
    EQUITY = "equity"
    JOINT_VENTURE = "joint_venture"
    DEVELOPER_EXIT = "developer_exit"
    REFURBISHMENT = "refurbishment"
    AUCTION = "auction"
    LAND = "land"
    STRETCH_SENIOR = "stretch_senior"


class PropertyType(enum.Enum):
    """Types of property/development."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    STUDENT = "student"
    HMO = "hmo"
    BTR = "build_to_rent"
    CARE_HOME = "care_home"
    HOTEL = "hotel"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    OFFICE = "office"
    LAND = "land"


class Product(Base):
    """
    Financial product offered by a lender.

    Each lender can offer multiple products across different finance types.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Product Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    finance_type = Column(SQLEnum(FinanceType), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Rates
    rate_from = Column(Float, nullable=True)  # Annual rate as percentage (e.g., 0.75 for 0.75% pm)
    rate_to = Column(Float, nullable=True)
    rate_type = Column(String(50), nullable=True)  # 'monthly', 'annual', 'variable', 'fixed'

    # Fees
    arrangement_fee_percent = Column(Float, nullable=True)  # As percentage
    arrangement_fee_min = Column(Integer, nullable=True)  # Minimum fee in GBP
    exit_fee_percent = Column(Float, nullable=True)
    valuation_fee = Column(String(100), nullable=True)  # Can be 'included', amount, or 'at cost'
    legal_fee = Column(String(100), nullable=True)

    # Loan Parameters
    min_loan = Column(Integer, nullable=True)  # GBP
    max_loan = Column(Integer, nullable=True)  # GBP
    max_ltv = Column(Float, nullable=True)  # As percentage (e.g., 75.0)
    max_ltc = Column(Float, nullable=True)  # Loan to Cost
    max_ltgdv = Column(Float, nullable=True)  # Loan to GDV

    # Term
    min_term_months = Column(Integer, nullable=True)
    max_term_months = Column(Integer, nullable=True)

    # Property Types Supported (JSON array)
    property_types = Column(JSON, nullable=True)

    # Geographic Coverage (JSON array of regions)
    geographic_areas = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Source Information
    source_url = Column(String(500), nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", back_populates="products")
    criteria = relationship("ProductCriteria", back_populates="product", uselist=False, cascade="all, delete-orphan")
    geographic_pricing = relationship("GeographicPricing", back_populates="product", cascade="all, delete-orphan")
    type_pricing = relationship("ProductTypePricing", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', type={self.finance_type.value})>"


class ProductCriteria(Base):
    """
    Detailed lending criteria for a product.

    This captures the specific requirements and restrictions for each product.
    """
    __tablename__ = "product_criteria"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)

    # Borrower Requirements
    min_experience_units = Column(Integer, nullable=True)  # Number of completed projects
    accepts_first_time_developers = Column(Boolean, nullable=True)
    accepts_foreign_nationals = Column(Boolean, nullable=True)
    accepts_spv = Column(Boolean, nullable=True)  # Special Purpose Vehicle
    accepts_ltd_company = Column(Boolean, nullable=True)
    accepts_llp = Column(Boolean, nullable=True)
    accepts_individuals = Column(Boolean, nullable=True)
    accepts_pension_funds = Column(Boolean, nullable=True)

    # Property Requirements
    min_units = Column(Integer, nullable=True)
    max_units = Column(Integer, nullable=True)
    min_gdv = Column(Integer, nullable=True)
    max_gdv = Column(Integer, nullable=True)

    # Location Restrictions
    excluded_postcodes = Column(JSON, nullable=True)
    excluded_regions = Column(JSON, nullable=True)

    # Security Requirements
    requires_personal_guarantee = Column(Boolean, nullable=True)
    pg_percentage = Column(Float, nullable=True)
    requires_debenture = Column(Boolean, nullable=True)

    # Planning Status
    accepts_no_planning = Column(Boolean, nullable=True)
    accepts_outline_planning = Column(Boolean, nullable=True)
    accepts_full_planning = Column(Boolean, nullable=True)
    accepts_permitted_development = Column(Boolean, nullable=True)

    # Additional Criteria (flexible JSON for lender-specific fields)
    additional_criteria = Column(JSON, nullable=True)

    # Notes
    criteria_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="criteria")

    def __repr__(self):
        return f"<ProductCriteria(id={self.id}, product_id={self.product_id})>"


class GeographicPricing(Base):
    """
    Geographic-specific pricing adjustments for a product.

    Allows lenders to offer different rates in different regions.
    Phase 2 feature - lenders can set these via portal.
    """
    __tablename__ = "geographic_pricing"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Region (could be postcode prefix, region name, or specific area)
    region_type = Column(String(50), nullable=False)  # 'postcode', 'region', 'county'
    region_value = Column(String(100), nullable=False)  # e.g., 'SW', 'London', 'Greater Manchester'

    # Rate Adjustment
    rate_adjustment = Column(Float, nullable=False)  # +/- percentage points

    # Validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # 'system' or lender user ID

    # Relationships
    product = relationship("Product", back_populates="geographic_pricing")

    def __repr__(self):
        return f"<GeographicPricing(product_id={self.product_id}, region='{self.region_value}', adj={self.rate_adjustment})>"


class ProductTypePricing(Base):
    """
    Property type-specific pricing adjustments for a product.

    Allows lenders to offer different rates for different development types.
    Phase 2 feature - lenders can set these via portal.
    """
    __tablename__ = "product_type_pricing"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Property Type
    property_type = Column(SQLEnum(PropertyType), nullable=False)

    # Rate Adjustment
    rate_adjustment = Column(Float, nullable=False)  # +/- percentage points

    # LTV Adjustment (some lenders offer higher LTV for certain types)
    ltv_adjustment = Column(Float, nullable=True)

    # Validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="type_pricing")

    def __repr__(self):
        return f"<ProductTypePricing(product_id={self.product_id}, type={self.property_type.value}, adj={self.rate_adjustment})>"
