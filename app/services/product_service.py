"""
Product Service

Handles CRUD operations and business logic for products.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from slugify import slugify

from app.models.lender import Lender
from app.models.product import Product, ProductCriteria, FinanceType
from app.schemas.product import ProductCreate, ProductUpdate, ProductSearchParams


class ProductService:
    """Service for managing products."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        finance_type: Optional[FinanceType] = None,
        lender_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[Product]:
        """Get all products with optional filtering."""
        query = self.db.query(Product)

        if active_only:
            query = query.filter(Product.is_active == True)

        if finance_type:
            query = query.filter(Product.finance_type == finance_type)

        if lender_id:
            query = query.filter(Product.lender_id == lender_id)

        return query.offset(skip).limit(limit).all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get a product by slug."""
        return self.db.query(Product).filter(Product.slug == slug).first()

    def get_by_lender(self, lender_id: int) -> List[Product]:
        """Get all products for a lender."""
        return (
            self.db.query(Product)
            .filter(Product.lender_id == lender_id)
            .filter(Product.is_active == True)
            .all()
        )

    def get_by_finance_type(self, finance_type: FinanceType) -> List[Product]:
        """Get all products of a specific finance type."""
        return (
            self.db.query(Product)
            .filter(Product.finance_type == finance_type)
            .filter(Product.is_active == True)
            .all()
        )

    def create(self, lender_id: int, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Verify lender exists
        lender = self.db.query(Lender).filter(Lender.id == lender_id).first()
        if not lender:
            raise ValueError(f"Lender with ID {lender_id} not found")

        # Generate slug
        slug = slugify(f"{lender.name}-{product_data.name}")

        # Check for duplicate
        existing = self.get_by_slug(slug)
        if existing:
            # Append ID to make unique
            slug = f"{slug}-{self.db.query(Product).count() + 1}"

        # Extract criteria data
        criteria_data = None
        if product_data.criteria:
            criteria_data = product_data.criteria.model_dump()

        # Create product
        product = Product(
            lender_id=lender_id,
            name=product_data.name,
            slug=slug,
            finance_type=product_data.finance_type,
            description=product_data.description,
            rate_from=product_data.rate_from,
            rate_to=product_data.rate_to,
            rate_type=product_data.rate_type,
            arrangement_fee_percent=product_data.arrangement_fee_percent,
            arrangement_fee_min=product_data.arrangement_fee_min,
            exit_fee_percent=product_data.exit_fee_percent,
            valuation_fee=product_data.valuation_fee,
            legal_fee=product_data.legal_fee,
            min_loan=product_data.min_loan,
            max_loan=product_data.max_loan,
            max_ltv=product_data.max_ltv,
            max_ltc=product_data.max_ltc,
            max_ltgdv=product_data.max_ltgdv,
            min_term_months=product_data.min_term_months,
            max_term_months=product_data.max_term_months,
            property_types=product_data.property_types,
            geographic_areas=product_data.geographic_areas,
            source_url=product_data.source_url,
            is_active=True,
        )

        self.db.add(product)
        self.db.flush()

        # Add criteria if provided
        if criteria_data:
            criteria = ProductCriteria(
                product_id=product.id,
                **criteria_data
            )
            self.db.add(criteria)

        self.db.commit()
        self.db.refresh(product)

        return product

    def update(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update a product."""
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)

        return product

    def delete(self, product_id: int) -> bool:
        """Delete a product."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        self.db.delete(product)
        self.db.commit()

        return True

    def search(self, params: ProductSearchParams) -> List[Product]:
        """Search products with filters."""
        query = self.db.query(Product).filter(Product.is_active == True)

        if params.finance_type:
            query = query.filter(Product.finance_type == params.finance_type)

        if params.loan_amount:
            query = query.filter(
                (Product.min_loan == None) | (Product.min_loan <= params.loan_amount)
            )
            query = query.filter(
                (Product.max_loan == None) | (Product.max_loan >= params.loan_amount)
            )

        if params.max_rate:
            query = query.filter(Product.rate_from <= params.max_rate)

        if params.ltv:
            query = query.filter(
                (Product.max_ltv == None) | (Product.max_ltv >= params.ltv)
            )

        # Pagination
        offset = (params.page - 1) * params.page_size
        return query.offset(offset).limit(params.page_size).all()

    def count(
        self,
        finance_type: Optional[FinanceType] = None,
        active_only: bool = True
    ) -> int:
        """Count products."""
        query = self.db.query(Product)

        if active_only:
            query = query.filter(Product.is_active == True)

        if finance_type:
            query = query.filter(Product.finance_type == finance_type)

        return query.count()

    def get_finance_type_summary(self) -> dict:
        """Get count of products by finance type."""
        from sqlalchemy import func

        results = (
            self.db.query(Product.finance_type, func.count(Product.id))
            .filter(Product.is_active == True)
            .group_by(Product.finance_type)
            .all()
        )

        return {ft.value: count for ft, count in results}
