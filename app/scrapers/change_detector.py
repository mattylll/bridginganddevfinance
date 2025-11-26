"""
Change Detection System

Compares scraped data with stored data to detect changes
in lender products, rates, and terms.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.lender import Lender
from app.models.product import Product
from app.models.scrape_history import ScrapeHistory, ScrapeChange, ScrapeStatus, ChangeType
from app.scrapers.base import ScrapeResult, ScrapedProduct


@dataclass
class DetectedChange:
    """A detected change in lender data."""
    change_type: ChangeType
    entity_type: str  # 'product', 'lender'
    entity_id: Optional[int]
    field_name: Optional[str]
    old_value: Any
    new_value: Any
    description: str
    significance: str  # 'low', 'normal', 'high', 'critical'


class ChangeDetector:
    """
    Detects changes between scraped data and database.

    Changes are categorized by type and significance to help
    prioritize which changes need attention.
    """

    # Thresholds for rate changes
    RATE_CHANGE_THRESHOLD = 0.05  # 0.05% change is significant
    RATE_CRITICAL_THRESHOLD = 0.25  # 0.25% change is critical

    def __init__(self, db: Session):
        self.db = db

    def detect_changes(
        self,
        lender: Lender,
        scrape_result: ScrapeResult,
    ) -> List[DetectedChange]:
        """
        Detect changes between scraped data and stored data.

        Args:
            lender: The lender entity
            scrape_result: Result from scraping

        Returns:
            List of detected changes
        """
        changes = []

        # Get existing products for this lender
        existing_products = {p.name.lower(): p for p in lender.products}
        scraped_products = {p.name.lower(): p for p in scrape_result.products}

        # Check for new products
        for name, scraped in scraped_products.items():
            if name not in existing_products:
                changes.append(DetectedChange(
                    change_type=ChangeType.NEW_PRODUCT,
                    entity_type="product",
                    entity_id=None,
                    field_name=None,
                    old_value=None,
                    new_value=scraped.name,
                    description=f"New product detected: {scraped.name}",
                    significance="high",
                ))

        # Check for removed products
        for name, existing in existing_products.items():
            if name not in scraped_products and existing.is_active:
                changes.append(DetectedChange(
                    change_type=ChangeType.PRODUCT_REMOVED,
                    entity_type="product",
                    entity_id=existing.id,
                    field_name=None,
                    old_value=existing.name,
                    new_value=None,
                    description=f"Product may have been removed: {existing.name}",
                    significance="high",
                ))

        # Check for changes in existing products
        for name, scraped in scraped_products.items():
            if name in existing_products:
                existing = existing_products[name]
                product_changes = self._compare_products(existing, scraped)
                changes.extend(product_changes)

        return changes

    def _compare_products(
        self,
        existing: Product,
        scraped: ScrapedProduct
    ) -> List[DetectedChange]:
        """Compare an existing product with scraped data."""
        changes = []

        # Compare rates
        if scraped.rate_from is not None and existing.rate_from is not None:
            rate_diff = scraped.rate_from - existing.rate_from

            if abs(rate_diff) >= self.RATE_CHANGE_THRESHOLD:
                if rate_diff > 0:
                    change_type = ChangeType.RATE_INCREASE
                    description = f"Rate increased from {existing.rate_from}% to {scraped.rate_from}%"
                else:
                    change_type = ChangeType.RATE_DECREASE
                    description = f"Rate decreased from {existing.rate_from}% to {scraped.rate_from}%"

                significance = "critical" if abs(rate_diff) >= self.RATE_CRITICAL_THRESHOLD else "high"

                changes.append(DetectedChange(
                    change_type=change_type,
                    entity_type="product",
                    entity_id=existing.id,
                    field_name="rate_from",
                    old_value=existing.rate_from,
                    new_value=scraped.rate_from,
                    description=description,
                    significance=significance,
                ))

        # Compare LTV
        if scraped.max_ltv is not None and existing.max_ltv is not None:
            if scraped.max_ltv != existing.max_ltv:
                changes.append(DetectedChange(
                    change_type=ChangeType.LTV_CHANGE,
                    entity_type="product",
                    entity_id=existing.id,
                    field_name="max_ltv",
                    old_value=existing.max_ltv,
                    new_value=scraped.max_ltv,
                    description=f"Max LTV changed from {existing.max_ltv}% to {scraped.max_ltv}%",
                    significance="high",
                ))

        # Compare fees
        if scraped.arrangement_fee_percent is not None and existing.arrangement_fee_percent is not None:
            if scraped.arrangement_fee_percent != existing.arrangement_fee_percent:
                changes.append(DetectedChange(
                    change_type=ChangeType.FEE_CHANGE,
                    entity_type="product",
                    entity_id=existing.id,
                    field_name="arrangement_fee_percent",
                    old_value=existing.arrangement_fee_percent,
                    new_value=scraped.arrangement_fee_percent,
                    description=f"Arrangement fee changed from {existing.arrangement_fee_percent}% to {scraped.arrangement_fee_percent}%",
                    significance="normal",
                ))

        # Compare loan amounts
        if scraped.max_loan is not None and existing.max_loan is not None:
            if scraped.max_loan != existing.max_loan:
                changes.append(DetectedChange(
                    change_type=ChangeType.CRITERIA_CHANGE,
                    entity_type="product",
                    entity_id=existing.id,
                    field_name="max_loan",
                    old_value=existing.max_loan,
                    new_value=scraped.max_loan,
                    description=f"Max loan changed from £{existing.max_loan:,} to £{scraped.max_loan:,}",
                    significance="normal",
                ))

        return changes

    def record_scrape(
        self,
        lender: Lender,
        scrape_result: ScrapeResult,
        changes: List[DetectedChange],
    ) -> ScrapeHistory:
        """
        Record the scrape result and changes in the database.

        Args:
            lender: The lender entity
            scrape_result: Result from scraping
            changes: Detected changes

        Returns:
            ScrapeHistory record
        """
        # Determine status
        if not scrape_result.success:
            status = ScrapeStatus.FAILED
        elif not changes:
            status = ScrapeStatus.NO_CHANGES
        else:
            status = ScrapeStatus.SUCCESS

        # Create history record
        history = ScrapeHistory(
            lender_id=lender.id,
            scrape_started_at=scrape_result.timestamp,
            scrape_completed_at=datetime.utcnow(),
            status=status,
            urls_scraped=scrape_result.urls_scraped,
            pages_scraped=len(scrape_result.urls_scraped),
            changes_detected=len(changes),
            raw_html_hash=scrape_result.content_hash,
            error_message=scrape_result.error_message,
        )

        self.db.add(history)
        self.db.flush()

        # Record each change
        for change in changes:
            change_record = ScrapeChange(
                scrape_history_id=history.id,
                change_type=change.change_type,
                entity_type=change.entity_type,
                entity_id=change.entity_id,
                field_name=change.field_name,
                old_value=str(change.old_value) if change.old_value is not None else None,
                new_value=str(change.new_value) if change.new_value is not None else None,
                description=change.description,
                significance=change.significance,
            )
            self.db.add(change_record)

        # Update lender's last scraped timestamp
        lender.last_scraped_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(history)

        return history

    def apply_changes(
        self,
        changes: List[DetectedChange],
        auto_apply: bool = False
    ) -> List[Tuple[DetectedChange, bool]]:
        """
        Apply detected changes to the database.

        Args:
            changes: List of changes to apply
            auto_apply: If True, automatically apply low-significance changes

        Returns:
            List of (change, applied) tuples
        """
        results = []

        for change in changes:
            applied = False

            # Auto-apply non-critical changes if enabled
            if auto_apply and change.significance in ["low", "normal"]:
                if change.entity_type == "product" and change.entity_id:
                    product = self.db.query(Product).filter(
                        Product.id == change.entity_id
                    ).first()

                    if product and change.field_name:
                        setattr(product, change.field_name, change.new_value)
                        product.last_verified_at = datetime.utcnow()
                        applied = True

            results.append((change, applied))

        if auto_apply:
            self.db.commit()

        return results

    def get_change_summary(
        self,
        lender_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get a summary of changes over a period.

        Args:
            lender_id: Optional lender to filter by
            days: Number of days to look back

        Returns:
            Summary statistics
        """
        from datetime import timedelta
        from sqlalchemy import func

        cutoff = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(ScrapeChange).filter(
            ScrapeChange.created_at >= cutoff
        )

        if lender_id:
            query = query.join(ScrapeHistory).filter(
                ScrapeHistory.lender_id == lender_id
            )

        changes = query.all()

        # Count by type
        by_type = {}
        for change in changes:
            type_name = change.change_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Count by significance
        by_significance = {}
        for change in changes:
            by_significance[change.significance] = by_significance.get(change.significance, 0) + 1

        return {
            "total_changes": len(changes),
            "by_type": by_type,
            "by_significance": by_significance,
            "period_days": days,
        }
