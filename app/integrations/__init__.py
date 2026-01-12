"""
Lender API Integrations

This module provides real-time API integrations with lenders
that offer APIs for indicative pricing and applications.
"""

from app.integrations.base import BaseLenderAPI, QuoteRequest, QuoteResponse
from app.integrations.manager import IntegrationManager

__all__ = [
    "BaseLenderAPI",
    "QuoteRequest",
    "QuoteResponse",
    "IntegrationManager",
]
