# Developer Finance Engine

A comprehensive loan comparison and matching platform for UK property development finance.

## Features

- **Lender Database**: Comprehensive database of UK bridging and development finance lenders
- **Loan Matching Engine**: Intelligent matching of deals to suitable lenders based on criteria
- **Rate Tracking**: Automated weekly monitoring of lender websites for rate changes
- **Change Detection**: Alerts when lenders change rates, LTVs, or criteria
- **Lender Ratings**: Score and rank lenders based on performance metrics
- **API & Dashboard**: Full REST API and web dashboard for easy access

## Finance Types Supported

- Bridging Finance
- Development Finance
- Mezzanine Finance
- Equity Funding
- Joint Venture Finance
- Developer Exit Finance
- Refurbishment Finance
- Auction Finance
- Land Finance

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python cli.py init
python cli.py seed
```

### 3. Run the Server

```bash
python main.py
```

Or with CLI:

```bash
python cli.py serve --reload
```

The API will be available at:
- Dashboard: http://localhost:8000
- API Docs: http://localhost:8000/docs

## CLI Commands

```bash
# Initialize database
python cli.py init

# Seed with lender data
python cli.py seed

# Start server
python cli.py serve

# List lenders
python cli.py lenders

# List products
python cli.py products --finance-type bridging

# Search for loans
python cli.py search 1000000 --finance-type bridging --ltv 70

# Run scrape
python cli.py scrape
python cli.py scrape --lender mt-finance

# Check status
python cli.py status
```

## API Endpoints

### Search
- `POST /api/v1/search/loans` - Search for matching loan products
- `POST /api/v1/search/quick-quote` - Get a quick indicative quote
- `GET /api/v1/search/compare` - Compare multiple products

### Lenders
- `GET /api/v1/lenders/` - List all lenders
- `GET /api/v1/lenders/{id}` - Get lender details
- `POST /api/v1/lenders/` - Create a lender
- `PUT /api/v1/lenders/{id}` - Update a lender

### Products
- `GET /api/v1/products/` - List all products
- `GET /api/v1/products/by-type/{type}` - Get products by finance type
- `GET /api/v1/products/by-lender/{id}` - Get products by lender
- `POST /api/v1/products/lender/{id}` - Create a product

### Scraping
- `GET /api/v1/scraping/status` - Get scraping system status
- `POST /api/v1/scraping/run` - Trigger a scrape
- `GET /api/v1/scraping/changes` - Get recent changes

### Dashboard
- `GET /api/v1/dashboard/overview` - Dashboard statistics
- `GET /api/v1/dashboard/rate-trends` - Rate trend data
- `GET /api/v1/dashboard/lender-rankings` - Lender rankings
- `GET /api/v1/dashboard/alerts` - System alerts

## Architecture

```
app/
├── api/              # FastAPI routes and endpoints
├── core/             # Configuration and database
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic schemas for validation
├── scrapers/         # Web scraping framework
├── services/         # Business logic services
└── scheduler.py      # Background task scheduling
```

## Data Model

### Lenders
- Name, type, contact details
- FCA registration
- Geographic coverage
- Loan amount ranges

### Products
- Finance type (bridging, development, etc.)
- Rates and fees
- LTV/LTC/LTGDV limits
- Term lengths
- Property types supported

### Criteria
- Borrower requirements (experience, entity type)
- Planning status requirements
- Geographic exclusions
- Security requirements

### Ratings
- Speed to offer
- Rate competitiveness
- Flexibility
- Overall score

## Phase 2: Lender Portal (Planned)

Future functionality to allow lenders to:
- Update their own rates and criteria
- Set geographic pricing adjustments
- Set product type pricing adjustments
- View deal flow analytics

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **SQLite/PostgreSQL** - Database
- **BeautifulSoup** - Web scraping
- **APScheduler** - Task scheduling
- **Tailwind CSS** - Dashboard styling

## Configuration

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=sqlite:///./data/devfinance.db
API_HOST=0.0.0.0
API_PORT=8000
SCRAPE_INTERVAL_DAYS=7
```

## License

Proprietary - All Rights Reserved
