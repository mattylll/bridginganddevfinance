"""
Term Sheet API Routes

Endpoints for managing lender term sheets.
"""

from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.term_sheet_service import TermSheetService


router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================

class RateTierCreate(BaseModel):
    """Schema for creating a rate tier."""
    rate: float = Field(..., description="The interest rate")
    rate_type: str = Field(..., description="'monthly' or 'annual'")
    ltv_from: Optional[float] = None
    ltv_to: Optional[float] = None
    ltc_from: Optional[float] = None
    ltc_to: Optional[float] = None
    ltgdv_from: Optional[float] = None
    ltgdv_to: Optional[float] = None
    loan_from: Optional[int] = None
    loan_to: Optional[int] = None
    is_fixed: bool = True
    day_one_rate: Optional[float] = None
    rolled_up_rate: Optional[float] = None
    notes: Optional[str] = None


class FeeStructureCreate(BaseModel):
    """Schema for fee structure."""
    arrangement_fee_type: Optional[str] = None
    arrangement_fee_percent: Optional[float] = None
    arrangement_fee_min: Optional[int] = None
    exit_fee_type: Optional[str] = None
    exit_fee_percent: Optional[float] = None
    exit_fee_months_free: Optional[int] = None
    valuation_fee_type: Optional[str] = None
    valuation_fee_amount: Optional[int] = None
    legal_fee_type: Optional[str] = None
    legal_fee_amount: Optional[int] = None
    admin_fee: Optional[int] = None


class LendingCriteriaCreate(BaseModel):
    """Schema for lending criteria."""
    min_projects_completed: Optional[int] = None
    accepts_first_time_developers: Optional[bool] = None
    accepts_individuals: Optional[bool] = None
    accepts_spv: Optional[bool] = None
    accepts_ltd_company: Optional[bool] = None
    accepts_llp: Optional[bool] = None
    accepts_foreign_nationals: Optional[bool] = None
    min_units: Optional[int] = None
    max_units: Optional[int] = None
    min_gdv: Optional[int] = None
    max_gdv: Optional[int] = None
    accepts_no_planning: Optional[bool] = None
    accepts_outline_planning: Optional[bool] = None
    accepts_full_planning: Optional[bool] = None
    accepts_permitted_development: Optional[bool] = None
    requires_personal_guarantee: Optional[bool] = None
    pg_percentage: Optional[float] = None
    full_criteria_text: Optional[str] = None


class RateCardCreate(BaseModel):
    """Schema for creating a rate card."""
    product_name: str
    finance_type: str
    property_types: Optional[List[str]] = None
    loan_purposes: Optional[List[str]] = None
    borrower_types: Optional[List[str]] = None
    regions_included: Optional[List[str]] = None
    regions_excluded: Optional[List[str]] = None
    postcodes_excluded: Optional[List[str]] = None
    min_loan: Optional[int] = None
    max_loan: Optional[int] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    rate_tiers: Optional[List[RateTierCreate]] = None
    fees: Optional[FeeStructureCreate] = None
    criteria: Optional[LendingCriteriaCreate] = None


class TermSheetCreate(BaseModel):
    """Schema for creating a term sheet."""
    name: str = Field(..., description="Name of the term sheet")
    effective_date: date = Field(..., description="Date terms become effective")
    source_document_url: Optional[str] = None
    received_from: Optional[str] = None
    notes: Optional[str] = None


class TermSheetImport(BaseModel):
    """Schema for importing a complete term sheet with all data."""
    name: str
    effective_date: str  # "YYYY-MM-DD"
    source_document_url: Optional[str] = None
    received_from: Optional[str] = None
    notes: Optional[str] = None
    rate_cards: List[Dict[str, Any]] = []


class TermSheetResponse(BaseModel):
    """Response schema for term sheet."""
    id: int
    lender_id: int
    name: str
    effective_date: date
    expiry_date: Optional[date]
    is_current: bool
    source_document_url: Optional[str]
    verified_at: Optional[str]
    verified_by: Optional[str]

    class Config:
        from_attributes = True


# =============================================================================
# Term Sheet Endpoints
# =============================================================================

