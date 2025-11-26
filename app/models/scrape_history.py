"""Scrape history and change tracking models."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ScrapeStatus(enum.Enum):
    """Status of a scrape operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    NO_CHANGES = "no_changes"


class ChangeType(enum.Enum):
    """Type of change detected."""
    RATE_INCREASE = "rate_increase"
    RATE_DECREASE = "rate_decrease"
    FEE_CHANGE = "fee_change"
    LTV_CHANGE = "ltv_change"
    CRITERIA_CHANGE = "criteria_change"
    NEW_PRODUCT = "new_product"
    PRODUCT_REMOVED = "product_removed"
    CONTACT_CHANGE = "contact_change"
    GENERAL_UPDATE = "general_update"


class ScrapeHistory(Base):
    """
    Record of each scrape operation for a lender.

    Tracks when we scraped, what changed, and any issues encountered.
    """
    __tablename__ = "scrape_history"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Scrape Details
    scrape_started_at = Column(DateTime, default=datetime.utcnow)
    scrape_completed_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(ScrapeStatus), default=ScrapeStatus.SUCCESS)

    # URLs Scraped
    urls_scraped = Column(JSON, nullable=True)  # List of URLs visited

    # Results
    pages_scraped = Column(Integer, default=0)
    changes_detected = Column(Integer, default=0)

    # Raw Data (optional - for debugging)
    raw_html_hash = Column(String(64), nullable=True)  # SHA256 of scraped content

    # Error Information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", back_populates="scrape_history")
    changes = relationship("ScrapeChange", back_populates="scrape_history", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScrapeHistory(id={self.id}, lender_id={self.lender_id}, status={self.status.value})>"


class ScrapeChange(Base):
    """
    Individual change detected during a scrape.

    Each change is logged with before/after values for audit trail.
    """
    __tablename__ = "scrape_changes"

    id = Column(Integer, primary_key=True, index=True)
    scrape_history_id = Column(Integer, ForeignKey("scrape_history.id"), nullable=False)

    # What Changed
    change_type = Column(SQLEnum(ChangeType), nullable=False)
    entity_type = Column(String(50), nullable=False)  # 'product', 'lender', 'criteria'
    entity_id = Column(Integer, nullable=True)  # ID of the changed entity
    field_name = Column(String(100), nullable=True)  # Specific field that changed

    # Change Values
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Context
    description = Column(Text, nullable=True)  # Human-readable description
    significance = Column(String(20), default="normal")  # 'low', 'normal', 'high', 'critical'

    # Notification Status
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scrape_history = relationship("ScrapeHistory", back_populates="changes")

    def __repr__(self):
        return f"<ScrapeChange(id={self.id}, type={self.change_type.value}, entity={self.entity_type})>"
