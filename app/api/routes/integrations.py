"""
Integration API Routes

Endpoints for managing lender API integrations and getting live quotes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lender import Lender
from app.models.integration import LenderIntegration, IntegrationType
from app.integrations.base import QuoteRequest as IntegrationQuoteRequest, QuoteStatus
from app.integrations.manager import IntegrationManager


router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================

class QuoteRequestSchema(BaseModel):
    """Request for a quote from lender APIs."""
    # Loan Details
    loan_amount: int = Field(..., gt=0, description="Loan amount in GBP")
    loan_purpose: str = Field(..., description="purchase, refinance, equity_release, development")
    term_months: int = Field(12, gt=0, description="Loan term in months")

    # Property Details
    property_value: Optional[int] = None
    purchase_price: Optional[int] = None
    property_type: str = "residential"
    property_postcode: Optional[str] = None

    # Development Specific
    gdv: Optional[int] = None
    build_costs: Optional[int] = None
    current_value: Optional[int] = None

    # Borrower Details
    borrower_type: str = "individual"
    experience_projects: Optional[int] = None
    is_first_time_developer: bool = False

    # Planning
    planning_status: Optional[str] = None

    # Exit
    exit_strategy: Optional[str] = None


class IntegrationConfigSchema(BaseModel):
    """Schema for configuring a lender integration."""
    integration_type: str = Field(..., description="api, term_sheet, hybrid")
    api_base_url: Optional[str] = None
    api_key_name: Optional[str] = None
    api_auth_type: Optional[str] = None
    supports_indicative_quote: bool = False
    technical_contact_email: Optional[str] = None


# =============================================================================
# Quote Endpoints
# =============================================================================

@router.post("/quote")
async def get_quotes(
    request: QuoteRequestSchema,
    lender_id: Optional[int] = None,
    include_api: bool = True,
    include_term_sheets: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get quotes from all available sources.

    - **lender_id**: Optional - get quote from specific lender only
    - **include_api**: Include real-time API quotes
    - **include_term_sheets**: Include term sheet based indicative quotes

    Returns combined quotes from all matching lenders.
    """
    manager = IntegrationManager(db)

    # Convert to internal request format
    quote_request = IntegrationQuoteRequest(
        loan_amount=request.loan_amount,
        loan_purpose=request.loan_purpose,
        term_months=request.term_months,
        property_value=request.property_value,
        purchase_price=request.purchase_price,
        property_type=request.property_type,
        property_postcode=request.property_postcode,
        gdv=request.gdv,
        build_costs=request.build_costs,
        current_value=request.current_value,
        borrower_type=request.borrower_type,
        experience_projects=request.experience_projects,
        is_first_time_developer=request.is_first_time_developer,
        planning_status=request.planning_status,
        exit_strategy=request.exit_strategy,
    )

    try:
        if lender_id:
            # Get quote from specific lender
            lender = db.query(Lender).filter(Lender.id == lender_id).first()
            if not lender:
                raise HTTPException(status_code=404, detail="Lender not found")

            # Try API first
            api_quote = await manager.get_api_quote(lender, quote_request)
            if api_quote:
                return {
                    "source": "api",
                    "lender": lender.name,
                    "status": api_quote.status.value,
                    "quotes": [
                        {
                            "rate": q.rate,
                            "rate_type": q.rate_type,
                            "max_ltv": q.max_ltv,
                            "arrangement_fee": q.arrangement_fee_percent,
                            "product_name": q.product_name,
                        }
                        for q in api_quote.quotes
                    ] if api_quote.quotes else [],
                    "best_rate": api_quote.best_rate,
                    "decline_reason": api_quote.decline_reason,
                }

            # Fall back to term sheet
            ts_quote = manager.get_term_sheet_quote(lender, quote_request)
            if ts_quote:
                return {
                    "source": "term_sheet",
                    "lender": lender.name,
                    "status": ts_quote.status.value,
                    "quotes": [
                        {
                            "rate": q.rate,
                            "rate_type": q.rate_type,
                            "max_ltv": q.max_ltv,
                            "arrangement_fee": q.arrangement_fee_percent,
                            "product_name": q.product_name,
                        }
                        for q in ts_quote.quotes
                    ] if ts_quote.quotes else [],
                    "best_rate": ts_quote.best_rate,
                }

            return {
                "source": None,
                "lender": lender.name,
                "status": "no_data",
                "message": "No API integration or term sheet data available for this lender",
            }

        # Get from all sources
        combined = await manager.get_all_quotes(
            quote_request,
            include_api=include_api,
            include_term_sheets=include_term_sheets,
        )

        # Format response
        results = []
        for quote in combined.all_quotes:
            if quote.status == QuoteStatus.SUCCESS:
                results.append({
                    "lender_id": quote.lender_id,
                    "lender_name": quote.lender_name,
                    "status": quote.status.value,
                    "best_rate": quote.best_rate,
                    "quotes_count": len(quote.quotes),
                    "quotes": [
                        {
                            "rate": q.rate,
                            "rate_type": q.rate_type,
                            "max_ltv": q.max_ltv,
                            "arrangement_fee": q.arrangement_fee_percent,
                            "product_name": q.product_name,
                        }
                        for q in quote.quotes[:3]  # Limit to top 3 per lender
                    ],
                })

        # Sort by best rate
        results.sort(key=lambda x: x["best_rate"] if x["best_rate"] else float("inf"))

        return {
            "total_lenders_queried": combined.total_lenders_queried,
            "api_responses": combined.api_lenders_responded,
            "term_sheet_matches": combined.term_sheet_lenders_matched,
            "best_rate": combined.best_rate,
            "best_lender": combined.best_rate_quote.lender_name if combined.best_rate_quote else None,
            "results": results,
        }

    finally:
        await manager.close_all()