@router.post("/lender/{lender_id}", response_model=TermSheetResponse)
async def create_term_sheet(
    lender_id: int,
    data: TermSheetCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new term sheet for a lender.

    This will mark any existing current term sheets as expired.
    """
    service = TermSheetService(db)

    term_sheet = service.create_term_sheet(
        lender_id=lender_id,
        name=data.name,
        effective_date=data.effective_date,
        source_document_url=data.source_document_url,
        received_from=data.received_from,
        notes=data.notes,
    )

    return term_sheet


@router.post("/lender/{lender_id}/import")
async def import_term_sheet(
    lender_id: int,
    data: TermSheetImport,
    db: Session = Depends(get_db),
):
    """
    Import a complete term sheet with all rate cards, tiers, fees, and criteria.

    This is the main endpoint for entering lender term sheet data.
    """
    service = TermSheetService(db)

    term_sheet = service.import_term_sheet_from_dict(
        lender_id=lender_id,
        data=data.model_dump(),
        created_by="api_import",
    )

    return {
        "status": "success",
        "term_sheet_id": term_sheet.id,
        "name": term_sheet.name,
        "rate_cards_count": len(term_sheet.rate_cards),
    }


@router.get("/lender/{lender_id}/current")
async def get_current_term_sheet(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Get the current term sheet for a lender."""
    service = TermSheetService(db)
    term_sheet = service.get_current_term_sheet(lender_id)

    if not term_sheet:
        raise HTTPException(
            status_code=404,
            detail=f"No current term sheet found for lender {lender_id}"
        )

    # Build full response with rate cards
    rate_cards = []
    for rc in term_sheet.rate_cards:
        rate_cards.append({
            "id": rc.id,
            "product_name": rc.product_name,
            "finance_type": rc.finance_type,
            "property_types": rc.property_types,
            "min_loan": rc.min_loan,
            "max_loan": rc.max_loan,
            "rate_tiers": [
                {
                    "ltv_from": t.ltv_from,
                    "ltv_to": t.ltv_to,
                    "ltc_from": t.ltc_from,
                    "ltc_to": t.ltc_to,
                    "rate": t.rate,
                    "rate_type": t.rate_type,
                }
                for t in rc.rate_tiers
            ],
            "fees": {
                "arrangement_fee_percent": rc.fee_structure.arrangement_fee_percent if rc.fee_structure else None,
                "exit_fee_percent": rc.fee_structure.exit_fee_percent if rc.fee_structure else None,
            } if rc.fee_structure else None,
        })

    return {
        "id": term_sheet.id,
        "name": term_sheet.name,
        "effective_date": term_sheet.effective_date,
        "is_current": term_sheet.is_current,
        "verified_at": term_sheet.verified_at,
        "rate_cards": rate_cards,
    }


@router.get("/lender/{lender_id}/history")
async def get_term_sheet_history(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Get all term sheets for a lender (historical)."""
    service = TermSheetService(db)
    term_sheets = service.get_all_term_sheets(lender_id)

    return {
        "lender_id": lender_id,
        "term_sheets": [
            {
                "id": ts.id,
                "name": ts.name,
                "effective_date": ts.effective_date,
                "expiry_date": ts.expiry_date,
                "is_current": ts.is_current,
                "verified_at": ts.verified_at,
            }
            for ts in term_sheets
        ],
    }


@router.post("/{term_sheet_id}/verify")
async def verify_term_sheet(
    term_sheet_id: int,
    verified_by: str,
    db: Session = Depends(get_db),
):
    """Mark a term sheet as verified."""
    service = TermSheetService(db)
    term_sheet = service.verify_term_sheet(term_sheet_id, verified_by)

    if not term_sheet:
        raise HTTPException(status_code=404, detail="Term sheet not found")

    return {
        "status": "verified",
        "verified_by": term_sheet.verified_by,
        "verified_at": term_sheet.verified_at,
    }


# =============================================================================
# Rate Card Endpoints
# =============================================================================

@router.post("/{term_sheet_id}/rate-cards")
async def add_rate_card(
    term_sheet_id: int,
    data: RateCardCreate,
    db: Session = Depends(get_db),
):
    """Add a rate card to a term sheet."""
    service = TermSheetService(db)

    # Verify term sheet exists
    term_sheet = service.get_term_sheet(term_sheet_id)
    if not term_sheet:
        raise HTTPException(status_code=404, detail="Term sheet not found")

    # Create rate card
    rate_card = service.add_rate_card(
        term_sheet_id=term_sheet_id,
        product_name=data.product_name,
        finance_type=data.finance_type,
        property_types=data.property_types,
        loan_purposes=data.loan_purposes,
        borrower_types=data.borrower_types,
        regions_included=data.regions_included,
        regions_excluded=data.regions_excluded,
        postcodes_excluded=data.postcodes_excluded,
        min_loan=data.min_loan,
        max_loan=data.max_loan,
        min_term_months=data.min_term_months,
        max_term_months=data.max_term_months,
    )

    # Add rate tiers if provided
    if data.rate_tiers:
        service.add_rate_tiers_bulk(
            rate_card.id,
            [t.model_dump() for t in data.rate_tiers]
        )

    # Set fees if provided
    if data.fees:
        service.set_fee_structure(rate_card.id, **data.fees.model_dump())

    # Set criteria if provided
    if data.criteria:
        service.set_lending_criteria(rate_card.id, **data.criteria.model_dump())

    return {
        "status": "success",
        "rate_card_id": rate_card.id,
        "product_name": rate_card.product_name,
    }


@router.post("/rate-cards/{rate_card_id}/tiers")
async def add_rate_tier(
    rate_card_id: int,
    data: RateTierCreate,
    db: Session = Depends(get_db),
):
    """Add a rate tier to a rate card."""
    service = TermSheetService(db)

    tier = service.add_rate_tier(
        rate_card_id=rate_card_id,
        **data.model_dump()
    )

    return {
        "status": "success",
        "tier_id": tier.id,
        "rate": tier.rate,
    }


@router.post("/rate-cards/{rate_card_id}/fees")
async def set_fees(
    rate_card_id: int,
    data: FeeStructureCreate,
    db: Session = Depends(get_db),
):
    """Set fee structure for a rate card."""
    service = TermSheetService(db)

    fees = service.set_fee_structure(
        rate_card_id=rate_card_id,
        **data.model_dump()
    )

    return {
        "status": "success",
        "arrangement_fee": fees.arrangement_fee_percent,
        "exit_fee": fees.exit_fee_percent,
    }


@router.post("/rate-cards/{rate_card_id}/criteria")
async def set_criteria(
    rate_card_id: int,
    data: LendingCriteriaCreate,
    db: Session = Depends(get_db),
):
    """Set lending criteria for a rate card."""
    service = TermSheetService(db)

    criteria = service.set_lending_criteria(
        rate_card_id=rate_card_id,
        **data.model_dump()
    )

    return {
        "status": "success",
        "accepts_first_time": criteria.accepts_first_time_developers,
        "accepts_spv": criteria.accepts_spv,
    }
