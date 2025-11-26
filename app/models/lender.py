"""Lender database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LenderStatus(enum.Enum):
    """Lender operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class LenderType(enum.Enum):
    """Type of lender."""
    BANK = "bank"
    BUILDING_SOCIETY = "building_society"
    SPECIALIST_LENDER = "specialist_lender"
    BRIDGING_SPECIALIST = "bridging_specialist"
    DEVELOPMENT_FUNDER = "development_funder"
    PRIVATE_LENDER = "private_lender"
    FAMILY_OFFICE = "family_office"
    FUND = "fund"
    PEER_TO_PEER = "peer_to_peer"


class Lender(Base):
    """
    Lender entity representing a finance provider.

    This is the core entity that products, ratings, and scrape history
    are associated with.
    """
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Classification
    lender_type = Column(SQLEnum(LenderType), nullable=False)
    status = Column(SQLEnum(LenderStatus), default=LenderStatus.ACTIVE)

    # Website & Scraping
    website_url = Column(String(500), nullable=True)
    rates_page_url = Column(String(500), nullable=True)
    criteria_page_url = Column(String(500), nullable=True)

    # FCA Information
    fca_number = Column(String(50), nullable=True)
    is_fca_regulated = Column(Boolean, default=True)

    # Business Details
    founded_year = Column(Integer, nullable=True)
    headquarters_location = Column(String(255), nullable=True)

    # Lending Appetite
    min_loan_amount = Column(Integer, nullable=True)  # in GBP
    max_loan_amount = Column(Integer, nullable=True)  # in GBP
    geographic_coverage = Column(Text, nullable=True)  # JSON array of regions

    # Lender Portal (Phase 2)
    has_portal_access = Column(Boolean, default=False)
    portal_email = Column(String(255), nullable=True)
    portal_password_hash = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)

    # Relationships
    contacts = relationship("LenderContact", back_populates="lender", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="lender", cascade="all, delete-orphan")
    ratings = relationship("LenderRating", back_populates="lender", cascade="all, delete-orphan")
    scrape_history = relationship("ScrapeHistory", back_populates="lender", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lender(id={self.id}, name='{self.name}', type={self.lender_type.value})>"


class LenderContact(Base):
    """Contact information for a lender."""
    __tablename__ = "lender_contacts"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Contact Details
    contact_type = Column(String(50), nullable=False)  # 'broker_desk', 'general', 'bdm'
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)  # For regional BDMs

    # Metadata
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", back_populates="contacts")

    def __repr__(self):
        return f"<LenderContact(id={self.id}, lender_id={self.lender_id}, type='{self.contact_type}')>"
