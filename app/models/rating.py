"""Lender rating and scoring models."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class RatingCategory(enum.Enum):
    """Categories for rating lenders."""
    SPEED_TO_OFFER = "speed_to_offer"
    SPEED_TO_COMPLETION = "speed_to_completion"
    RATE_COMPETITIVENESS = "rate_competitiveness"
    FLEXIBILITY = "flexibility"
    COMMUNICATION = "communication"
    RELIABILITY = "reliability"
    BDM_SUPPORT = "bdm_support"
    DOCUMENTATION = "documentation"
    OVERALL = "overall"


class LenderRating(Base):
    """
    Rating/score for a lender in a specific category.

    Ratings can come from:
    - System calculations (based on data)
    - Broker feedback
    - Admin input
    """
    __tablename__ = "lender_ratings"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Rating Details
    category = Column(SQLEnum(RatingCategory), nullable=False)
    score = Column(Float, nullable=False)  # 0-100 scale

    # Rating Source
    source = Column(String(50), nullable=False)  # 'system', 'broker', 'admin'
    source_user_id = Column(Integer, nullable=True)  # If from a specific user

    # Supporting Data
    sample_size = Column(Integer, nullable=True)  # Number of data points
    confidence = Column(Float, nullable=True)  # 0-1 confidence level

    # Comments
    notes = Column(Text, nullable=True)

    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lender = relationship("Lender", back_populates="ratings")

    def __repr__(self):
        return f"<LenderRating(lender_id={self.lender_id}, category={self.category.value}, score={self.score})>"


class LenderPerformanceMetric(Base):
    """
    Actual performance metrics for a lender.

    These are used to calculate ratings and provide objective data.
    """
    __tablename__ = "lender_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Time Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Speed Metrics (in business days)
    avg_days_to_dip = Column(Float, nullable=True)  # Decision in Principle
    avg_days_to_offer = Column(Float, nullable=True)
    avg_days_to_completion = Column(Float, nullable=True)

    # Volume Metrics
    deals_submitted = Column(Integer, nullable=True)
    deals_offered = Column(Integer, nullable=True)
    deals_completed = Column(Integer, nullable=True)
    deals_declined = Column(Integer, nullable=True)
    deals_withdrawn = Column(Integer, nullable=True)

    # Conversion Rates
    dip_to_offer_rate = Column(Float, nullable=True)  # Percentage
    offer_to_completion_rate = Column(Float, nullable=True)

    # Value Metrics
    total_value_submitted = Column(Integer, nullable=True)  # GBP
    total_value_completed = Column(Integer, nullable=True)
    avg_loan_size = Column(Integer, nullable=True)

    # Rate Analysis
    avg_rate_offered = Column(Float, nullable=True)
    rate_vs_advertised = Column(Float, nullable=True)  # Difference from advertised rate

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    data_source = Column(String(50), nullable=True)  # 'manual', 'api', 'import'

    def __repr__(self):
        return f"<LenderPerformanceMetric(lender_id={self.lender_id}, period={self.period_start}-{self.period_end})>"


class BrokerFeedback(Base):
    """
    Feedback submitted by brokers about their experience with a lender.

    This provides qualitative data to complement quantitative metrics.
    """
    __tablename__ = "broker_feedback"

    id = Column(Integer, primary_key=True, index=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=False)

    # Feedback Source
    broker_id = Column(Integer, nullable=True)  # If we have broker accounts
    broker_name = Column(String(255), nullable=True)
    is_anonymous = Column(Boolean, default=False)

    # Deal Context (optional)
    deal_type = Column(String(50), nullable=True)
    deal_size = Column(Integer, nullable=True)
    deal_completed = Column(Boolean, nullable=True)

    # Ratings (1-5 scale)
    rating_speed = Column(Integer, nullable=True)
    rating_communication = Column(Integer, nullable=True)
    rating_flexibility = Column(Integer, nullable=True)
    rating_bdm_support = Column(Integer, nullable=True)
    rating_overall = Column(Integer, nullable=True)

    # Written Feedback
    positive_feedback = Column(Text, nullable=True)
    negative_feedback = Column(Text, nullable=True)
    would_recommend = Column(Boolean, nullable=True)

    # Moderation
    is_approved = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BrokerFeedback(id={self.id}, lender_id={self.lender_id}, overall={self.rating_overall})>"
