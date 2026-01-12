"""
Term Sheet Service

Handles management of lender term sheets - the source of truth
for non-API based pricing.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.lender import Lender
from app.models.integration import (
    TermSheet,
    RateCard,
    RateTier,
    FeeStructure,
    LendingCriteria,
    LenderIntegration,
    IntegrationType,
)


class TermSheetService:
    """Service for managing lender term sheets."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Term Sheet CRUD
    # =========================================================================

    def create_term_sheet(
        self,
        lender_id: int,
        name: str,
        effective_date: date,
        source_document_url: Optional[str] = None,
        received_from: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TermSheet:
        """Create a new term sheet for a lender."""
        # Mark any existing current term sheets as not current
        existing = (
            self.db.query(TermSheet)
            .filter(TermSheet.lender_id == lender_id)
            .filter(TermSheet.is_current == True)
            .all()
        )
        for ts in existing:
            ts.is_current = False
            ts.expiry_date = effective_date

        # Create new term sheet
        term_sheet = TermSheet(
            lender_id=lender_id,
            name=name,
            effective_date=effective_date,
            is_current=True,
            source_document_url=source_document_url,
            received_from=received_from,
            received_date=date.today(),
            notes=notes,
            created_by=created_by,
        )

        self.db.add(term_sheet)

        # Ensure lender has term_sheet integration type
        self._ensure_integration_type(lender_id, IntegrationType.TERM_SHEET)

        self.db.commit()
        self.db.refresh(term_sheet)

        return term_sheet

    def get_term_sheet(self, term_sheet_id: int) -> Optional[TermSheet]:
        """Get a term sheet by ID."""
        return self.db.query(TermSheet).filter(TermSheet.id == term_sheet_id).first()

    def get_current_term_sheet(self, lender_id: int) -> Optional[TermSheet]:
        """Get the current term sheet for a lender."""
        return (
            self.db.query(TermSheet)
            .filter(TermSheet.lender_id == lender_id)
            .filter(TermSheet.is_current == True)
            .first()
        )

    def get_all_term_sheets(self, lender_id: int) -> List[TermSheet]:
        """Get all term sheets for a lender (historical)."""
        return (
            self.db.query(TermSheet)
            .filter(TermSheet.lender_id == lender_id)
            .order_by(TermSheet.effective_date.desc())
            .all()
        )

    def verify_term_sheet(
        self,
        term_sheet_id: int,
        verified_by: str
    ) -> Optional[TermSheet]:
        """Mark a term sheet as verified."""
        term_sheet = self.get_term_sheet(term_sheet_id)
        if term_sheet:
            term_sheet.verified_by = verified_by
            term_sheet.verified_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(term_sheet)
        return term_sheet

    # =========================================================================
    # Rate Card Management
    # =========================================================================

    def add_rate_card(
        self,
        term_sheet_id: int,
        product_name: str,
        finance_type: str,
        property_types: Optional[List[str]] = None,
        loan_purposes: Optional[List[str]] = None,
        borrower_types: Optional[List[str]] = None,
        regions_included: Optional[List[str]] = None,
        regions_excluded: Optional[List[str]] = None,
        postcodes_excluded: Optional[List[str]] = None,
        min_loan: Optional[int] = None,
        max_loan: Optional[int] = None,
        min_term_months: Optional[int] = None,
        max_term_months: Optional[int] = None,
    ) -> RateCard:
        """Add a rate card to a term sheet."""
        rate_card = RateCard(
            term_sheet_id=term_sheet_id,
            product_name=product_name,
            finance_type=finance_type,
            property_types=property_types,
            loan_purposes=loan_purposes,
            borrower_types=borrower_types,
            regions_included=regions_included,
            regions_excluded=regions_excluded,
            postcodes_excluded=postcodes_excluded,
            min_loan=min_loan,
            max_loan=max_loan,
            min_term_months=min_term_months,
            max_term_months=max_term_months,
            is_active=True,
        )

        self.db.add(rate_card)
        self.db.commit()
        self.db.refresh(rate_card)

        return rate_card

    def get_rate_card(self, rate_card_id: int) -> Optional[RateCard]:
        """Get a rate card by ID."""
        return self.db.query(RateCard).filter(RateCard.id == rate_card_id).first()

    # =========================================================================
    # Rate Tier Management
    # =========================================================================

    def add_rate_tier(
        self,
        rate_card_id: int,
        rate: float,
        rate_type: str,  # 'monthly' or 'annual'
        ltv_from: Optional[float] = None,
        ltv_to: Optional[float] = None,
        ltc_from: Optional[float] = None,
        ltc_to: Optional[float] = None,
        ltgdv_from: Optional[float] = None,
        ltgdv_to: Optional[float] = None,
        loan_from: Optional[int] = None,
        loan_to: Optional[int] = None,
        is_fixed: bool = True,
        day_one_rate: Optional[float] = None,
        rolled_up_rate: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> RateTier:
        """Add a rate tier to a rate card."""
        tier = RateTier(
            rate_card_id=rate_card_id,
            rate=rate,
            rate_type=rate_type,
            ltv_from=ltv_from,
            ltv_to=ltv_to,
            ltc_from=ltc_from,
            ltc_to=ltc_to,
            ltgdv_from=ltgdv_from,
            ltgdv_to=ltgdv_to,
            loan_from=loan_from,
            loan_to=loan_to,
            is_fixed=is_fixed,
            day_one_rate=day_one_rate,
            rolled_up_rate=rolled_up_rate,
            notes=notes,
        )

        self.db.add(tier)
        self.db.commit()
        self.db.refresh(tier)

        return tier

    def add_rate_tiers_bulk(
        self,
        rate_card_id: int,
        tiers_data: List[Dict[str, Any]]
    ) -> List[RateTier]:
        """Add multiple rate tiers at once."""
        tiers = []
        for data in tiers_data:
            tier = RateTier(rate_card_id=rate_card_id, **data)
            self.db.add(tier)
            tiers.append(tier)

        self.db.commit()
        for tier in tiers:
            self.db.refresh(tier)

        return tiers

    # =========================================================================
    # Fee Structure Management
    # =========================================================================

    def set_fee_structure(
        self,
        rate_card_id: int,
        arrangement_fee_type: Optional[str] = None,
        arrangement_fee_percent: Optional[float] = None,
        arrangement_fee_min: Optional[int] = None,
        exit_fee_type: Optional[str] = None,
        exit_fee_percent: Optional[float] = None,
        exit_fee_months_free: Optional[int] = None,
        valuation_fee_type: Optional[str] = None,
        valuation_fee_amount: Optional[int] = None,
        legal_fee_type: Optional[str] = None,
        legal_fee_amount: Optional[int] = None,
        admin_fee: Optional[int] = None,
        broker_fee_percent: Optional[float] = None,
        other_fees: Optional[Dict[str, Any]] = None,
    ) -> FeeStructure:
        """Set the fee structure for a rate card."""
        # Check if exists
        existing = (
            self.db.query(FeeStructure)
            .filter(FeeStructure.rate_card_id == rate_card_id)
            .first()
        )

        if existing:
            # Update
            for key, value in locals().items():
                if key not in ('self', 'rate_card_id', 'existing') and value is not None:
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new
        fee_structure = FeeStructure(
            rate_card_id=rate_card_id,
            arrangement_fee_type=arrangement_fee_type,
            arrangement_fee_percent=arrangement_fee_percent,
            arrangement_fee_min=arrangement_fee_min,
            exit_fee_type=exit_fee_type,
            exit_fee_percent=exit_fee_percent,
            exit_fee_months_free=exit_fee_months_free,
            valuation_fee_type=valuation_fee_type,
            valuation_fee_amount=valuation_fee_amount,
            legal_fee_type=legal_fee_type,
            legal_fee_amount=legal_fee_amount,
            admin_fee=admin_fee,
            broker_fee_percent=broker_fee_percent,
            other_fees=other_fees,
        )

        self.db.add(fee_structure)
        self.db.commit()
        self.db.refresh(fee_structure)

        return fee_structure

    # =========================================================================
    # Lending Criteria Management
    # =========================================================================

    def set_lending_criteria(
        self,
        rate_card_id: int,
        **criteria_fields
    ) -> LendingCriteria:
        """Set lending criteria for a rate card."""
        existing = (
            self.db.query(LendingCriteria)
            .filter(LendingCriteria.rate_card_id == rate_card_id)
            .first()
        )

        if existing:
            for key, value in criteria_fields.items():
                if value is not None:
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        criteria = LendingCriteria(rate_card_id=rate_card_id, **criteria_fields)
        self.db.add(criteria)
        self.db.commit()
        self.db.refresh(criteria)

        return criteria

    # =========================================================================
    # Helpers
    # =========================================================================

    def _ensure_integration_type(
        self,
        lender_id: int,
        integration_type: IntegrationType
    ):
        """Ensure lender has the correct integration type set."""
        existing = (
            self.db.query(LenderIntegration)
            .filter(LenderIntegration.lender_id == lender_id)
            .first()
        )

        if existing:
            if existing.integration_type == IntegrationType.API:
                existing.integration_type = IntegrationType.HYBRID
        else:
            integration = LenderIntegration(
                lender_id=lender_id,
                integration_type=integration_type,
                is_active=True,
            )
            self.db.add(integration)

    def import_term_sheet_from_dict(
        self,
        lender_id: int,
        data: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> TermSheet:
        """
        Import a complete term sheet from a dictionary structure.

        Expected format:
        {
            "name": "Bridging Rate Card 2024",
            "effective_date": "2024-01-01",
            "source_document_url": "https://...",
            "rate_cards": [
                {
                    "product_name": "Standard Bridge",
                    "finance_type": "bridging",
                    "property_types": ["residential"],
                    "min_loan": 100000,
                    "max_loan": 10000000,
                    "rate_tiers": [
                        {"ltv_from": 0, "ltv_to": 50, "rate": 0.55, "rate_type": "monthly"},
                        {"ltv_from": 50, "ltv_to": 60, "rate": 0.65, "rate_type": "monthly"},
                    ],
                    "fees": {
                        "arrangement_fee_percent": 2.0,
                        "exit_fee_percent": 0,
                    },
                    "criteria": {
                        "accepts_first_time_developers": true,
                        "accepts_spv": true,
                    }
                }
            ]
        }
        """
        # Create term sheet
        term_sheet = self.create_term_sheet(
            lender_id=lender_id,
            name=data["name"],
            effective_date=datetime.strptime(data["effective_date"], "%Y-%m-%d").date(),
            source_document_url=data.get("source_document_url"),
            received_from=data.get("received_from"),
            notes=data.get("notes"),
            created_by=created_by,
        )

        # Add rate cards
        for rc_data in data.get("rate_cards", []):
            rate_card = self.add_rate_card(
                term_sheet_id=term_sheet.id,
                product_name=rc_data["product_name"],
                finance_type=rc_data["finance_type"],
                property_types=rc_data.get("property_types"),
                loan_purposes=rc_data.get("loan_purposes"),
                borrower_types=rc_data.get("borrower_types"),
                regions_included=rc_data.get("regions_included"),
                regions_excluded=rc_data.get("regions_excluded"),
                postcodes_excluded=rc_data.get("postcodes_excluded"),
                min_loan=rc_data.get("min_loan"),
                max_loan=rc_data.get("max_loan"),
                min_term_months=rc_data.get("min_term_months"),
                max_term_months=rc_data.get("max_term_months"),
            )

            # Add rate tiers
            if "rate_tiers" in rc_data:
                self.add_rate_tiers_bulk(rate_card.id, rc_data["rate_tiers"])

            # Set fees
            if "fees" in rc_data:
                self.set_fee_structure(rate_card.id, **rc_data["fees"])

            # Set criteria
            if "criteria" in rc_data:
                self.set_lending_criteria(rate_card.id, **rc_data["criteria"])

        self.db.refresh(term_sheet)
        return term_sheet
