"""
Lender Integration Models

Handles both API-based integrations and manual term sheet data.
Each lender's actual terms are stored exactly as they provide them.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SQLEnum, JSON, Date
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class IntegrationType(enum.Enum):
    """How we get data from this lender."""
    API = "api"                    # Real-time API integration
    TERM_SHEET = "term_sheet"      # Manual term sheet entry
    SCRAPE = "scrape"              # Web scraping (less reliable)
    HYBRID = "hybrid"              # API + manual for some products


class DataFreshness(enum.Enum):
    """How fresh/reliable is this data."""
    REAL_TIME = "real_time"        # From API, current
    CURRENT = "current"            # Manual entry, verified recently
    STALE = "stale"                # Needs re-verification
    UNKNOWN = "unknown"            # Not verified


class LenderIntegration(Base):
    """
    Tracks how we integrate with each lender for data.

    Some lenders have APIs (LendInvest), others we need to
    manually enter their term sheet data.
    """
    __tablename__ = "lender_integrations"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False, unique=True)

    # Integration Type
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)

    # API Configuration (if API type)
    api_base_url = Column(String(500), nullable=True)
    api_version = Column(String(50), nullable=True)
    api_key_name = Column(String(100), nullable=True)  # Name of env var holding API key
    api_auth_type = Column(String(50), nullable=True)  # 'bearer', 'api_key', 'oauth2'
    api_documentation_url = Column(String(500), nullable=True)

    # API Capabilities
    supports_indicative_quote = Column(Boolean, default=False)
    supports_full_application = Column(Boolean, default=False)
    supports_document_upload = Column(Boolean, default=False)
    supports_status_check = Column(Boolean, default=False)

    # Rate Limits
    rate_limit_requests = Column(Integer, nullable=True)  # requests per minute
    rate_limit_window = Column(Integer, nullable=True)    # window in seconds

    # Status
    is_active = Column(Boolean, default=True)
    last_successful_call = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Contact for integration issues
    technical_contact_email = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", backref="integration")

    def __repr__(self):
        return f"<LenderIntegration(lender_id={self.lender_id}, type={self.integration_type.value})>"


class TermSheet(Base):
    """
    A term sheet from a lender - their actual published terms.

    This is the source of truth for non-API lenders. Each term sheet
    is dated and versioned so we know exactly when it was valid.
    """
    __tablename__ = "term_sheets"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Term Sheet Identity
    name = Column(String(255), nullable=False)  # e.g., "Bridging Rate Card Q1 2024"
    version = Column(String(50), nullable=True)  # e.g., "v2.1"

    # Validity Period
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)  # Null if current
    is_current = Column(Boolean, default=True)

    # Source
    source_document_url = Column(String(500), nullable=True)  # Link to PDF/document
    source_document_hash = Column(String(64), nullable=True)   # SHA256 of document
    received_from = Column(String(255), nullable=True)         # Who provided it
    received_date = Column(Date, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Verification
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", backref="term_sheets")
    rate_cards = relationship("RateCard", back_populates="term_sheet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TermSheet(id={self.id}, lender_id={self.lender_id}, name='{self.name}')>"


class RateCard(Base):
    """
    Specific rate card from a term sheet.

    A term sheet may have multiple rate cards for different:
    - Finance types (bridging, development)
    - Property types (residential, commercial)
    - Loan sizes
    - LTV bands
    """
    __tablename__ = "rate_cards"

    id = Column(Integer, primary_key=True, index=True)
    term_sheet_id = Column(Integer, ForeignKey("term_sheets.id"), nullable=False)

    # Product Identification
    product_name = Column(String(255), nullable=False)
    finance_type = Column(String(50), nullable=False)  # bridging, development, etc.

    # Applicability Criteria
    property_types = Column(JSON, nullable=True)       # ["residential", "commercial"]
    loan_purposes = Column(JSON, nullable=True)        # ["purchase", "refinance", "equity_release"]
    borrower_types = Column(JSON, nullable=True)       # ["individual", "spv", "ltd"]

    # Geographic Applicability
    regions_included = Column(JSON, nullable=True)     # Regions where this applies
    regions_excluded = Column(JSON, nullable=True)     # Regions excluded
    postcodes_excluded = Column(JSON, nullable=True)   # Specific postcodes excluded

    # Loan Parameters
    min_loan = Column(Integer, nullable=True)
    max_loan = Column(Integer, nullable=True)
    min_term_months = Column(Integer, nullable=True)
    max_term_months = Column(Integer, nullable=True)

    # This card is active
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    term_sheet = relationship("TermSheet", back_populates="rate_cards")
    rate_tiers = relationship("RateTier", back_populates="rate_card", cascade="all, delete-orphan")
    fee_structure = relationship("FeeStructure", back_populates="rate_card", uselist=False, cascade="all, delete-orphan")
    lending_criteria = relationship("LendingCriteria", back_populates="rate_card", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RateCard(id={self.id}, product='{self.product_name}', type={self.finance_type})>"


class RateTier(Base):
    """
    Individual rate tier within a rate card.

    Rates typically vary by LTV band - this captures exactly
    what the lender publishes.

    Example:
    - 0-50% LTV: 0.55% pm
    - 50-60% LTV: 0.65% pm
    - 60-70% LTV: 0.75% pm
    - 70-75% LTV: 0.89% pm
    """
    __tablename__ = "rate_tiers"

    id = Column(Integer, primary_key=True, index=True)
    rate_card_id = Column(Integer, ForeignKey("rate_cards.id"), nullable=False)

    # LTV Band
    ltv_from = Column(Float, nullable=True)   # e.g., 0
    ltv_to = Column(Float, nullable=True)     # e.g., 50

    # LTC Band (for development)
    ltc_from = Column(Float, nullable=True)
    ltc_to = Column(Float, nullable=True)

    # LTGDV Band (for development)
    ltgdv_from = Column(Float, nullable=True)
    ltgdv_to = Column(Float, nullable=True)

    # Loan Size Band
    loan_from = Column(Integer, nullable=True)
    loan_to = Column(Integer, nullable=True)

    # The Rate
    rate = Column(Float, nullable=False)      # The actual rate
    rate_type = Column(String(20), nullable=False)  # 'monthly' or 'annual'
    is_fixed = Column(Boolean, default=True)

    # If variable, what's it linked to
    base_rate_reference = Column(String(100), nullable=True)  # e.g., "Bank of England Base Rate"
    margin_over_base = Column(Float, nullable=True)           # e.g., 5.5 (meaning base + 5.5%)

    # Day 1 vs Rolled Up
    day_one_rate = Column(Float, nullable=True)      # If different rate for day 1 lending
    rolled_up_rate = Column(Float, nullable=True)    # Rate if interest rolled up

    # Notes
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    rate_card = relationship("RateCard", back_populates="rate_tiers")

    def __repr__(self):
        return f"<RateTier(rate_card_id={self.rate_card_id}, ltv={self.ltv_from}-{self.ltv_to}%, rate={self.rate}%)>"


class FeeStructure(Base):
    """
    Fee structure for a rate card - exactly as lender publishes.
    """
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    rate_card_id = Column(Integer, ForeignKey("rate_cards.id"), nullable=False, unique=True)

    # Arrangement Fee
    arrangement_fee_type = Column(String(20), nullable=True)  # 'percentage', 'fixed', 'tiered'
    arrangement_fee_percent = Column(Float, nullable=True)
    arrangement_fee_min = Column(Integer, nullable=True)
    arrangement_fee_max = Column(Integer, nullable=True)
    arrangement_fee_notes = Column(Text, nullable=True)

    # Exit Fee
    exit_fee_type = Column(String(20), nullable=True)
    exit_fee_percent = Column(Float, nullable=True)
    exit_fee_min = Column(Integer, nullable=True)
    exit_fee_months_free = Column(Integer, nullable=True)  # e.g., "no exit fee in months 1-3"
    exit_fee_notes = Column(Text, nullable=True)

    # Valuation Fee
    valuation_fee_type = Column(String(20), nullable=True)  # 'included', 'at_cost', 'fixed'
    valuation_fee_amount = Column(Integer, nullable=True)
    valuation_fee_notes = Column(Text, nullable=True)

    # Legal Fee
    legal_fee_type = Column(String(20), nullable=True)
    legal_fee_amount = Column(Integer, nullable=True)
    legal_fee_notes = Column(Text, nullable=True)

    # Admin/Processing Fee
    admin_fee = Column(Integer, nullable=True)

    # Broker Fee (if lender-set)
    broker_fee_percent = Column(Float, nullable=True)
    broker_fee_min = Column(Integer, nullable=True)

    # Other Fees (JSON for flexibility)
    other_fees = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate_card = relationship("RateCard", back_populates="fee_structure")

    def __repr__(self):
        return f"<FeeStructure(rate_card_id={self.rate_card_id})>"


class LendingCriteria(Base):
    """
    Lending criteria for a rate card - exactly as lender publishes.
    """
    __tablename__ = "lending_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rate_card_id = Column(Integer, ForeignKey("rate_cards.id"), nullable=False, unique=True)

    # Experience Requirements
    min_projects_completed = Column(Integer, nullable=True)
    accepts_first_time_developers = Column(Boolean, nullable=True)
    experience_notes = Column(Text, nullable=True)

    # Borrower Types
    accepts_individuals = Column(Boolean, nullable=True)
    accepts_spv = Column(Boolean, nullable=True)
    accepts_ltd_company = Column(Boolean, nullable=True)
    accepts_llp = Column(Boolean, nullable=True)
    accepts_offshore = Column(Boolean, nullable=True)
    accepts_foreign_nationals = Column(Boolean, nullable=True)
    foreign_national_notes = Column(Text, nullable=True)

    # Property/Project Requirements
    min_units = Column(Integer, nullable=True)
    max_units = Column(Integer, nullable=True)
    min_gdv = Column(Integer, nullable=True)
    max_gdv = Column(Integer, nullable=True)

    # Planning Requirements
    accepts_no_planning = Column(Boolean, nullable=True)
    accepts_outline_planning = Column(Boolean, nullable=True)
    accepts_full_planning = Column(Boolean, nullable=True)
    accepts_permitted_development = Column(Boolean, nullable=True)
    planning_notes = Column(Text, nullable=True)

    # Security Requirements
    requires_personal_guarantee = Column(Boolean, nullable=True)
    pg_percentage = Column(Float, nullable=True)
    pg_notes = Column(Text, nullable=True)
    requires_debenture = Column(Boolean, nullable=True)

    # Additional Criteria (flexible JSON)
    additional_criteria = Column(JSON, nullable=True)

    # Full criteria text (as published)
    full_criteria_text = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate_card = relationship("RateCard", back_populates="lending_criteria")

    def __repr__(self):
        return f"<LendingCriteria(rate_card_id={self.rate_card_id})>"
