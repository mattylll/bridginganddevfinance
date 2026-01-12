"""
Integration Manager

Manages all lender API integrations and coordinates
between API-based and term-sheet-based pricing.
"""

from datetime import datetime
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.lender import Lender
from app.models.integration import (
    LenderIntegration,
    IntegrationType,
    TermSheet,
    RateCard,
    RateTier,
)
from app.integrations.base import (
    BaseLenderAPI,
    QuoteRequest,
    QuoteResponse,
    QuoteStatus,
    RateQuote,
)


@dataclass
class CombinedQuoteResponse:
    """
    Combined response from multiple lenders.

    Includes both API-sourced and term-sheet-sourced quotes.
    """
    request: QuoteRequest
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Results by source
    api_quotes: List[QuoteResponse] = field(default_factory=list)
    term_sheet_quotes: List[QuoteResponse] = field(default_factory=list)

    # All combined
    all_quotes: List[QuoteResponse] = field(default_factory=list)

    # Summary
    total_lenders_queried: int = 0
    api_lenders_responded: int = 0
    term_sheet_lenders_matched: int = 0

    # Best options
    best_rate_quote: Optional[QuoteResponse] = None
    best_rate: Optional[float] = None


class IntegrationManager:
    """
    Manages lender integrations and coordinates quote requests.

    Handles:
    - API integrations (real-time quotes)
    - Term sheet lookups (manual data)
    - Combining results from both sources
    """

    # Registry of API integration classes by lender slug
    _api_registry: Dict[str, Type[BaseLenderAPI]] = {}

    def __init__(self, db: Session):
        self.db = db
        self._api_instances: Dict[int, BaseLenderAPI] = {}

    @classmethod
    def register_api(cls, lender_slug: str, api_class: Type[BaseLenderAPI]):
        """Register an API integration class for a lender."""
        cls._api_registry[lender_slug] = api_class

    def get_api_lenders(self) -> List[Lender]:
        """Get all lenders with API integrations configured."""
        return (
            self.db.query(Lender)
            .join(LenderIntegration)
            .filter(LenderIntegration.integration_type.in_([
                IntegrationType.API,
                IntegrationType.HYBRID,
            ]))
            .filter(LenderIntegration.is_active == True)
            .all()
        )

    def get_term_sheet_lenders(self) -> List[Lender]:
        """Get all lenders with term sheet data."""
        return (
            self.db.query(Lender)
            .join(TermSheet)
            .filter(TermSheet.is_current == True)
            .all()
        )

    async def get_api_instance(self, lender: Lender) -> Optional[BaseLenderAPI]:
        """Get or create API instance for a lender."""
        if lender.id in self._api_instances:
            return self._api_instances[lender.id]

        if lender.slug not in self._api_registry:
            return None

        api_class = self._api_registry[lender.slug]
        instance = api_class(lender_id=lender.id, lender_name=lender.name)

        if instance.is_configured:
            self._api_instances[lender.id] = instance
            return instance

        return None

    async def get_api_quote(
        self,
        lender: Lender,
        request: QuoteRequest
    ) -> Optional[QuoteResponse]:
        """Get a quote from a lender's API."""
        api = await self.get_api_instance(lender)
        if api is None:
            return None

        # Check eligibility first (quick local check)
        if not await api.check_eligibility(request):
            return QuoteResponse(
                status=QuoteStatus.OUTSIDE_CRITERIA,
                lender_name=lender.name,
                lender_id=lender.id,
                decline_reason="Outside lender criteria",
            )

        # Get actual quote
        return await api.get_indicative_quote(request)

    def get_term_sheet_quote(
        self,
        lender: Lender,
        request: QuoteRequest
    ) -> Optional[QuoteResponse]:
        """
        Get indicative quote from term sheet data.

        This uses the manually entered term sheet data to
        provide indicative pricing.
        """
        # Get current term sheets for this lender
        term_sheets = (
            self.db.query(TermSheet)
            .filter(TermSheet.lender_id == lender.id)
            .filter(TermSheet.is_current == True)
            .all()
        )

        if not term_sheets:
            return None

        matching_quotes = []

        for term_sheet in term_sheets:
            for rate_card in term_sheet.rate_cards:
                if not rate_card.is_active:
                    continue

                # Check if rate card applies to this request
                if not self._rate_card_matches(rate_card, request):
                    continue

                # Find applicable rate tier
                rate_tier = self._find_rate_tier(rate_card, request)
                if rate_tier is None:
                    continue

                # Get fee structure
                fees = rate_card.fee_structure

                quote = RateQuote(
                    rate=rate_tier.rate,
                    rate_type=rate_tier.rate_type,
                    max_ltv=rate_tier.ltv_to,
                    max_ltc=rate_tier.ltc_to,
                    max_ltgdv=rate_tier.ltgdv_to,
                    arrangement_fee_percent=fees.arrangement_fee_percent if fees else None,
                    exit_fee_percent=fees.exit_fee_percent if fees else None,
                    product_name=rate_card.product_name,
                    notes=rate_tier.notes,
                )
                matching_quotes.append(quote)

        if not matching_quotes:
            return QuoteResponse(
                status=QuoteStatus.OUTSIDE_CRITERIA,
                lender_name=lender.name,
                lender_id=lender.id,
                decline_reason="No matching products in term sheets",
            )

        # Find best rate
        best_rate = min(q.rate for q in matching_quotes)

        return QuoteResponse(
            status=QuoteStatus.SUCCESS,
            lender_name=lender.name,
            lender_id=lender.id,
            quotes=matching_quotes,
            best_rate=best_rate,
        )

    def _rate_card_matches(self, rate_card: RateCard, request: QuoteRequest) -> bool:
        """Check if a rate card applies to this request."""
        # Finance type
        if rate_card.finance_type != request.loan_purpose:
            # Map loan_purpose to finance_type
            purpose_to_type = {
                "purchase": "bridging",
                "refinance": "bridging",
                "equity_release": "bridging",
                "development": "development",
            }
            if rate_card.finance_type != purpose_to_type.get(request.loan_purpose):
                return False

        # Property type
        if rate_card.property_types:
            if request.property_type not in rate_card.property_types:
                return False

        # Borrower type
        if rate_card.borrower_types:
            if request.borrower_type not in rate_card.borrower_types:
                return False

        # Loan amount
        if rate_card.min_loan and request.loan_amount < rate_card.min_loan:
            return False
        if rate_card.max_loan and request.loan_amount > rate_card.max_loan:
            return False

        # Geography
        if rate_card.postcodes_excluded and request.property_postcode:
            prefix = request.property_postcode.split()[0][:2].upper()
            if prefix in rate_card.postcodes_excluded:
                return False

        return True

    def _find_rate_tier(self, rate_card: RateCard, request: QuoteRequest) -> Optional[RateTier]:
        """Find the applicable rate tier for this request."""
        # Calculate LTV/LTC/LTGDV
        ltv = None
        if request.property_value and request.property_value > 0:
            ltv = (request.loan_amount / request.property_value) * 100

        ltc = None
        if request.purchase_price and request.build_costs:
            total_cost = request.purchase_price + request.build_costs
            ltc = (request.loan_amount / total_cost) * 100

        ltgdv = None
        if request.gdv and request.gdv > 0:
            ltgdv = (request.loan_amount / request.gdv) * 100

        # Find matching tier
        for tier in rate_card.rate_tiers:
            # Check LTV band
            if tier.ltv_from is not None and tier.ltv_to is not None:
                if ltv is None:
                    continue
                if not (tier.ltv_from <= ltv <= tier.ltv_to):
                    continue

            # Check LTC band
            if tier.ltc_from is not None and tier.ltc_to is not None:
                if ltc is None:
                    continue
                if not (tier.ltc_from <= ltc <= tier.ltc_to):
                    continue

            # Check LTGDV band
            if tier.ltgdv_from is not None and tier.ltgdv_to is not None:
                if ltgdv is None:
                    continue
                if not (tier.ltgdv_from <= ltgdv <= tier.ltgdv_to):
                    continue

            # Check loan size band
            if tier.loan_from is not None and tier.loan_to is not None:
                if not (tier.loan_from <= request.loan_amount <= tier.loan_to):
                    continue

            return tier

        return None

    async def get_all_quotes(
        self,
        request: QuoteRequest,
        include_api: bool = True,
        include_term_sheets: bool = True,
    ) -> CombinedQuoteResponse:
        """
        Get quotes from all available sources.

        Args:
            request: Quote request
            include_api: Include API-based lenders
            include_term_sheets: Include term-sheet-based lenders

        Returns:
            Combined response with all quotes
        """
        response = CombinedQuoteResponse(request=request)

        # Get API quotes
        if include_api:
            api_lenders = self.get_api_lenders()
            response.total_lenders_queried += len(api_lenders)

            for lender in api_lenders:
                quote = await self.get_api_quote(lender, request)
                if quote:
                    response.api_quotes.append(quote)
                    response.all_quotes.append(quote)
                    if quote.status == QuoteStatus.SUCCESS:
                        response.api_lenders_responded += 1

        # Get term sheet quotes
        if include_term_sheets:
            ts_lenders = self.get_term_sheet_lenders()

            # Don't double-count lenders that also have APIs
            api_lender_ids = {l.id for l in self.get_api_lenders()}
            ts_only_lenders = [l for l in ts_lenders if l.id not in api_lender_ids]

            response.total_lenders_queried += len(ts_only_lenders)

            for lender in ts_only_lenders:
                quote = self.get_term_sheet_quote(lender, request)
                if quote:
                    response.term_sheet_quotes.append(quote)
                    response.all_quotes.append(quote)
                    if quote.status == QuoteStatus.SUCCESS:
                        response.term_sheet_lenders_matched += 1

        # Find best rate overall
        successful_quotes = [
            q for q in response.all_quotes
            if q.status == QuoteStatus.SUCCESS and q.best_rate is not None
        ]

        if successful_quotes:
            response.best_rate_quote = min(successful_quotes, key=lambda q: q.best_rate)
            response.best_rate = response.best_rate_quote.best_rate

        return response

    async def close_all(self):
        """Close all API connections."""
        for api in self._api_instances.values():
            await api.close()
        self._api_instances.clear()


# Register known API integrations
def register_integrations():
    """Register all known API integrations."""
    from app.integrations.lendinvest import LendInvestAPI
    IntegrationManager.register_api("lendinvest", LendInvestAPI)


# Auto-register on import
register_integrations()
