"""
Dashboard API Routes

Endpoints for the admin dashboard and analytics.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.lender import Lender, LenderStatus, LenderType
from app.models.product import Product, FinanceType
from app.models.scrape_history import ScrapeHistory, ScrapeChange, ScrapeStatus
from app.models.rating import LenderRating, RatingCategory


router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
):
    """
    Get dashboard overview statistics.

    Provides a high-level view of the system status.
    """
    # Lender stats
    total_lenders = db.query(Lender).count()
    active_lenders = db.query(Lender).filter(Lender.status == LenderStatus.ACTIVE).count()

    # Product stats
    total_products = db.query(Product).filter(Product.is_active == True).count()

    products_by_type = (
        db.query(Product.finance_type, func.count(Product.id))
        .filter(Product.is_active == True)
        .group_by(Product.finance_type)
        .all()
    )

    # Lenders by type
    lenders_by_type = (
        db.query(Lender.lender_type, func.count(Lender.id))
        .filter(Lender.status == LenderStatus.ACTIVE)
        .group_by(Lender.lender_type)
        .all()
    )

    # Recent scraping activity
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_scrapes = db.query(ScrapeHistory).filter(ScrapeHistory.created_at >= week_ago).count()
    recent_changes = db.query(ScrapeChange).filter(ScrapeChange.created_at >= week_ago).count()

    # Critical changes in last 7 days
    critical_changes = (
        db.query(ScrapeChange)
        .filter(ScrapeChange.created_at >= week_ago)
        .filter(ScrapeChange.significance == "critical")
        .count()
    )

    return {
        "lenders": {
            "total": total_lenders,
            "active": active_lenders,
            "by_type": {lt.value: count for lt, count in lenders_by_type},
        },
        "products": {
            "total": total_products,
            "by_type": {ft.value: count for ft, count in products_by_type},
        },
        "scraping": {
            "scrapes_last_7_days": recent_scrapes,
            "changes_last_7_days": recent_changes,
            "critical_changes": critical_changes,
        },
        "generated_at": datetime.utcnow(),
    }


@router.get("/rate-trends")
async def get_rate_trends(
    finance_type: Optional[FinanceType] = None,
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Get rate trend data over time.

    Shows how average rates have changed based on scrape history.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Get rate changes from scrape history
    query = (
        db.query(ScrapeChange)
        .filter(ScrapeChange.created_at >= cutoff)
        .filter(ScrapeChange.change_type.in_(["rate_increase", "rate_decrease"]))
    )

    changes = query.all()

    # Group changes by week
    weekly_changes = {}
    for change in changes:
        week = change.created_at.strftime("%Y-W%W")
        if week not in weekly_changes:
            weekly_changes[week] = {"increases": 0, "decreases": 0}

        if change.change_type.value == "rate_increase":
            weekly_changes[week]["increases"] += 1
        else:
            weekly_changes[week]["decreases"] += 1

    # Current average rates by finance type
    current_rates = {}
    for ft in FinanceType:
        products = (
            db.query(Product)
            .filter(Product.finance_type == ft)
            .filter(Product.is_active == True)
            .filter(Product.rate_from != None)
            .all()
        )

        if products:
            rates = [p.rate_from for p in products]
            current_rates[ft.value] = {
                "min": min(rates),
                "max": max(rates),
                "avg": round(sum(rates) / len(rates), 2),
                "count": len(rates),
            }

    return {
        "current_rates": current_rates,
        "weekly_changes": weekly_changes,
        "period_days": days,
    }


@router.get("/lender-rankings")
async def get_lender_rankings(
    category: Optional[RatingCategory] = None,
    finance_type: Optional[FinanceType] = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get lender rankings by various metrics.

    Rankings can be filtered by rating category and finance type.
    """
    # Default to overall rating
    if category is None:
        category = RatingCategory.OVERALL

    # Get ratings
    query = (
        db.query(LenderRating, Lender)
        .join(Lender, LenderRating.lender_id == Lender.id)
        .filter(LenderRating.category == category)
        .filter(LenderRating.is_current == True)
        .filter(Lender.status == LenderStatus.ACTIVE)
        .order_by(LenderRating.score.desc())
    )

    # Filter by finance type if specified
    if finance_type:
        lender_ids = (
            db.query(Product.lender_id)
            .filter(Product.finance_type == finance_type)
            .filter(Product.is_active == True)
            .distinct()
        )
        query = query.filter(Lender.id.in_(lender_ids))

    results = query.limit(limit).all()

    return {
        "category": category.value,
        "finance_type": finance_type.value if finance_type else None,
        "rankings": [
            {
                "rank": i + 1,
                "lender_id": lender.id,
                "lender_name": lender.name,
                "lender_slug": lender.slug,
                "lender_type": lender.lender_type.value,
                "score": rating.score,
                "confidence": rating.confidence,
            }
            for i, (rating, lender) in enumerate(results)
        ],
    }


