"""
Seed database with UK bridging and development finance lenders.

This script populates the database with real UK lenders and their products.
Run with: python -m scripts.seed_data
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from slugify import slugify
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.models.lender import Lender, LenderContact, LenderType, LenderStatus
from app.models.product import Product, ProductCriteria, FinanceType
from app.models.rating import LenderRating, RatingCategory


def create_slug(name: str) -> str:
    """Create a URL-friendly slug from a name."""
    return name.lower().replace(" ", "-").replace("&", "and").replace("'", "")


# ============================================================================
# UK BRIDGING & DEVELOPMENT FINANCE LENDERS DATA
# ============================================================================

LENDERS_DATA = [
    # Major Bridging Lenders
    {
        "name": "MT Finance",
        "lender_type": LenderType.BRIDGING_SPECIALIST,
        "website_url": "https://www.mt-finance.com",
        "description": "Leading UK bridging lender with fast decisions and competitive rates",
        "fca_number": "718098",
        "headquarters_location": "London",
        "min_loan_amount": 150000,
        "max_loan_amount": 15000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Regulated Bridging",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.55,
                "rate_to": 1.25,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "exit_fee_percent": 0,
                "max_ltv": 75.0,
                "min_loan": 150000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "property_types": ["residential"],
            },
            {
                "name": "Unregulated Bridging",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.55,
                "rate_to": 1.45,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "exit_fee_percent": 0,
                "max_ltv": 80.0,
                "min_loan": 150000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "property_types": ["residential", "commercial", "mixed_use", "land"],
            },
        ],
    },
    {
        "name": "Bridging Finance Solutions",
        "lender_type": LenderType.BRIDGING_SPECIALIST,
        "website_url": "https://www.bfrg.co.uk",
        "description": "Award-winning bridging lender for property professionals",
        "fca_number": "680713",
        "headquarters_location": "Manchester",
        "min_loan_amount": 100000,
        "max_loan_amount": 25000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Standard Bridge",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.59,
                "rate_to": 1.35,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "exit_fee_percent": 1.0,
                "max_ltv": 75.0,
                "min_loan": 100000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
            },
        ],
    },
    {
        "name": "United Trust Bank",
        "lender_type": LenderType.SPECIALIST_LENDER,
        "website_url": "https://www.utbank.co.uk",
        "description": "Specialist bank offering bridging, development and BTL finance",
        "fca_number": "204463",
        "founded_year": 1955,
        "headquarters_location": "London",
        "min_loan_amount": 250000,
        "max_loan_amount": 25000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 6.5,
                "rate_to": 9.5,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "exit_fee_percent": 0,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
                "criteria": {
                    "min_experience_units": 2,
                    "accepts_first_time_developers": False,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                    "accepts_full_planning": True,
                    "requires_personal_guarantee": True,
                },
            },
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.65,
                "rate_to": 1.15,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "exit_fee_percent": 0,
                "max_ltv": 70.0,
                "min_loan": 250000,
                "max_loan": 15000000,
                "min_term_months": 3,
                "max_term_months": 18,
            },
        ],
    },
    {
        "name": "Atelier Capital Partners",
        "lender_type": LenderType.DEVELOPMENT_FUNDER,
        "website_url": "https://www.ateliercapitalpartners.com",
        "description": "Specialist development finance provider for experienced developers",
        "headquarters_location": "London",
        "min_loan_amount": 1000000,
        "max_loan_amount": 75000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Senior Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 8.0,
                "rate_to": 12.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "exit_fee_percent": 1.0,
                "max_ltc": 90.0,
                "max_ltgdv": 70.0,
                "min_loan": 1000000,
                "max_loan": 75000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use", "student"],
                "criteria": {
                    "min_experience_units": 5,
                    "min_gdv": 5000000,
                    "accepts_first_time_developers": False,
                    "accepts_spv": True,
                },
            },
            {
                "name": "Stretch Senior",
                "finance_type": FinanceType.STRETCH_SENIOR,
                "rate_from": 10.0,
                "rate_to": 15.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.0,
                "exit_fee_percent": 1.5,
                "max_ltc": 95.0,
                "max_ltgdv": 75.0,
                "min_loan": 2000000,
                "max_loan": 50000000,
                "min_term_months": 12,
                "max_term_months": 36,
            },
        ],
    },
    {
        "name": "Octopus Real Estate",
        "lender_type": LenderType.FUND,
        "website_url": "https://octopusrealestate.com",
        "description": "Part of Octopus Group, providing development and bridging finance",
        "fca_number": "194779",
        "headquarters_location": "London",
        "min_loan_amount": 500000,
        "max_loan_amount": 100000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 7.5,
                "rate_to": 11.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "max_ltc": 90.0,
                "max_ltgdv": 65.0,
                "min_loan": 1000000,
                "max_loan": 100000000,
                "min_term_months": 6,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use", "commercial"],
            },
            {
                "name": "Bridging Finance",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.69,
                "rate_to": 1.29,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
            },
        ],
    },
    {
        "name": "LendInvest",
        "lender_type": LenderType.SPECIALIST_LENDER,
        "website_url": "https://www.lendinvest.com",
        "description": "Technology-led property finance platform",
        "fca_number": "610993",
        "founded_year": 2013,
        "headquarters_location": "London",
        "min_loan_amount": 100000,
        "max_loan_amount": 50000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 7.99,
                "rate_to": 12.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.0,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 500000,
                "max_loan": 50000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
                "criteria": {
                    "min_experience_units": 1,
                    "accepts_first_time_developers": True,
                    "accepts_spv": True,
                    "accepts_full_planning": True,
                },
            },
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.55,
                "rate_to": 1.10,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 100000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 18,
            },
            {
                "name": "Developer Exit",
                "finance_type": FinanceType.DEVELOPER_EXIT,
                "rate_from": 0.49,
                "rate_to": 0.89,
                "rate_type": "monthly",
                "arrangement_fee_percent": 1.5,
                "max_ltv": 75.0,
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 3,
                "max_term_months": 18,
            },
        ],
    },
    {
        "name": "Maslow Capital",
        "lender_type": LenderType.DEVELOPMENT_FUNDER,
        "website_url": "https://www.maslowcapital.com",
        "description": "Development finance specialists for residential and commercial projects",
        "headquarters_location": "London",
        "min_loan_amount": 5000000,
        "max_loan_amount": 150000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Senior Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 8.0,
                "rate_to": 11.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.25,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 5000000,
                "max_loan": 150000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use", "student", "build_to_rent"],
                "criteria": {
                    "min_experience_units": 10,
                    "min_gdv": 10000000,
                    "accepts_spv": True,
                },
            },
        ],
    },
    {
        "name": "Shawbrook Bank",
        "lender_type": LenderType.SPECIALIST_LENDER,
        "website_url": "https://www.shawbrook.co.uk",
        "description": "Specialist bank for property development and bridging",
        "fca_number": "204574",
        "founded_year": 2011,
        "headquarters_location": "Brentwood",
        "min_loan_amount": 250000,
        "max_loan_amount": 25000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 7.5,
                "rate_to": 10.5,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
                "criteria": {
                    "min_experience_units": 2,
                    "accepts_first_time_developers": False,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                },
            },
            {
                "name": "Bridging Finance",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.69,
                "rate_to": 1.19,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 250000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 18,
            },
        ],
    },
    {
        "name": "Investec",
        "lender_type": LenderType.BANK,
        "website_url": "https://www.investec.com/en_gb",
        "description": "International specialist bank with UK development finance division",
        "fca_number": "172330",
        "headquarters_location": "London",
        "min_loan_amount": 5000000,
        "max_loan_amount": 200000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 7.0,
                "rate_to": 10.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.25,
                "max_ltc": 80.0,
                "max_ltgdv": 60.0,
                "min_loan": 5000000,
                "max_loan": 200000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use", "commercial", "student", "build_to_rent"],
                "criteria": {
                    "min_experience_units": 10,
                    "min_gdv": 20000000,
                    "accepts_spv": True,
                },
            },
        ],
    },
    {
        "name": "Blend Network",
        "lender_type": LenderType.PEER_TO_PEER,
        "website_url": "https://www.blendnetwork.com",
        "description": "P2P development finance platform connecting developers with investors",
        "fca_number": "741993",
        "founded_year": 2017,
        "headquarters_location": "London",
        "min_loan_amount": 250000,
        "max_loan_amount": 5000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 9.0,
                "rate_to": 14.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.0,
                "max_ltc": 80.0,
                "max_ltgdv": 65.0,
                "min_loan": 250000,
                "max_loan": 5000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
                "criteria": {
                    "accepts_first_time_developers": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                },
            },
        ],
    },
    {
        "name": "Close Brothers",
        "lender_type": LenderType.BANK,
        "website_url": "https://www.closebrothers.com",
        "description": "Merchant banking group with specialist property finance division",
        "fca_number": "124750",
        "founded_year": 1878,
        "headquarters_location": "London",
        "min_loan_amount": 1000000,
        "max_loan_amount": 50000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 7.5,
                "rate_to": 10.5,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 1000000,
                "max_loan": 50000000,
                "min_term_months": 12,
                "max_term_months": 30,
                "property_types": ["residential", "mixed_use"],
                "criteria": {
                    "min_experience_units": 3,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                },
            },
        ],
    },
    # Mezzanine and Equity Providers
    {
        "name": "Silbury Finance",
        "lender_type": LenderType.FUND,
        "website_url": "https://www.silburyfinance.co.uk",
        "description": "Mezzanine and equity provider for property developments",
        "headquarters_location": "London",
        "min_loan_amount": 500000,
        "max_loan_amount": 30000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Mezzanine Finance",
                "finance_type": FinanceType.MEZZANINE,
                "rate_from": 12.0,
                "rate_to": 18.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.5,
                "exit_fee_percent": 2.0,
                "max_ltc": 95.0,
                "max_ltgdv": 80.0,
                "min_loan": 500000,
                "max_loan": 30000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use", "student"],
            },
            {
                "name": "Preferred Equity",
                "finance_type": FinanceType.EQUITY,
                "rate_from": 15.0,
                "rate_to": 25.0,
                "rate_type": "annual",
                "max_ltc": 100.0,
                "max_ltgdv": 90.0,
                "min_loan": 1000000,
                "max_loan": 20000000,
                "min_term_months": 18,
                "max_term_months": 48,
            },
        ],
    },
    {
        "name": "Precede Capital Partners",
        "lender_type": LenderType.FUND,
        "website_url": "https://www.precede.co.uk",
        "description": "Mezzanine and equity finance for UK residential development",
        "headquarters_location": "London",
        "min_loan_amount": 1000000,
        "max_loan_amount": 50000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Mezzanine Debt",
                "finance_type": FinanceType.MEZZANINE,
                "rate_from": 14.0,
                "rate_to": 20.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.0,
                "max_ltc": 95.0,
                "max_ltgdv": 75.0,
                "min_loan": 1000000,
                "max_loan": 50000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "build_to_rent", "student"],
            },
        ],
    },
    {
        "name": "Urban Exposure",
        "lender_type": LenderType.FUND,
        "website_url": "https://www.urbanexposure.com",
        "description": "Specialist development and mezzanine finance provider",
        "headquarters_location": "London",
        "min_loan_amount": 2000000,
        "max_loan_amount": 75000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Senior Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 8.5,
                "rate_to": 12.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 1.5,
                "max_ltc": 90.0,
                "max_ltgdv": 70.0,
                "min_loan": 2000000,
                "max_loan": 75000000,
                "min_term_months": 12,
                "max_term_months": 36,
                "property_types": ["residential", "mixed_use"],
            },
            {
                "name": "Mezzanine Finance",
                "finance_type": FinanceType.MEZZANINE,
                "rate_from": 15.0,
                "rate_to": 22.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.5,
                "max_ltc": 97.0,
                "max_ltgdv": 85.0,
                "min_loan": 1000000,
                "max_loan": 40000000,
                "min_term_months": 12,
                "max_term_months": 36,
            },
        ],
    },
    # JV Partners
    {
        "name": "Fruition Properties",
        "lender_type": LenderType.FUND,
        "website_url": "https://www.fruitionproperties.co.uk",
        "description": "Joint venture partner for residential development projects",
        "headquarters_location": "London",
        "min_loan_amount": 500000,
        "max_loan_amount": 20000000,
        "geographic_coverage": ["England"],
        "products": [
            {
                "name": "JV Partnership",
                "finance_type": FinanceType.JOINT_VENTURE,
                "description": "Joint venture equity for residential developments",
                "max_ltc": 100.0,
                "max_ltgdv": 100.0,
                "min_loan": 500000,
                "max_loan": 20000000,
                "min_term_months": 18,
                "max_term_months": 48,
                "property_types": ["residential"],
                "criteria": {
                    "min_experience_units": 3,
                    "accepts_spv": True,
                    "criteria_notes": "Profit share typically 50/50 after hurdle return",
                },
            },
        ],
    },
    {
        "name": "Reditum Capital",
        "lender_type": LenderType.FUND,
        "website_url": "https://www.reditumcapital.com",
        "description": "JV and equity partner for UK property developments",
        "headquarters_location": "London",
        "min_loan_amount": 1000000,
        "max_loan_amount": 50000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "JV Equity",
                "finance_type": FinanceType.JOINT_VENTURE,
                "description": "Joint venture equity for experienced developers",
                "max_ltc": 100.0,
                "max_ltgdv": 100.0,
                "min_loan": 1000000,
                "max_loan": 50000000,
                "min_term_months": 18,
                "max_term_months": 48,
                "property_types": ["residential", "mixed_use", "commercial"],
                "criteria": {
                    "min_experience_units": 5,
                    "min_gdv": 5000000,
                    "accepts_spv": True,
                },
            },
        ],
    },
    # More Bridging Specialists
    {
        "name": "Together",
        "lender_type": LenderType.SPECIALIST_LENDER,
        "website_url": "https://www.togethermoney.com",
        "description": "Specialist lender for bridging, development and BTL",
        "fca_number": "308742",
        "founded_year": 1974,
        "headquarters_location": "Manchester",
        "min_loan_amount": 50000,
        "max_loan_amount": 15000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Auction Finance",
                "finance_type": FinanceType.AUCTION,
                "rate_from": 0.59,
                "rate_to": 1.25,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 50000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 12,
            },
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.59,
                "rate_to": 1.35,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 80.0,
                "min_loan": 50000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 24,
            },
            {
                "name": "Refurbishment Finance",
                "finance_type": FinanceType.REFURBISHMENT,
                "rate_from": 0.65,
                "rate_to": 1.35,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 50000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 18,
            },
        ],
    },
    {
        "name": "Roma Finance",
        "lender_type": LenderType.BRIDGING_SPECIALIST,
        "website_url": "https://www.romafinance.co.uk",
        "description": "Specialist bridging and development lender",
        "fca_number": "732478",
        "headquarters_location": "Essex",
        "min_loan_amount": 100000,
        "max_loan_amount": 25000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.55,
                "rate_to": 1.25,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 80.0,
                "min_loan": 100000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
            },
            {
                "name": "Light Development",
                "finance_type": FinanceType.REFURBISHMENT,
                "rate_from": 0.69,
                "rate_to": 1.35,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "max_ltgdv": 70.0,
                "min_loan": 250000,
                "max_loan": 10000000,
                "min_term_months": 3,
                "max_term_months": 24,
            },
        ],
    },
    {
        "name": "Castle Trust Bank",
        "lender_type": LenderType.SPECIALIST_LENDER,
        "website_url": "https://www.castletrust.co.uk",
        "description": "Specialist bank for development and bridging finance",
        "fca_number": "541910",
        "headquarters_location": "Basingstoke",
        "min_loan_amount": 150000,
        "max_loan_amount": 25000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 8.0,
                "rate_to": 12.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.0,
                "max_ltc": 85.0,
                "max_ltgdv": 65.0,
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
            },
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.65,
                "rate_to": 1.20,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 150000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 18,
            },
        ],
    },
    {
        "name": "Assetz Capital",
        "lender_type": LenderType.PEER_TO_PEER,
        "website_url": "https://www.assetzcapital.co.uk",
        "description": "P2P business lending platform with property finance products",
        "fca_number": "724996",
        "headquarters_location": "Manchester",
        "min_loan_amount": 150000,
        "max_loan_amount": 5000000,
        "geographic_coverage": ["England", "Wales", "Scotland"],
        "products": [
            {
                "name": "Development Finance",
                "finance_type": FinanceType.DEVELOPMENT,
                "rate_from": 9.0,
                "rate_to": 14.0,
                "rate_type": "annual",
                "arrangement_fee_percent": 2.5,
                "max_ltc": 75.0,
                "max_ltgdv": 60.0,
                "min_loan": 500000,
                "max_loan": 5000000,
                "min_term_months": 6,
                "max_term_months": 24,
                "property_types": ["residential"],
                "criteria": {
                    "accepts_first_time_developers": True,
                    "accepts_spv": True,
                },
            },
            {
                "name": "Bridging Loan",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.65,
                "rate_to": 1.35,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 70.0,
                "min_loan": 150000,
                "max_loan": 2500000,
                "min_term_months": 1,
                "max_term_months": 18,
            },
        ],
    },
    # Land Finance
    {
        "name": "Hope Capital",
        "lender_type": LenderType.BRIDGING_SPECIALIST,
        "website_url": "https://www.hopecapital.co.uk",
        "description": "Bridging and land finance specialists",
        "fca_number": "801522",
        "headquarters_location": "Liverpool",
        "min_loan_amount": 100000,
        "max_loan_amount": 10000000,
        "geographic_coverage": ["England", "Wales"],
        "products": [
            {
                "name": "Land Finance",
                "finance_type": FinanceType.LAND,
                "rate_from": 0.85,
                "rate_to": 1.50,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 65.0,
                "min_loan": 250000,
                "max_loan": 10000000,
                "min_term_months": 3,
                "max_term_months": 24,
                "property_types": ["land"],
            },
            {
                "name": "Bridging Finance",
                "finance_type": FinanceType.BRIDGING,
                "rate_from": 0.65,
                "rate_to": 1.25,
                "rate_type": "monthly",
                "arrangement_fee_percent": 2.0,
                "max_ltv": 75.0,
                "min_loan": 100000,
                "max_loan": 10000000,
                "min_term_months": 1,
                "max_term_months": 24,
            },
        ],
    },
]


def seed_lenders(db: Session) -> None:
    """Seed lenders and their products into the database."""
    print("Seeding lenders and products...")

    for lender_data in LENDERS_DATA:
        # Check if lender already exists
        existing = db.query(Lender).filter(Lender.name == lender_data["name"]).first()
        if existing:
            print(f"  Skipping {lender_data['name']} - already exists")
            continue

        # Create lender
        products_data = lender_data.pop("products", [])

        lender = Lender(
            name=lender_data["name"],
            slug=create_slug(lender_data["name"]),
            description=lender_data.get("description"),
            lender_type=lender_data["lender_type"],
            status=LenderStatus.ACTIVE,
            website_url=lender_data.get("website_url"),
            fca_number=lender_data.get("fca_number"),
            is_fca_regulated=bool(lender_data.get("fca_number")),
            founded_year=lender_data.get("founded_year"),
            headquarters_location=lender_data.get("headquarters_location"),
            min_loan_amount=lender_data.get("min_loan_amount"),
            max_loan_amount=lender_data.get("max_loan_amount"),
            geographic_coverage=json.dumps(lender_data.get("geographic_coverage")) if lender_data.get("geographic_coverage") else None,
        )

        db.add(lender)
        db.flush()  # Get the lender ID

        print(f"  Added lender: {lender.name}")

        # Create products
        for product_data in products_data:
            criteria_data = product_data.pop("criteria", None)

            product = Product(
                lender_id=lender.id,
                name=product_data["name"],
                slug=create_slug(f"{lender.name}-{product_data['name']}"),
                finance_type=product_data["finance_type"],
                description=product_data.get("description"),
                rate_from=product_data.get("rate_from"),
                rate_to=product_data.get("rate_to"),
                rate_type=product_data.get("rate_type"),
                arrangement_fee_percent=product_data.get("arrangement_fee_percent"),
                exit_fee_percent=product_data.get("exit_fee_percent"),
                max_ltv=product_data.get("max_ltv"),
                max_ltc=product_data.get("max_ltc"),
                max_ltgdv=product_data.get("max_ltgdv"),
                min_loan=product_data.get("min_loan"),
                max_loan=product_data.get("max_loan"),
                min_term_months=product_data.get("min_term_months"),
                max_term_months=product_data.get("max_term_months"),
                property_types=product_data.get("property_types"),
                is_active=True,
            )

            db.add(product)
            db.flush()

            # Create criteria if provided
            if criteria_data:
                criteria = ProductCriteria(
                    product_id=product.id,
                    **criteria_data
                )
                db.add(criteria)

            print(f"    Added product: {product.name}")

    db.commit()
    print("Seeding complete!")


def seed_initial_ratings(db: Session) -> None:
    """Add initial system ratings for lenders."""
    print("Seeding initial ratings...")

    lenders = db.query(Lender).all()

    for lender in lenders:
        # Check if ratings exist
        existing = db.query(LenderRating).filter(LenderRating.lender_id == lender.id).first()
        if existing:
            continue

        # Add baseline ratings (can be updated with real data later)
        categories = [
            (RatingCategory.SPEED_TO_OFFER, 70),
            (RatingCategory.RATE_COMPETITIVENESS, 75),
            (RatingCategory.FLEXIBILITY, 70),
            (RatingCategory.OVERALL, 72),
        ]

        for category, score in categories:
            rating = LenderRating(
                lender_id=lender.id,
                category=category,
                score=score,
                source="system",
                confidence=0.5,  # Low confidence for initial ratings
                notes="Initial system rating - to be updated with real data",
            )
            db.add(rating)

    db.commit()
    print("Ratings seeding complete!")


def main():
    """Run the seeding process."""
    print("=" * 60)
    print("Developer Finance Engine - Database Seeder")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    init_db()

    # Create session
    db = SessionLocal()

    try:
        seed_lenders(db)
        seed_initial_ratings(db)

        # Print summary
        lender_count = db.query(Lender).count()
        product_count = db.query(Product).count()

        print("\n" + "=" * 60)
        print(f"Database now contains:")
        print(f"  - {lender_count} lenders")
        print(f"  - {product_count} products")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
