"""
Import actual lender term sheets based on public rate information.

This script imports real rate data gathered from lender websites and
industry sources as of January 2025.

IMPORTANT: These rates are indicative and based on publicly available
information. Always verify with the lender for actual quotes.

Run with: python -m scripts.import_term_sheets
"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, init_db
from app.models.lender import Lender
from app.services.term_sheet_service import TermSheetService


# =============================================================================
# ACTUAL TERM SHEET DATA FROM PUBLIC SOURCES
# =============================================================================
# Sources:
# - Lender websites
# - Bridging Loan Directory (bridgingloandirectory.co.uk)
# - Mortgage Introducer
# - Bridging & Commercial
# - Financial Reporter
# =============================================================================

TERM_SHEETS = {
    "mt-finance": {
        "name": "MT Finance Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://www.mt-finance.com",
        "received_from": "Public website / Bridging Trends data",
        "notes": "Rates based on Bridging Trends Q2 2025 data and public information",
        "rate_cards": [
            {
                "product_name": "Regulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.80, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                    "accepts_individuals": True,
                }
            },
            {
                "product_name": "Unregulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial", "mixed_use", "land"],
                "min_loan": 150000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.80, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.90, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.95, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                }
            },
        ]
    },

    "together": {
        "name": "Together Money Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://togethermoney.com/intermediaries/bridging-loans",
        "received_from": "Public website and product updates",
        "notes": "LTV increased to 75% on select products Nov 2025. Rates reduced May/Oct 2025.",
        "rate_cards": [
            {
                "product_name": "Regulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 26000,
                "max_loan": 3000000,
                "min_term_months": 1,
                "max_term_months": 12,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.55, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_individuals": True,
                    "accepts_spv": True,
                }
            },
            {
                "product_name": "Unregulated Residential Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 26000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.59, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.69, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.79, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.89, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                }
            },
            {
                "product_name": "Auction Finance",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial"],
                "min_loan": 50000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 12,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.89, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "lendinvest": {
        "name": "LendInvest Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://docs.lendinvest.com/web/public-pdfs/bridging-dev-resources/bridging-criteria.pdf",
        "received_from": "Public criteria guide and website",
        "notes": "Rates from 0.82% pm. Max 73% net LTV via portal. 10% personal contribution required.",
        "rate_cards": [
            {
                "product_name": "Regulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.82, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.89, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.95, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_individuals": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                    "full_criteria_text": "10% personal contribution required. No bankruptcy/IVA in last 6 years.",
                }
            },
            {
                "product_name": "Refurbishment Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 15000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.85, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.92, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.99, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 73, "rate": 1.05, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "united-trust-bank": {
        "name": "United Trust Bank Bridging Rate Card - February 2025",
        "effective_date": "2025-02-01",
        "source_document_url": "https://www.utbank.co.uk",
        "received_from": "UTB announcements and press releases",
        "notes": "Rates as announced Feb 2025. Max LTV 75% for standard, £100k minimum.",
        "rate_cards": [
            {
                "product_name": "Regulated Standard Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 15000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.60, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.70, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.75, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_individuals": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                }
            },
            {
                "product_name": "Unregulated Standard Bridging",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial", "mixed_use"],
                "min_loan": 100000,
                "max_loan": 15000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.62, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.67, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.72, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.77, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Large Loan Bridging (£1.5m+)",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial", "mixed_use"],
                "min_loan": 1500000,
                "max_loan": 15000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.58, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.63, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.70, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.75, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 1.5,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Heavy Refurbishment - Experienced",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 5000000,
                "min_term_months": 6,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.80, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "min_projects_completed": 2,
                    "accepts_first_time_developers": False,
                }
            },
        ]
    },

    "shawbrook-bank": {
        "name": "Shawbrook Bank Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://www.shawbrook.co.uk",
        "received_from": "Shawbrook product guides",
        "notes": "Rates from 0.5%. Up to 85% LTV. Shawbrook Base Rate currently 3.75%.",
        "rate_cards": [
            {
                "product_name": "Regulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 75000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 60, "rate": 0.55, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 75, "ltv_to": 85, "rate": 0.90, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_individuals": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                    "accepts_llp": True,
                    "full_criteria_text": "Min 12 months BTL landlord experience. Min age 21, max 85.",
                }
            },
            {
                "product_name": "Unregulated Bridging",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial", "mixed_use", "hmo"],
                "min_loan": 75000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 60, "rate": 0.60, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.70, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.80, "rate_type": "monthly"},
                    {"ltv_from": 75, "ltv_to": 85, "rate": 0.95, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "roma-finance": {
        "name": "Roma Finance Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://romafinance.co.uk",
        "received_from": "Roma Finance website and press releases",
        "notes": "Roma75 product launched. Rates from 0.75%. No exit fees.",
        "rate_cards": [
            {
                "product_name": "Roma75 - Standard Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 3000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.75, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "min_projects_completed": 2,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                    "full_criteria_text": "Min 2 BTL properties or homeowner with 1 investment property",
                }
            },
            {
                "product_name": "Semi-Commercial Bridge",
                "finance_type": "bridging",
                "property_types": ["mixed_use"],
                "min_loan": 100000,
                "max_loan": 3000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Commercial Bridge",
                "finance_type": "bridging",
                "property_types": ["commercial"],
                "min_loan": 100000,
                "max_loan": 3000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 65, "rate": 0.95, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "BMV (Below Market Value) Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 75000,
                "max_loan": 500000,
                "min_term_months": 1,
                "max_term_months": 12,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.99, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "castle-trust-bank": {
        "name": "Castle Trust Bank Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://www.castletrust.co.uk",
        "received_from": "Castle Trust announcements",
        "notes": "Rates cut Jan 2025. Arrangement fees reduced to 2%.",
        "rate_cards": [
            {
                "product_name": "Standard Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 10000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 65, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 65, "ltv_to": 75, "rate": 0.70, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Light Refurb Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 10000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 65, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 65, "ltv_to": 70, "rate": 0.80, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 80, "rate": 0.80, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Heavy Refurb Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 10000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "min_projects_completed": 1,
                }
            },
            {
                "product_name": "Bridge the Gap",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 12,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 75, "rate": 0.52, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 5.5,
                    "exit_fee_percent": 0,
                    "exit_fee_months_free": 3,
                },
            },
        ]
    },

    "hope-capital": {
        "name": "Hope Capital Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://hope-capital.co.uk",
        "received_from": "Hope Capital press releases",
        "notes": "Largest rate drop Jan 2025. Flat rates across refurb levels.",
        "rate_cards": [
            {
                "product_name": "Residential Fast Track Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 5000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 75, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Residential Bridge (inc Light/Medium/Heavy Refurb)",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 100000,
                "max_loan": 5000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.92, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.92, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Semi-Commercial Bridge",
                "finance_type": "bridging",
                "property_types": ["mixed_use"],
                "min_loan": 100000,
                "max_loan": 5000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 1.05, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Commercial Bridge",
                "finance_type": "bridging",
                "property_types": ["commercial"],
                "min_loan": 100000,
                "max_loan": 5000000,
                "min_term_months": 3,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 65, "rate": 1.09, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "octopus-real-estate": {
        "name": "Octopus Capital (Real Estate) Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://octopus-capital.com",
        "received_from": "Octopus website",
        "notes": "Rebranded to Octopus Capital May 2025. Rates from 0.55%.",
        "rate_cards": [
            {
                "product_name": "Bridging Finance",
                "finance_type": "bridging",
                "property_types": ["residential", "commercial"],
                "min_loan": 500000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.55, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },

    "assetz-capital": {
        "name": "Assetz Capital Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://www.assetzcapital.co.uk",
        "received_from": "Assetz Capital website",
        "notes": "Bridging from 0.70% pm. Development from 8.35% pa.",
        "rate_cards": [
            {
                "product_name": "Bridging Finance",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 150000,
                "max_loan": 5000000,
                "min_term_months": 1,
                "max_term_months": 18,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.70, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.80, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.90, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 1.00, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_first_time_developers": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                }
            },
        ]
    },

    "bridging-finance-solutions": {
        "name": "BFS Bridging Rate Card - January 2025",
        "effective_date": "2025-01-01",
        "source_document_url": "https://www.bfratesetter.co.uk",
        "received_from": "BFS website and broker sources",
        "notes": "Specialist bridging lender. Rates from 0.55% pm. Up to 75% LTV.",
        "rate_cards": [
            {
                "product_name": "Standard Residential Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 50000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 50, "rate": 0.55, "rate_type": "monthly"},
                    {"ltv_from": 50, "ltv_to": 60, "rate": 0.65, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 70, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
                "criteria": {
                    "accepts_individuals": True,
                    "accepts_spv": True,
                    "accepts_ltd_company": True,
                }
            },
            {
                "product_name": "Light Refurbishment Bridge",
                "finance_type": "bridging",
                "property_types": ["residential"],
                "min_loan": 50000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 70, "rate": 0.79, "rate_type": "monthly"},
                    {"ltv_from": 70, "ltv_to": 75, "rate": 0.89, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
            {
                "product_name": "Commercial Bridge",
                "finance_type": "bridging",
                "property_types": ["commercial", "mixed_use"],
                "min_loan": 100000,
                "max_loan": 25000000,
                "min_term_months": 1,
                "max_term_months": 24,
                "rate_tiers": [
                    {"ltv_from": 0, "ltv_to": 60, "rate": 0.75, "rate_type": "monthly"},
                    {"ltv_from": 60, "ltv_to": 65, "rate": 0.85, "rate_type": "monthly"},
                ],
                "fees": {
                    "arrangement_fee_percent": 2.0,
                    "exit_fee_percent": 0,
                },
            },
        ]
    },
}


def get_or_create_lender(db, slug: str, name: str):
    """Get lender by slug or return None if not found."""
    lender = db.query(Lender).filter(Lender.slug == slug).first()
    if not lender:
        print(f"  [SKIP] Lender '{slug}' not found in database")
        return None
    return lender


def main():
    """Import all term sheets."""
    print("=" * 70)
    print("Developer Finance Engine - Term Sheet Importer")
    print("Importing real rate data from public sources")
    print("=" * 70)

    init_db()
    db = SessionLocal()

    try:
        service = TermSheetService(db)

        imported = 0
        skipped = 0

        for slug, term_sheet_data in TERM_SHEETS.items():
            print(f"\nProcessing: {slug}")

            # Find the lender
            lender = get_or_create_lender(db, slug, slug)
            if not lender:
                skipped += 1
                continue

            # Check if term sheet already exists
            existing = service.get_current_term_sheet(lender.id)
            if existing and existing.name == term_sheet_data["name"]:
                print(f"  [SKIP] Term sheet already exists")
                skipped += 1
                continue

            # Import term sheet
            print(f"  Importing: {term_sheet_data['name']}")
            term_sheet = service.import_term_sheet_from_dict(
                lender_id=lender.id,
                data=term_sheet_data,
                created_by="import_term_sheets.py",
            )

            print(f"  [OK] Created term sheet ID {term_sheet.id}")
            print(f"       Rate cards: {len(term_sheet.rate_cards)}")
            imported += 1

        print("\n" + "=" * 70)
        print(f"Import complete!")
        print(f"  Imported: {imported}")
        print(f"  Skipped: {skipped}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
