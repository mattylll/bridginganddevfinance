"""Pydantic schemas for API validation and serialization."""

from app.schemas.lender import (
    LenderCreate,
    LenderUpdate,
    LenderResponse,
    LenderListResponse,
    LenderContactCreate,
    LenderContactResponse,
)
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSearchParams,
    ProductComparisonResponse,
)
from app.schemas.search import (
    LoanSearchRequest,
    LoanSearchResponse,
    MatchedProduct,
)

__all__ = [
    "LenderCreate",
    "LenderUpdate",
    "LenderResponse",
    "LenderListResponse",
    "LenderContactCreate",
    "LenderContactResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductSearchParams",
    "ProductComparisonResponse",
    "LoanSearchRequest",
    "LoanSearchResponse",
    "MatchedProduct",
]