# =============================================================================
# Integration Management Endpoints
# =============================================================================

@router.get("/")
async def list_integrations(
    db: Session = Depends(get_db),
):
    """List all configured lender integrations."""
    integrations = db.query(LenderIntegration).all()

    return {
        "integrations": [
            {
                "id": i.id,
                "lender_id": i.lender_id,
                "integration_type": i.integration_type.value,
                "is_active": i.is_active,
                "supports_indicative_quote": i.supports_indicative_quote,
                "last_successful_call": i.last_successful_call,
                "last_error": i.last_error,
            }
            for i in integrations
        ],
    }


@router.get("/lender/{lender_id}")
async def get_lender_integration(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Get integration details for a specific lender."""
    integration = (
        db.query(LenderIntegration)
        .filter(LenderIntegration.lender_id == lender_id)
        .first()
    )

    if not integration:
        # Check if lender exists
        lender = db.query(Lender).filter(Lender.id == lender_id).first()
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")

        return {
            "lender_id": lender_id,
            "lender_name": lender.name,
            "integration_configured": False,
            "message": "No integration configured for this lender",
        }

    return {
        "lender_id": lender_id,
        "integration_configured": True,
        "integration_type": integration.integration_type.value,
        "is_active": integration.is_active,
        "api_base_url": integration.api_base_url,
        "supports_indicative_quote": integration.supports_indicative_quote,
        "supports_full_application": integration.supports_full_application,
        "last_successful_call": integration.last_successful_call,
        "last_error": integration.last_error,
        "last_error_at": integration.last_error_at,
        "technical_contact_email": integration.technical_contact_email,
    }


@router.post("/lender/{lender_id}")
async def configure_integration(
    lender_id: int,
    config: IntegrationConfigSchema,
    db: Session = Depends(get_db),
):
    """Configure or update integration for a lender."""
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    # Map string to enum
    try:
        integration_type = IntegrationType(config.integration_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid integration type. Must be one of: {[t.value for t in IntegrationType]}"
        )

    # Check if exists
    existing = (
        db.query(LenderIntegration)
        .filter(LenderIntegration.lender_id == lender_id)
        .first()
    )

    if existing:
        # Update
        existing.integration_type = integration_type
        existing.api_base_url = config.api_base_url
        existing.api_key_name = config.api_key_name
        existing.api_auth_type = config.api_auth_type
        existing.supports_indicative_quote = config.supports_indicative_quote
        existing.technical_contact_email = config.technical_contact_email
        db.commit()
        db.refresh(existing)

        return {
            "status": "updated",
            "integration_id": existing.id,
        }

    # Create new
    integration = LenderIntegration(
        lender_id=lender_id,
        integration_type=integration_type,
        api_base_url=config.api_base_url,
        api_key_name=config.api_key_name,
        api_auth_type=config.api_auth_type,
        supports_indicative_quote=config.supports_indicative_quote,
        technical_contact_email=config.technical_contact_email,
        is_active=True,
    )

    db.add(integration)
    db.commit()
    db.refresh(integration)

    return {
        "status": "created",
        "integration_id": integration.id,
    }


@router.post("/lender/{lender_id}/test")
async def test_integration(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Test the API integration for a lender."""
    integration = (
        db.query(LenderIntegration)
        .filter(LenderIntegration.lender_id == lender_id)
        .filter(LenderIntegration.integration_type.in_([IntegrationType.API, IntegrationType.HYBRID]))
        .first()
    )

    if not integration:
        raise HTTPException(
            status_code=400,
            detail="No API integration configured for this lender"
        )

    lender = db.query(Lender).filter(Lender.id == lender_id).first()

    manager = IntegrationManager(db)
    api = await manager.get_api_instance(lender)

    if not api:
        return {
            "status": "error",
            "message": "API integration class not found or not configured",
        }

    if not api.is_configured:
        return {
            "status": "error",
            "message": f"API not configured - missing environment variable: {api.api_key_env_var}",
        }

    # Try a test quote
    test_request = IntegrationQuoteRequest(
        loan_amount=500000,
        loan_purpose="purchase",
        term_months=12,
        property_value=700000,
        property_type="residential",
        borrower_type="individual",
    )

    response = await api.get_indicative_quote(test_request)
    await manager.close_all()

    return {
        "status": response.status.value,
        "test_passed": response.status in [QuoteStatus.SUCCESS, QuoteStatus.DECLINED, QuoteStatus.OUTSIDE_CRITERIA],
        "error": response.error_message,
        "quotes_returned": len(response.quotes) if response.quotes else 0,
    }


@router.get("/status")
async def integration_status(
    db: Session = Depends(get_db),
):
    """Get overall integration status summary."""
    integrations = db.query(LenderIntegration).all()

    by_type = {}
    for i in integrations:
        t = i.integration_type.value
        by_type[t] = by_type.get(t, 0) + 1

    active_apis = sum(
        1 for i in integrations
        if i.integration_type in [IntegrationType.API, IntegrationType.HYBRID]
        and i.is_active
    )

    return {
        "total_integrations": len(integrations),
        "by_type": by_type,
        "active_api_integrations": active_apis,
        "lenders_without_integration": db.query(Lender).count() - len(integrations),
    }
