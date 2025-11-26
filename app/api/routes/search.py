"""
Search API Routes

Loan matching and search endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import FinanceType
from app.schemas.search import (
    LoanSearchRequest,
    LoanSearchResponse,
    QuickQuoteRequest,
    QuickQuoteResponse,
)
from app.services.loan_matcher import LoanMatcher


router = APIRouter()


@router.post("/loans", response_model=LoanSearchResponse)
async def search_loans(
    request: LoanSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Search for matching loan products.

    This is the main endpoint for finding suitable finance options.
    Provide your deal details and get matched with appropriate lenders.

    The response includes:
    - Ranked list of matching products
    - Match scores showing fit quality
    - Criteria issues and warnings
    - Best rate, best match, and fastest lender recommendations
    """
    matcher = LoanMatcher(db)
    return matcher.search(request)


@router.post("/quick-quote", response_model=QuickQuoteResponse)
async def quick_quote(
    request: QuickQuoteRequest,
    db: Session = Depends(get_db),
):
    """
    Get a quick indicative quote.

    Simplified search for getting ballpark figures quickly.
    """
    # Convert to full search request
    full_request = LoanSearchRequest(
        finance_type=request.finance_type,
        loan_amount=request.loan_amount,
        property_value=request.property_value,
        gdv=request.gdv,
        postcode=request.postcode,
        is_first_time_developer=request.is_first_time,
        limit=50,
    )

    matcher = LoanMatcher(db)
    results = matcher.search(full_request)

    # Summarize results
    if results.total_matches == 0:
        return QuickQuoteResponse(
            indicative_rate_from=None,
            indicative_rate_to=None,
            available_lenders=0,
            best_ltv_available=None,
            message="No matching products found. Try adjusting your criteria.",
        )

    # Get rate range from matching products
    rates = [m.rate_from for m in results.matches if m.matches_criteria and m.rate_from]
    ltvs = [m.max_ltv for m in results.matches if m.matches_criteria and m.max_ltv]

    matching_lenders = len(set(m.lender_id for m in results.matches if m.matches_criteria))

    return QuickQuoteResponse(
        indicative_rate_from=min(rates) if rates else None,
        indicative_rate_to=max(rates) if rates else None,
        available_lenders=matching_lenders,
        best_ltv_available=max(ltvs) if ltvs else None,
        message=f"Found {matching_lenders} lenders with suitable products.",
    )


@router.get("/finance-types")
async def list_finance_types():
    """List available finance types."""
    return {
        "finance_types": [
            {
                "value": ft.value,
                "name": ft.value.replace("_", " ").title(),
                "description": _get_finance_type_description(ft),
            }
            for ft in FinanceType
        ]
    }


def _get_finance_type_description(ft: FinanceType) -> str:
    """Get description for a finance type."""
    descriptions = {
        FinanceType.BRIDGING: "Short-term finance for property purchases, typically 1-24 months",
        FinanceType.DEVELOPMENT: "Finance for ground-up development or major refurbishment projects",
        FinanceType.MEZZANINE: "Junior debt sitting behind senior debt, higher LTC but higher rates",
        FinanceType.EQUITY: "Equity investment in exchange for profit share",
        FinanceType.JOINT_VENTURE: "Partnership with a funder who provides capital for a share of profits",
        FinanceType.DEVELOPER_EXIT: "Refinancing completed developments to release capital",
        FinanceType.REFURBISHMENT: "Finance for light to medium refurbishment projects",
        FinanceType.AUCTION: "Fast finance specifically for auction purchases (28-day completion)",
        FinanceType.LAND: "Finance for land purchases, with or without planning",
        FinanceType.STRETCH_SENIOR: "Enhanced senior debt providing higher LTC than standard senior",
    }
    return descriptions.get(ft, "")


@router.get("/compare")
async def compare_products(
    product_ids: str = Query(..., description="Comma-separated product IDs"),
    db: Session = Depends(get_db),
):
    """
    Compare multiple products side by side.

    Provide a comma-separated list of product IDs to compare.
    """
    from app.services.product_service import ProductService

    ids = [int(id.strip()) for id in product_ids.split(",") if id.strip()]

    if len(ids) < 2:
        return {"error": "Please provide at least 2 product IDs to compare"}

    if len(ids) > 5:
        return {"error": "Maximum 5 products can be compared at once"}

    service = ProductService(db)
    products = []

    for product_id in ids:
        product = service.get_by_id(product_id)
        if product:
            products.append(product)

    if len(products) < 2:
        return {"error": "Not enough valid products found"}

    # Build comparison matrix
    comparison = {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "lender_id": p.lender_id,
                "finance_type": p.finance_type.value,
                "rate_from": p.rate_from,
                "rate_to": p.rate_to,
                "rate_type": p.rate_type,
                "arrangement_fee_percent": p.arrangement_fee_percent,
                "exit_fee_percent": p.exit_fee_percent,
                "max_ltv": p.max_ltv,
                "max_ltc": p.max_ltc,
                "max_ltgdv": p.max_ltgdv,
                "min_loan": p.min_loan,
                "max_loan": p.max_loan,
                "min_term_months": p.min_term_months,
                "max_term_months": p.max_term_months,
            }
            for p in products
        ],
        "best_rate": min(products, key=lambda p: p.rate_from or float("inf")).id if products else None,
        "best_ltv": max(products, key=lambda p: p.max_ltv or 0).id if products else None,
        "lowest_fee": min(products, key=lambda p: p.arrangement_fee_percent or float("inf")).id if products else None,
    }

    return comparison
