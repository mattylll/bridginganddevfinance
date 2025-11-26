"""
Lender API Routes

CRUD operations for lenders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lender import LenderStatus, LenderType
from app.schemas.lender import (
    LenderCreate,
    LenderUpdate,
    LenderResponse,
    LenderListResponse,
    LenderContactCreate,
    LenderContactResponse,
)
from app.services.lender_service import LenderService


router = APIRouter()


@router.get("/", response_model=LenderListResponse)
async def list_lenders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[LenderStatus] = None,
    lender_type: Optional[LenderType] = None,
    db: Session = Depends(get_db),
):
    """
    List all lenders with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by lender status
    - **lender_type**: Filter by lender type
    """
    service = LenderService(db)

    lenders = service.get_all(
        skip=skip,
        limit=limit,
        status=status,
        lender_type=lender_type.value if lender_type else None,
    )

    total = service.count(status=status)
    pages = (total + limit - 1) // limit

    return LenderListResponse(
        items=lenders,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        pages=pages,
    )


@router.get("/{lender_id}", response_model=LenderResponse)
async def get_lender(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific lender by ID."""
    service = LenderService(db)
    lender = service.get_by_id(lender_id)

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    return lender


@router.get("/slug/{slug}", response_model=LenderResponse)
async def get_lender_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a specific lender by slug."""
    service = LenderService(db)
    lender = service.get_by_slug(slug)

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    return lender


@router.post("/", response_model=LenderResponse, status_code=201)
async def create_lender(
    lender_data: LenderCreate,
    db: Session = Depends(get_db),
):
    """Create a new lender."""
    service = LenderService(db)

    try:
        lender = service.create(lender_data)
        return lender
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{lender_id}", response_model=LenderResponse)
async def update_lender(
    lender_id: int,
    lender_data: LenderUpdate,
    db: Session = Depends(get_db),
):
    """Update a lender."""
    service = LenderService(db)
    lender = service.update(lender_id, lender_data)

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    return lender


@router.delete("/{lender_id}", status_code=204)
async def delete_lender(
    lender_id: int,
    db: Session = Depends(get_db),
):
    """Delete a lender."""
    service = LenderService(db)
    deleted = service.delete(lender_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Lender not found")


@router.post("/{lender_id}/contacts", response_model=LenderContactResponse, status_code=201)
async def add_lender_contact(
    lender_id: int,
    contact_data: LenderContactCreate,
    db: Session = Depends(get_db),
):
    """Add a contact to a lender."""
    service = LenderService(db)
    contact = service.add_contact(lender_id, contact_data)

    if not contact:
        raise HTTPException(status_code=404, detail="Lender not found")

    return contact


@router.get("/search/", response_model=List[LenderResponse])
async def search_lenders(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search lenders by name."""
    service = LenderService(db)
    return service.search(q, limit)
