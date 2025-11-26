"""
Task Scheduler

Handles scheduled tasks like weekly scraping.
"""

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.scrapers.manager import ScraperManager


settings = get_settings()

# Global scheduler instance
scheduler = BackgroundScheduler()


def run_weekly_scrape():
    """
    Run the weekly scrape job.

    This is called by the scheduler every week.
    """
    print(f"[{datetime.utcnow()}] Starting weekly scrape...")

    db = SessionLocal()
    try:
        manager = ScraperManager(db)
        summary = manager.scrape_all(force=False, auto_apply_changes=False)

        print(f"[{datetime.utcnow()}] Weekly scrape complete:")
        print(f"  - Lenders scraped: {summary.lenders_scraped}")
        print(f"  - Lenders failed: {summary.lenders_failed}")
        print(f"  - Changes detected: {summary.total_changes}")
        print(f"  - Critical changes: {summary.critical_changes}")

        if summary.errors:
            print(f"  - Errors:")
            for error in summary.errors[:5]:
                print(f"    - {error}")

        # TODO: Send notification if there are critical changes
        if summary.critical_changes > 0:
            send_change_notification(summary)

    except Exception as e:
        print(f"[{datetime.utcnow()}] Weekly scrape failed: {e}")
    finally:
        db.close()


def send_change_notification(summary):
    """
    Send notification about important changes.

    TODO: Implement email/webhook notifications
    """
    print(f"[NOTIFICATION] {summary.critical_changes} critical changes detected!")


def start_scheduler():
    """Start the background scheduler."""
    if scheduler.running:
        return

    # Weekly scrape - every Sunday at 2 AM
    scheduler.add_job(
        run_weekly_scrape,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_scrape",
        name="Weekly Lender Scrape",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduler started - weekly scrape scheduled for Sunday 2:00 AM")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")


def run_scrape_now():
    """Run a scrape immediately (for manual triggers)."""
    run_weekly_scrape()
