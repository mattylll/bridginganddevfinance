"""
Loan Matching Engine

This is the core intelligence of the system - it matches loan requirements
to available products and scores them based on fit, rate, and lender quality.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.lender import Lender, LenderStatus
from app.models.product import Product, FinanceType, ProductCriteria, GeographicPricing
from app.models.rating import LenderRating, RatingCategory
from app.schemas.search import (
    LoanSearchRequest,
    LoanSearchResponse,
    MatchedProduct,
    MatchScore,
)


class LoanMatcher:
    """
    Loan matching engine that finds and scores suitable finance products.

    The matching process:
    1. Filter products by hard criteria (loan amount, finance type, etc.)
    2. Check soft criteria (experience, planning status, etc.)
    3. Score each product on multiple dimensions
    4. Apply any geographic or type-specific adjustments
    5. Return ranked results with match analysis
    """

    def __init__(self, db: Session):
        self.db = db

    def search(self, request: LoanSearchRequest) -> LoanSearchResponse:
        """
        Search for matching loan products.

        Args:
            request: Loan search parameters

        Returns:
            LoanSearchResponse with matched and scored products
        """
        search_id = str(uuid4())[:8]

        # Calculate derived metrics if not provided
        request = self._calculate_metrics(request)

        # Get candidate products
        candidates = self._get_candidate_products(request)

        # Score and filter candidates
        matched_products = []
        for product, lender in candidates:
            match = self._evaluate_product(product, lender, request)
            if match:
                matched_products.append(match)

        # Sort by overall score
        matched_products.sort(key=lambda x: x.match_score.overall, reverse=True)

        # Limit results
        matched_products = matched_products[:request.limit]

        # Build response
        return self._build_response(search_id, request, matched_products)

    def _calculate_metrics(self, request: LoanSearchRequest) -> LoanSearchRequest:
        """Calculate LTV, LTC, LTGDV if not provided."""
        # Calculate LTV if we have property value
        if request.ltv is None and request.property_value:
            request.ltv = (request.loan_amount / request.property_value) * 100

        # Calculate LTC if we have costs
        if request.ltc is None:
            total_cost = (request.purchase_price or 0) + (request.development_costs or 0)
            if total_cost > 0:
                request.ltc = (request.loan_amount / total_cost) * 100

        # Calculate LTGDV if we have GDV
        if request.ltgdv is None and request.gdv:
            request.ltgdv = (request.loan_amount / request.gdv) * 100

        return request

    def _get_candidate_products(
        self, request: LoanSearchRequest
    ) -> List[Tuple[Product, Lender]]:
        """
        Get initial set of candidate products based on hard filters.

        This does the database query with filters that must be met.
        """
        query = (
            self.db.query(Product, Lender)
            .join(Lender, Product.lender_id == Lender.id)
            .filter(Lender.status == LenderStatus.ACTIVE)
            .filter(Product.is_active == True)
        )

        # Filter by finance type
        query = query.filter(Product.finance_type == request.finance_type)

        # Filter by loan amount range
        query = query.filter(
            (Product.min_loan == None) | (Product.min_loan <= request.loan_amount)
        )
        query = query.filter(
            (Product.max_loan == None) | (Product.max_loan >= request.loan_amount)
        )

        # Include inactive if requested
        if not request.include_inactive:
            query = query.filter(Product.is_active == True)

        return query.all()

    def _evaluate_product(
        self,
        product: Product,
        lender: Lender,
        request: LoanSearchRequest
    ) -> Optional[MatchedProduct]:
        """
        Evaluate a single product against the search criteria.

        Returns None if product doesn't meet minimum criteria.
        """
        criteria_issues = []
        criteria_warnings = []

        # Check LTV/LTC/LTGDV limits
        if request.ltv and product.max_ltv:
            if request.ltv > product.max_ltv:
                criteria_issues.append(
                    f"LTV {request.ltv:.1f}% exceeds max {product.max_ltv:.1f}%"
                )

        if request.ltc and product.max_ltc:
            if request.ltc > product.max_ltc:
                criteria_issues.append(
                    f"LTC {request.ltc:.1f}% exceeds max {product.max_ltc:.1f}%"
                )

        if request.ltgdv and product.max_ltgdv:
            if request.ltgdv > product.max_ltgdv:
                criteria_issues.append(
                    f"LTGDV {request.ltgdv:.1f}% exceeds max {product.max_ltgdv:.1f}%"
                )

        # Check detailed criteria if available
        if product.criteria:
            criteria = product.criteria
            self._check_borrower_criteria(criteria, request, criteria_issues, criteria_warnings)
            self._check_property_criteria(criteria, request, criteria_issues, criteria_warnings)
            self._check_planning_criteria(criteria, request, criteria_issues, criteria_warnings)

        # Check rate against max acceptable
        if request.max_rate and product.rate_from:
            if product.rate_from > request.max_rate:
                criteria_issues.append(
                    f"Rate {product.rate_from}% exceeds max acceptable {request.max_rate}%"
                )

        # If there are hard issues, still return but mark as not matching
        matches_criteria = len(criteria_issues) == 0

        # Calculate scores
        match_score = self._calculate_scores(product, lender, request, matches_criteria)

        # Get effective rate (with any adjustments)
        effective_rate = self._get_effective_rate(product, request)

        # Get lender ratings
        overall_rating = self._get_lender_rating(lender.id, RatingCategory.OVERALL)
        speed_rating = self._get_lender_rating(lender.id, RatingCategory.SPEED_TO_OFFER)

        # Estimate total cost over term
        total_cost = self._estimate_total_cost(product, request)

        return MatchedProduct(
            product_id=product.id,
            product_name=product.name,
            finance_type=product.finance_type,
            lender_id=lender.id,
            lender_name=lender.name,
            lender_type=lender.lender_type.value,
            rate_from=product.rate_from,
            rate_to=product.rate_to,
            rate_type=product.rate_type,
            effective_rate=effective_rate,
            arrangement_fee_percent=product.arrangement_fee_percent,
            exit_fee_percent=product.exit_fee_percent,
            total_cost_estimate=total_cost,
            max_ltv=product.max_ltv,
            max_ltc=product.max_ltc,
            max_ltgdv=product.max_ltgdv,
            max_loan=product.max_loan,
            match_score=match_score,
            matches_criteria=matches_criteria,
            criteria_issues=criteria_issues,
            criteria_warnings=criteria_warnings,
            lender_overall_rating=overall_rating,
            lender_speed_rating=speed_rating,
            source_url=product.source_url,
            last_verified_at=product.last_verified_at,
        )

    def _check_borrower_criteria(
        self,
        criteria: ProductCriteria,
        request: LoanSearchRequest,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """Check borrower-related criteria."""
        # Experience check
        if criteria.min_experience_units and request.experience_level is not None:
            if request.experience_level < criteria.min_experience_units:
                issues.append(
                    f"Requires {criteria.min_experience_units} completed projects, "
                    f"borrower has {request.experience_level}"
                )

        # First-time developer
        if request.is_first_time_developer:
            if criteria.accepts_first_time_developers is False:
                issues.append("Does not accept first-time developers")

        # Foreign national
        if request.is_foreign_national:
            if criteria.accepts_foreign_nationals is False:
                issues.append("Does not accept foreign nationals")

        # Borrower type
        if request.borrower_type:
            borrower_type_map = {
                "spv": criteria.accepts_spv,
                "ltd": criteria.accepts_ltd_company,
                "llp": criteria.accepts_llp,
                "individual": criteria.accepts_individuals,
            }
            accepts = borrower_type_map.get(request.borrower_type)
            if accepts is False:
                issues.append(f"Does not accept {request.borrower_type} borrowers")

    def _check_property_criteria(
        self,
        criteria: ProductCriteria,
        request: LoanSearchRequest,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """Check property-related criteria."""
        # GDV check
        if criteria.min_gdv and request.gdv:
            if request.gdv < criteria.min_gdv:
                issues.append(
                    f"GDV £{request.gdv:,} below minimum £{criteria.min_gdv:,}"
                )

        if criteria.max_gdv and request.gdv:
            if request.gdv > criteria.max_gdv:
                issues.append(
                    f"GDV £{request.gdv:,} exceeds maximum £{criteria.max_gdv:,}"
                )

        # Geographic exclusions
        if criteria.excluded_postcodes and request.postcode:
            prefix = request.postcode[:2].upper()
            if prefix in criteria.excluded_postcodes:
                issues.append(f"Postcode area {prefix} is excluded")

        if criteria.excluded_regions and request.region:
            if request.region in criteria.excluded_regions:
                issues.append(f"Region {request.region} is excluded")

    def _check_planning_criteria(
        self,
        criteria: ProductCriteria,
        request: LoanSearchRequest,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """Check planning status criteria."""
        if not request.planning_status:
            return

        status_map = {
            "none": criteria.accepts_no_planning,
            "outline": criteria.accepts_outline_planning,
            "full": criteria.accepts_full_planning,
            "permitted_development": criteria.accepts_permitted_development,
        }

        accepts = status_map.get(request.planning_status)
        if accepts is False:
            issues.append(f"Does not accept {request.planning_status} planning status")
        elif accepts is None:
            warnings.append(f"Planning status {request.planning_status} not confirmed")

    def _calculate_scores(
        self,
        product: Product,
        lender: Lender,
        request: LoanSearchRequest,
        matches_criteria: bool
    ) -> MatchScore:
        """
        Calculate multi-dimensional match scores.

        Each dimension is scored 0-100, then combined into overall score.
        """
        # Rate score (lower is better)
        rate_score = 100.0
        if product.rate_from:
            # Assume rates range from 0.4% to 2% monthly for bridging, 6-20% annual for dev
            if product.rate_type == "monthly":
                # Monthly rate 0.4-2.0%
                rate_score = max(0, 100 - ((product.rate_from - 0.4) / 1.6) * 100)
            else:
                # Annual rate 6-20%
                rate_score = max(0, 100 - ((product.rate_from - 6) / 14) * 100)

        # LTV score (based on headroom vs requested)
        ltv_score = 100.0
        if request.ltv and product.max_ltv:
            headroom = product.max_ltv - request.ltv
            if headroom < 0:
                ltv_score = 0
            elif headroom < 5:
                ltv_score = 50 + headroom * 10
            else:
                ltv_score = 100

        # Criteria score
        criteria_score = 100.0 if matches_criteria else 30.0

        # Lender rating score
        lender_rating = self._get_lender_rating(lender.id, RatingCategory.OVERALL)
        lender_rating_score = lender_rating if lender_rating else 70.0

        # Calculate overall (weighted average)
        weights = {
            "rate": 0.35,
            "ltv": 0.20,
            "criteria": 0.25,
            "lender": 0.20,
        }

        overall = (
            rate_score * weights["rate"] +
            ltv_score * weights["ltv"] +
            criteria_score * weights["criteria"] +
            lender_rating_score * weights["lender"]
        )

        return MatchScore(
            overall=round(overall, 1),
            rate_score=round(rate_score, 1),
            ltv_score=round(ltv_score, 1),
            criteria_score=round(criteria_score, 1),
            lender_rating_score=round(lender_rating_score, 1),
        )

    def _get_effective_rate(
        self, product: Product, request: LoanSearchRequest
    ) -> Optional[float]:
        """
        Get effective rate after any geographic or type adjustments.

        Phase 2 feature - lenders can set custom pricing by location/type.
        """
        if not product.rate_from:
            return None

        effective_rate = product.rate_from

        # Check for geographic adjustments
        if request.postcode or request.region:
            adjustments = (
                self.db.query(GeographicPricing)
                .filter(GeographicPricing.product_id == product.id)
                .filter(GeographicPricing.is_active == True)
                .all()
            )

            for adj in adjustments:
                if request.postcode and adj.region_type == "postcode":
                    if request.postcode.upper().startswith(adj.region_value.upper()):
                        effective_rate += adj.rate_adjustment

                if request.region and adj.region_type == "region":
                    if request.region.lower() == adj.region_value.lower():
                        effective_rate += adj.rate_adjustment

        return round(effective_rate, 2)

    def _get_lender_rating(
        self, lender_id: int, category: RatingCategory
    ) -> Optional[float]:
        """Get a specific rating for a lender."""
        rating = (
            self.db.query(LenderRating)
            .filter(LenderRating.lender_id == lender_id)
            .filter(LenderRating.category == category)
            .filter(LenderRating.is_current == True)
            .first()
        )
        return rating.score if rating else None

    def _estimate_total_cost(
        self, product: Product, request: LoanSearchRequest
    ) -> Optional[float]:
        """
        Estimate total cost of finance over the term.

        Includes interest, arrangement fee, and exit fee.
        """
        if not product.rate_from:
            return None

        term_months = request.term_months or 12
        loan_amount = request.loan_amount

        # Calculate interest
        if product.rate_type == "monthly":
            monthly_rate = product.rate_from / 100
            total_interest = loan_amount * monthly_rate * term_months
        else:
            annual_rate = product.rate_from / 100
            total_interest = loan_amount * annual_rate * (term_months / 12)

        # Arrangement fee
        arrangement_fee = 0
        if product.arrangement_fee_percent:
            arrangement_fee = loan_amount * (product.arrangement_fee_percent / 100)

        # Exit fee
        exit_fee = 0
        if product.exit_fee_percent:
            exit_fee = loan_amount * (product.exit_fee_percent / 100)

        total_cost = total_interest + arrangement_fee + exit_fee
        return round(total_cost, 2)

    def _build_response(
        self,
        search_id: str,
        request: LoanSearchRequest,
        matches: List[MatchedProduct]
    ) -> LoanSearchResponse:
        """Build the final search response with aggregated stats."""
        # Calculate rate range
        rates = [m.rate_from for m in matches if m.rate_from is not None]
        rate_range = {
            "min": min(rates) if rates else None,
            "max": max(rates) if rates else None,
            "avg": round(sum(rates) / len(rates), 2) if rates else None,
        }

        # Count unique lenders and products
        lender_ids = set(m.lender_id for m in matches)
        product_count = len(matches)

        # Find best options
        best_rate = None
        best_match = None
        fastest_lender = None

        if matches:
            # Best rate
            rate_sorted = sorted(
                [m for m in matches if m.rate_from],
                key=lambda x: x.rate_from
            )
            if rate_sorted:
                best_rate = rate_sorted[0]

            # Best overall match
            best_match = matches[0]  # Already sorted by overall score

            # Fastest lender
            speed_sorted = sorted(
                [m for m in matches if m.lender_speed_rating],
                key=lambda x: x.lender_speed_rating,
                reverse=True
            )
            if speed_sorted:
                fastest_lender = speed_sorted[0]

        return LoanSearchResponse(
            search_id=search_id,
            search_timestamp=datetime.utcnow(),
            total_matches=len(matches),
            filters_applied={
                "finance_type": request.finance_type.value,
                "loan_amount": request.loan_amount,
                "ltv": request.ltv,
                "ltc": request.ltc,
                "ltgdv": request.ltgdv,
                "region": request.region,
                "property_type": request.property_type,
            },
            matches=matches,
            rate_range=rate_range,
            lender_count=len(lender_ids),
            product_count=product_count,
            best_rate=best_rate,
            best_match=best_match,
            fastest_lender=fastest_lender,
        )
