"""
Lender Service

Handles CRUD operations and business logic for lenders.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from slugify import slugify

from app.models.lender import Lender, LenderContact, LenderStatus
from app.schemas.lender import LenderCreate, LenderUpdate, LenderContactCreate


class LenderService:
    """Service for managing lenders."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LenderStatus] = None,
        lender_type: Optional[str] = None,
    ) -> List[Lender]:
        """Get all lenders with optional filtering."""
        query = self.db.query(Lender)

        if status:
            query = query.filter(Lender.status == status)

        if lender_type:
            query = query.filter(Lender.lender_type == lender_type)

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, lender_id: int) -> Optional[Lender]:
        """Get a lender by ID."""
        return self.db.query(Lender).filter(Lender.id == lender_id).first()

    def get_by_slug(self, slug: str) -> Optional[Lender]:
        """Get a lender by slug."""
        return self.db.query(Lender).filter(Lender.slug == slug).first()

    def create(self, lender_data: LenderCreate) -> Lender:
        """Create a new lender."""
        # Generate slug
        slug = slugify(lender_data.name)

        # Check for duplicate
        existing = self.get_by_slug(slug)
        if existing:
            raise ValueError(f"Lender with slug '{slug}' already exists")

        # Create lender
        lender = Lender(
            name=lender_data.name,
            slug=slug,
            description=lender_data.description,
            lender_type=lender_data.lender_type,
            status=LenderStatus.ACTIVE,
            website_url=lender_data.website_url,
            rates_page_url=lender_data.rates_page_url,
            criteria_page_url=lender_data.criteria_page_url,
            fca_number=lender_data.fca_number,
            is_fca_regulated=lender_data.is_fca_regulated,
            founded_year=lender_data.founded_year,
            headquarters_location=lender_data.headquarters_location,
            min_loan_amount=lender_data.min_loan_amount,
            max_loan_amount=lender_data.max_loan_amount,
            geographic_coverage=lender_data.geographic_coverage,
        )

        self.db.add(lender)
        self.db.flush()

        # Add contacts if provided
        if lender_data.contacts:
            for contact_data in lender_data.contacts:
                contact = LenderContact(
                    lender_id=lender.id,
                    **contact_data.model_dump()
                )
                self.db.add(contact)

        self.db.commit()
        self.db.refresh(lender)

        return lender

    def update(self, lender_id: int, lender_data: LenderUpdate) -> Optional[Lender]:
        """Update a lender."""
        lender = self.get_by_id(lender_id)
        if not lender:
            return None

        # Update fields
        update_data = lender_data.model_dump(exclude_unset=True)

        # If name changed, update slug
        if "name" in update_data:
            update_data["slug"] = slugify(update_data["name"])

        for field, value in update_data.items():
            setattr(lender, field, value)

        self.db.commit()
        self.db.refresh(lender)

        return lender

    def delete(self, lender_id: int) -> bool:
        """Delete a lender."""
        lender = self.get_by_id(lender_id)
        if not lender:
            return False

        self.db.delete(lender)
        self.db.commit()

        return True

    def add_contact(
        self, lender_id: int, contact_data: LenderContactCreate
    ) -> Optional[LenderContact]:
        """Add a contact to a lender."""
        lender = self.get_by_id(lender_id)
        if not lender:
            return None

        contact = LenderContact(
            lender_id=lender_id,
            **contact_data.model_dump()
        )

        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)

        return contact

    def count(self, status: Optional[LenderStatus] = None) -> int:
        """Count lenders."""
        query = self.db.query(Lender)
        if status:
            query = query.filter(Lender.status == status)
        return query.count()

    def search(self, query: str, limit: int = 20) -> List[Lender]:
        """Search lenders by name."""
        return (
            self.db.query(Lender)
            .filter(Lender.name.ilike(f"%{query}%"))
            .limit(limit)
            .all()
        )