@router.get("/market-coverage")
async def get_market_coverage(
    db: Session = Depends(get_db),
):
    """
    Get market coverage analysis.

    Shows what loan sizes and LTVs are available in the market.
    """
    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .all()
    )

    # Analyze loan size coverage
    loan_ranges = {
        "under_500k": 0,
        "500k_1m": 0,
        "1m_5m": 0,
        "5m_25m": 0,
        "25m_plus": 0,
    }

    ltv_ranges = {
        "under_60": 0,
        "60_70": 0,
        "70_80": 0,
        "80_plus": 0,
    }

    for p in products:
        # Loan size
        if p.max_loan:
            if p.max_loan < 500000:
                loan_ranges["under_500k"] += 1
            elif p.max_loan < 1000000:
                loan_ranges["500k_1m"] += 1
            elif p.max_loan < 5000000:
                loan_ranges["1m_5m"] += 1
            elif p.max_loan < 25000000:
                loan_ranges["5m_25m"] += 1
            else:
                loan_ranges["25m_plus"] += 1

        # LTV
        if p.max_ltv:
            if p.max_ltv < 60:
                ltv_ranges["under_60"] += 1
            elif p.max_ltv < 70:
                ltv_ranges["60_70"] += 1
            elif p.max_ltv < 80:
                ltv_ranges["70_80"] += 1
            else:
                ltv_ranges["80_plus"] += 1

    return {
        "total_products": len(products),
        "loan_size_coverage": loan_ranges,
        "ltv_coverage": ltv_ranges,
        "finance_type_coverage": {
            ft.value: sum(1 for p in products if p.finance_type == ft)
            for ft in FinanceType
        },
    }


@router.get("/alerts")
async def get_system_alerts(
    db: Session = Depends(get_db),
):
    """
    Get system alerts and notifications.

    Returns important items that need attention.
    """
    alerts = []

    # Check for lenders that haven't been scraped recently
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    stale_lenders = (
        db.query(Lender)
        .filter(Lender.status == LenderStatus.ACTIVE)
        .filter(Lender.website_url != None)
        .filter(
            (Lender.last_scraped_at == None) |
            (Lender.last_scraped_at < two_weeks_ago)
        )
        .all()
    )

    if stale_lenders:
        alerts.append({
            "type": "warning",
            "title": "Stale Lender Data",
            "message": f"{len(stale_lenders)} lenders haven't been scraped in over 2 weeks",
            "count": len(stale_lenders),
            "lenders": [l.name for l in stale_lenders[:5]],
        })

    # Check for recent critical changes
    week_ago = datetime.utcnow() - timedelta(days=7)
    critical_changes = (
        db.query(ScrapeChange)
        .filter(ScrapeChange.created_at >= week_ago)
        .filter(ScrapeChange.significance == "critical")
        .all()
    )

    if critical_changes:
        alerts.append({
            "type": "critical",
            "title": "Critical Rate Changes",
            "message": f"{len(critical_changes)} critical changes detected in the last 7 days",
            "count": len(critical_changes),
            "changes": [c.description for c in critical_changes[:5]],
        })

    # Check for failed scrapes
    day_ago = datetime.utcnow() - timedelta(days=1)
    failed_scrapes = (
        db.query(ScrapeHistory)
        .filter(ScrapeHistory.created_at >= day_ago)
        .filter(ScrapeHistory.status == ScrapeStatus.FAILED)
        .all()
    )

    if failed_scrapes:
        alerts.append({
            "type": "error",
            "title": "Failed Scrapes",
            "message": f"{len(failed_scrapes)} scrape operations failed in the last 24 hours",
            "count": len(failed_scrapes),
        })

    return {
        "alerts": alerts,
        "generated_at": datetime.utcnow(),
    }
