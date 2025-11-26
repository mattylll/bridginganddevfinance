"""
Product API Routes

CRUD operations for financial products.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import FinanceType
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductSearchParams,
)
from app.services.product_service import ProductService


router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    finance_type: Optional[FinanceType] = None,
    lender_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """
    List all products with optional filtering.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **finance_type**: Filter by finance type (bridging, development, etc.)
    - **lender_id**: Filter by lender
    - **active_only**: Only return active products
    """
    service = ProductService(db)

    return service.get_all(
        skip=skip,
        limit=limit,
        finance_type=finance_type,
        lender_id=lender_id,
        active_only=active_only,
    )


@router.get("/by-type/{finance_type}", response_model=List[ProductResponse])
async def get_products_by_type(
    finance_type: FinanceType,
    db: Session = Depends(get_db),
):
    """Get all products of a specific finance type."""
    service = ProductService(db)
    return service.get_by_finance_type(finance_type)


@router.get("/by-lender/{lender_id}", response_model=List[ProductResponse])
async def get_products_by_lender(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Get all products from a specific lender."""
    service = ProductService(db)
    return service.get_by_lender(lender_id)


@router.get("/summary")
async def get_products_summary(
    db: Session = Depends(get_db),
):
    """Get a summary of products by finance type."""
    service = ProductService(db)
    summary = service.get_finance_type_summary()

    return {
        "by_finance_type": summary,
        "total": sum(summary.values()),
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific product by ID."""
    service = ProductService(db)
    product = service.get_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/lender/{lender_id}", response_model=ProductResponse, status_code=201)
async def create_product(
    lender_id: int,
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    """Create a new product for a lender."""
    service = ProductService(db)

    try:
        product = service.create(lender_id, product_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Update a product."""
    service = ProductService(db)
    product = service.update(product_id, product_data)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Delete a product."""
    service = ProductService(db)
    deleted = service.delete(product_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")


@router.post("/search", response_model=List[ProductResponse])
async def search_products(
    params: ProductSearchParams,
    db: Session = Depends(get_db),
):
    """Search products with filters."""
    service = ProductService(db)
    return service.search(params)
