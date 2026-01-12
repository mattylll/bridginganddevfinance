"""
LendInvest API Integration

LendInvest offers API access for brokers to get indicative quotes
and submit applications programmatically.

API Documentation: https://www.lendinvest.com/intermediaries/api
(Note: Actual endpoints may differ - this is a template to be updated
with real API details once credentials are obtained)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx

from app.integrations.base import (
    BaseLenderAPI,
    QuoteRequest,
    QuoteResponse,
    RateQuote,
    QuoteStatus,
)


class LendInvestAPI(BaseLenderAPI):
    """
    LendInvest API integration for bridging and development finance.

    Products available via API:
    - Bridging Finance
    - Development Finance
    - Buy-to-Let (out of scope for this platform)

    Note: This integration requires API credentials from LendInvest.
    Contact their intermediary team to get access.
    """

    @property
    def api_base_url(self) -> str:
        # Production URL - update with actual endpoint
        return "https://api.lendinvest.com/v1"

    @property
    def api_key_env_var(self) -> str:
        return "LENDINVEST_API_KEY"

    @property
    def api_secret_env_var(self) -> str:
        return "LENDINVEST_API_SECRET"

    def _get_auth_headers(self) -> Dict[str, str]:
        """LendInvest uses OAuth2 Bearer tokens."""
        import os
        api_key = os.getenv(self.api_key_env_var, "")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _map_request_to_api(self, request: QuoteRequest) -> Dict[str, Any]:
        """Map our standard request to LendInvest's API format."""
        # This mapping needs to be updated with actual LendInvest API schema
        payload = {
            "loanAmount": request.loan_amount,
            "loanPurpose": self._map_loan_purpose(request.loan_purpose),
            "termMonths": request.term_months,
            "property": {
                "type": self._map_property_type(request.property_type),
                "postcode": request.property_postcode,
                "currentValue": request.property_value or request.current_value,
                "purchasePrice": request.purchase_price,
            },
            "borrower": {
                "type": self._map_borrower_type(request.borrower_type),
            },
        }

        # Add development-specific fields
        if request.loan_purpose == "development":
            payload["development"] = {
                "gdv": request.gdv,
                "buildCosts": request.build_costs,
                "planningStatus": request.planning_status,
            }
            if request.experience_projects is not None:
                payload["borrower"]["projectsCompleted"] = request.experience_projects

        # Add exit strategy
        if request.exit_strategy:
            payload["exitStrategy"] = request.exit_strategy

        return payload

    def _map_loan_purpose(self, purpose: str) -> str:
        """Map our purpose to LendInvest's."""
        mapping = {
            "purchase": "PURCHASE",
            "refinance": "REFINANCE",
            "equity_release": "CAPITAL_RAISE",
            "development": "DEVELOPMENT",
        }
        return mapping.get(purpose, "OTHER")

    def _map_property_type(self, prop_type: str) -> str:
        """Map our property type to LendInvest's."""
        mapping = {
            "residential": "RESIDENTIAL",
            "commercial": "COMMERCIAL",
            "mixed": "MIXED_USE",
            "land": "LAND",
        }
        return mapping.get(prop_type, "RESIDENTIAL")

    def _map_borrower_type(self, borrower_type: str) -> str:
        """Map our borrower type to LendInvest's."""
        mapping = {
            "individual": "INDIVIDUAL",
            "spv": "SPV",
            "ltd": "LIMITED_COMPANY",
            "llp": "LLP",
        }
        return mapping.get(borrower_type, "INDIVIDUAL")

    def _parse_api_response(self, response_data: Dict[str, Any]) -> QuoteResponse:
        """Parse LendInvest API response into our standard format."""
        # This needs to be updated with actual response parsing
        # once we have real API access

        if response_data.get("status") == "DECLINED":
            return QuoteResponse(
                status=QuoteStatus.DECLINED,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                decline_reason=response_data.get("declineReason"),
                raw_response=response_data,
            )

        if response_data.get("status") == "REFER":
            return QuoteResponse(
                status=QuoteStatus.REFER,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                refer_reason=response_data.get("referReason"),
                raw_response=response_data,
            )

        # Parse quotes
        quotes = []
        for product in response_data.get("products", []):
            quote = RateQuote(
                rate=product.get("rate"),
                rate_type=product.get("rateType", "monthly"),
                max_ltv=product.get("maxLtv"),
                max_ltc=product.get("maxLtc"),
                max_ltgdv=product.get("maxLtgdv"),
                arrangement_fee_percent=product.get("arrangementFee"),
                exit_fee_percent=product.get("exitFee"),
                product_name=product.get("productName"),
                product_code=product.get("productCode"),
            )
            quotes.append(quote)

        # Find best rate
        best_rate = None
        if quotes:
            rates = [q.rate for q in quotes if q.rate is not None]
            if rates:
                best_rate = min(rates)

        return QuoteResponse(
            status=QuoteStatus.SUCCESS,
            lender_name=self.lender_name,
            lender_id=self.lender_id,
            quotes=quotes,
            best_rate=best_rate,
            max_loan_offered=response_data.get("maxLoan"),
            valid_until=datetime.utcnow() + timedelta(hours=24),
            raw_response=response_data,
        )

    async def get_indicative_quote(self, request: QuoteRequest) -> QuoteResponse:
        """
        Get indicative quote from LendInvest API.

        Args:
            request: Standardised quote request

        Returns:
            QuoteResponse with available products and rates
        """
        if not self.is_configured:
            return QuoteResponse(
                status=QuoteStatus.ERROR,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                error_message="API not configured - missing credentials",
                error_code="NOT_CONFIGURED",
            )

        try:
            client = await self.get_client()
            payload = self._map_request_to_api(request)

            response = await client.post("/quotes", json=payload)

            if response.status_code == 401:
                return QuoteResponse(
                    status=QuoteStatus.ERROR,
                    lender_name=self.lender_name,
                    lender_id=self.lender_id,
                    error_message="API authentication failed",
                    error_code="AUTH_FAILED",
                )

            if response.status_code == 400:
                error_data = response.json()
                return QuoteResponse(
                    status=QuoteStatus.ERROR,
                    lender_name=self.lender_name,
                    lender_id=self.lender_id,
                    error_message=error_data.get("message", "Bad request"),
                    error_code="BAD_REQUEST",
                    raw_response=error_data,
                )

            response.raise_for_status()
            response_data = response.json()

            return self._parse_api_response(response_data)

        except httpx.TimeoutException:
            return QuoteResponse(
                status=QuoteStatus.ERROR,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                error_message="API request timed out",
                error_code="TIMEOUT",
            )

        except httpx.HTTPError as e:
            return QuoteResponse(
                status=QuoteStatus.ERROR,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                error_message=f"HTTP error: {str(e)}",
                error_code="HTTP_ERROR",
            )

        except Exception as e:
            return QuoteResponse(
                status=QuoteStatus.ERROR,
                lender_name=self.lender_name,
                lender_id=self.lender_id,
                error_message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN",
            )

    async def check_eligibility(self, request: QuoteRequest) -> bool:
        """
        Quick eligibility check based on known criteria.

        LendInvest general criteria (as of known data):
        - Min loan: £100,000
        - Max loan: £15,000,000 (bridging), £50,000,000 (development)
        - Max LTV: 75%
        - England & Wales only
        """
        # Basic loan amount check
        if request.loan_amount < 100000:
            return False

        if request.loan_purpose == "development":
            if request.loan_amount > 50000000:
                return False
        else:
            if request.loan_amount > 15000000:
                return False

        # LTV check if we can calculate it
        if request.property_value and request.property_value > 0:
            ltv = (request.loan_amount / request.property_value) * 100
            if ltv > 75:
                return False

        # Geography check (basic - would need full postcode lookup)
        if request.property_postcode:
            # Scotland and NI postcodes
            scottish_prefixes = ["AB", "DD", "DG", "EH", "FK", "G", "HS", "IV", "KA", "KW", "KY", "ML", "PA", "PH", "TD", "ZE"]
            ni_prefix = "BT"
            postcode_prefix = request.property_postcode.split()[0][:2].upper()

            if postcode_prefix == ni_prefix:
                return False
            if any(postcode_prefix.startswith(sp) for sp in scottish_prefixes):
                return False

        return True


# Factory function to create the integration
def create_lendinvest_integration(lender_id: int) -> LendInvestAPI:
    """Create a LendInvest API integration instance."""
    return LendInvestAPI(lender_id=lender_id, lender_name="LendInvest")
