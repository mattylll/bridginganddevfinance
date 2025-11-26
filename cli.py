#!/usr/bin/env python3
"""
Developer Finance Engine CLI

Command-line interface for managing the application.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from app.core.database import init_db, SessionLocal
from app.core.config import get_settings

console = Console()
app = typer.Typer(
    name="devfinance",
    help="Developer Finance Engine - UK Property Development Finance Platform",
)


@app.command()
def init():
    """Initialize the database."""
    console.print("[yellow]Initializing database...[/yellow]")
    init_db()
    console.print("[green]Database initialized successfully![/green]")


@app.command()
def seed():
    """Seed the database with lender data."""
    console.print("[yellow]Seeding database with lender data...[/yellow]")

    from scripts.seed_data import main as seed_main
    seed_main()

    console.print("[green]Database seeded successfully![/green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn

    console.print(Panel.fit(
        f"[green]Starting Developer Finance Engine[/green]\n"
        f"API: http://{host}:{port}\n"
        f"Docs: http://{host}:{port}/docs",
        title="Dev Finance Engine",
    ))

    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def scrape(
    lender: str = typer.Option(None, help="Specific lender slug to scrape"),
    force: bool = typer.Option(False, help="Scrape all lenders regardless of schedule"),
):
    """Run scraping operation."""
    from app.scrapers.manager import ScraperManager

    db = SessionLocal()
    try:
        manager = ScraperManager(db)

        if lender:
            console.print(f"[yellow]Scraping {lender}...[/yellow]")
            result = manager.scrape_by_slug(lender)

            if result is None:
                console.print(f"[red]Lender '{lender}' not found[/red]")
                return

            scrape_result, changes = result

            if scrape_result.success:
                console.print(f"[green]Scrape successful![/green]")
                console.print(f"Changes detected: {len(changes)}")

                for change in changes:
                    color = "red" if change.significance == "critical" else "yellow"
                    console.print(f"  [{color}]{change.description}[/{color}]")
            else:
                console.print(f"[red]Scrape failed: {scrape_result.error_message}[/red]")

        else:
            console.print("[yellow]Running full scrape...[/yellow]")
            summary = manager.scrape_all(force=force)

            console.print(f"\n[green]Scrape complete![/green]")
            console.print(f"  Lenders scraped: {summary.lenders_scraped}")
            console.print(f"  Lenders failed: {summary.lenders_failed}")
            console.print(f"  Total changes: {summary.total_changes}")
            console.print(f"  Critical changes: {summary.critical_changes}")

    finally:
        db.close()


@app.command()
def lenders(
    show_all: bool = typer.Option(False, "--all", help="Show all lenders including inactive"),
):
    """List all lenders."""
    from app.models.lender import Lender, LenderStatus

    db = SessionLocal()
    try:
        query = db.query(Lender)
        if not show_all:
            query = query.filter(Lender.status == LenderStatus.ACTIVE)

        lenders = query.all()

        table = Table(title="Lenders")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Products", style="blue")
        table.add_column("Last Scraped", style="white")

        for lender in lenders:
            table.add_row(
                str(lender.id),
                lender.name,
                lender.lender_type.value,
                lender.status.value,
                str(len(lender.products)),
                str(lender.last_scraped_at)[:10] if lender.last_scraped_at else "Never",
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def products(
    finance_type: str = typer.Option(None, help="Filter by finance type"),
    lender_id: int = typer.Option(None, help="Filter by lender ID"),
):
    """List products."""
    from app.models.product import Product, FinanceType

    db = SessionLocal()
    try:
        query = db.query(Product).filter(Product.is_active == True)

        if finance_type:
            try:
                ft = FinanceType(finance_type)
                query = query.filter(Product.finance_type == ft)
            except ValueError:
                console.print(f"[red]Invalid finance type: {finance_type}[/red]")
                console.print(f"Valid types: {[ft.value for ft in FinanceType]}")
                return

        if lender_id:
            query = query.filter(Product.lender_id == lender_id)

        products = query.all()

        table = Table(title="Products")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Rate From", style="blue")
        table.add_column("Max LTV", style="magenta")
        table.add_column("Max Loan", style="white")

        for product in products:
            table.add_row(
                str(product.id),
                product.name[:30],
                product.finance_type.value,
                f"{product.rate_from}%" if product.rate_from else "-",
                f"{product.max_ltv}%" if product.max_ltv else "-",
                f"£{product.max_loan:,}" if product.max_loan else "-",
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def search(
    loan_amount: int = typer.Argument(..., help="Loan amount required"),
    finance_type: str = typer.Option("bridging", help="Type of finance"),
    ltv: float = typer.Option(None, help="Loan to Value percentage"),
):
    """Search for matching loan products."""
    from app.models.product import FinanceType
    from app.services.loan_matcher import LoanMatcher
    from app.schemas.search import LoanSearchRequest

    try:
        ft = FinanceType(finance_type)
    except ValueError:
        console.print(f"[red]Invalid finance type: {finance_type}[/red]")
        return

    db = SessionLocal()
    try:
        request = LoanSearchRequest(
            finance_type=ft,
            loan_amount=loan_amount,
            ltv=ltv,
        )

        matcher = LoanMatcher(db)
        results = matcher.search(request)

        console.print(f"\n[green]Found {results.total_matches} matching products[/green]\n")

        if results.rate_range["min"]:
            console.print(f"Rate range: {results.rate_range['min']}% - {results.rate_range['max']}%")

        table = Table(title="Top Matches")
        table.add_column("Rank", style="cyan")
        table.add_column("Lender", style="green")
        table.add_column("Product", style="yellow")
        table.add_column("Rate", style="blue")
        table.add_column("Score", style="magenta")
        table.add_column("Issues", style="red")

        for i, match in enumerate(results.matches[:10], 1):
            issues = len(match.criteria_issues)
            table.add_row(
                str(i),
                match.lender_name[:20],
                match.product_name[:25],
                f"{match.rate_from}%" if match.rate_from else "-",
                f"{match.match_score.overall:.0f}",
                str(issues) if issues > 0 else "✓",
            )

        console.print(table)

    finally:
        db.close()


@app.command()
def status():
    """Show system status."""
    from app.scrapers.manager import ScraperManager
    from app.models.lender import Lender
    from app.models.product import Product

    db = SessionLocal()
    try:
        manager = ScraperManager(db)
        scrape_status = manager.get_scrape_status()

        lender_count = db.query(Lender).count()
        product_count = db.query(Product).filter(Product.is_active == True).count()

        panel_content = f"""
[green]System Status[/green]

[yellow]Database:[/yellow]
  Lenders: {lender_count}
  Products: {product_count}

[yellow]Scraping:[/yellow]
  Total tracked: {scrape_status['total_lenders']}
  Due for scrape: {scrape_status['due_for_scrape']}
  Interval: {scrape_status['scrape_interval_days']} days

[yellow]Recent Activity (7 days):[/yellow]
  Total scrapes: {scrape_status['recent_scrapes']['total']}
  Successful: {scrape_status['recent_scrapes']['successful']}
  Failed: {scrape_status['recent_scrapes']['failed']}
"""
        console.print(Panel(panel_content, title="Developer Finance Engine"))

    finally:
        db.close()


if __name__ == "__main__":
    app()
