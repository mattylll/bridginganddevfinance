"""
Scraping API Routes

Endpoints for managing web scraping operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.scrapers.manager import ScraperManager
from app.scrapers.change_detector import ChangeDetector


router = APIRouter()


@router.get("/status")
async def get_scrape_status(
    db: Session = Depends(get_db),
):
    """
    Get the current status of the scraping system.

    Returns information about:
    - Total lenders being tracked
    - Lenders due for scraping
    - Recent scrape statistics
    """
    manager = ScraperManager(db)
    return manager.get_scrape_status()


@router.get("/due")
async def get_lenders_due_for_scrape(
    db: Session = Depends(get_db),
):
    """Get list of lenders that are due for scraping."""
    manager = ScraperManager(db)
    lenders = manager.get_lenders_due_for_scrape()

    return {
        "count": len(lenders),
        "lenders": [
            {
                "id": l.id,
                "name": l.name,
                "slug": l.slug,
                "last_scraped_at": l.last_scraped_at,
                "website_url": l.website_url,
            }
            for l in lenders
        ],
    }


@router.post("/run")
async def run_scrape(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Scrape all lenders regardless of schedule"),
    lender_slug: Optional[str] = Query(None, description="Specific lender to scrape"),
    db: Session = Depends(get_db),
):
    """
    Trigger a scrape operation.

    Can be run for all due lenders or a specific lender.
    Runs in the background for full scrapes.
    """
    manager = ScraperManager(db)

    if lender_slug:
        # Scrape specific lender (synchronous for single lender)
        result = manager.scrape_by_slug(lender_slug)

        if result is None:
            raise HTTPException(status_code=404, detail=f"Lender '{lender_slug}' not found")

        scrape_result, changes = result

        return {
            "status": "completed",
            "lender": lender_slug,
            "success": scrape_result.success,
            "changes_detected": len(changes),
            "changes": [
                {
                    "type": c.change_type.value,
                    "description": c.description,
                    "significance": c.significance,
                }
                for c in changes
            ],
            "error": scrape_result.error_message,
        }

    # Full scrape - run in background
    def run_full_scrape():
        manager = ScraperManager(db)
        manager.scrape_all(force=force)

    background_tasks.add_task(run_full_scrape)

    due_count = len(manager.get_lenders_due_for_scrape())

    return {
        "status": "started",
        "message": f"Scrape started for {due_count if not force else 'all'} lenders",
        "force": force,
    }


@router.get("/changes")
async def get_recent_changes(
    lender_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    significance: Optional[str] = Query(None, description="Filter by significance: low, normal, high, critical"),
    db: Session = Depends(get_db),
):
    """
    Get recent changes detected by scraping.

    Returns a summary of changes over the specified period.
    """
    detector = ChangeDetector(db)
    summary = detector.get_change_summary(lender_id=lender_id, days=days)

    # Get actual change records for details
    from datetime import datetime, timedelta
    from app.models.scrape_history import ScrapeChange, ScrapeHistory

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(ScrapeChange).filter(ScrapeChange.created_at >= cutoff)

    if lender_id:
        query = query.join(ScrapeHistory).filter(ScrapeHistory.lender_id == lender_id)

    if significance:
        query = query.filter(ScrapeChange.significance == significance)

    changes = query.order_by(ScrapeChange.created_at.desc()).limit(100).all()

    return {
        "summary": summary,
        "recent_changes": [
            {
                "id": c.id,
                "type": c.change_type.value,
                "entity_type": c.entity_type,
                "field": c.field_name,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "description": c.description,
                "significance": c.significance,
                "created_at": c.created_at,
            }
            for c in changes
        ],
    }


@router.get("/history/{lender_id}")
async def get_scrape_history(
    lender_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get scrape history for a specific lender."""
    from app.models.scrape_history import ScrapeHistory

    history = (
        db.query(ScrapeHistory)
        .filter(ScrapeHistory.lender_id == lender_id)
        .order_by(ScrapeHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "lender_id": lender_id,
        "history": [
            {
                "id": h.id,
                "status": h.status.value,
                "started_at": h.scrape_started_at,
                "completed_at": h.scrape_completed_at,
                "pages_scraped": h.pages_scraped,
                "changes_detected": h.changes_detected,
                "error": h.error_message,
            }
            for h in history
        ],
    }
