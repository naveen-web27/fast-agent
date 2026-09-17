"""Hybrid data access layer.

Every caller (intent handlers) uses these functions only — never raw SQL or HTTP calls directly,
and never cares whether business.data_mode is "hosted" or "api".

- "hosted": query our own Supabase tables (products, orders) via SQLAlchemy.
- "api": call the client's own backend/e-commerce API using business.client_api_base_url +
  business.client_api_key (sent as a Bearer token).

ratings and conversations are ALWAYS stored in our own runtime database regardless of data_mode.
"""
import logging
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Business, Order, Product, Rating

logger = logging.getLogger(__name__)


class DataAccessError(Exception):
    """Raised when the underlying data source (hosted DB or client API) fails."""


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

async def get_products(db: AsyncSession, business: Business, category: str | None = None) -> list[dict]:
    """Return a list of product dicts: {id, name, price, stock, category, rating_avg, rating_count}."""
    if business.data_mode == "hosted":
        return await _get_products_hosted(db, business, category)
    return await _get_products_api(business, category)


async def _get_products_hosted(db: AsyncSession, business: Business, category: str | None) -> list[dict]:
    stmt = select(Product).where(Product.business_id == business.id, Product.stock > 0)
    if category:
        stmt = stmt.where(Product.category.ilike(f"%{category}%"))
    result = await db.execute(stmt)
    products = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "category": p.category,
            "rating_avg": float(p.rating_avg),
            "rating_count": p.rating_count,
        }
        for p in products
    ]


async def _get_products_api(business: Business, category: str | None) -> list[dict]:
    params = {"category": category} if category else {}
    data = await _client_api_get(business, "/products", params=params)
    # Expect the client's API to return a list of product objects with similar fields.
    return data if isinstance(data, list) else data.get("products", [])


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

async def get_order(db: AsyncSession, business: Business, order_id: str | None = None, customer_phone: str | None = None) -> dict | None:
    """Return a single order dict, or None if not found. Lookup by order_id or customer_phone (most recent)."""
    if business.data_mode == "hosted":
        return await _get_order_hosted(db, business, order_id, customer_phone)
    return await _get_order_api(business, order_id, customer_phone)


async def _get_order_hosted(db: AsyncSession, business: Business, order_id: str | None, customer_phone: str | None) -> dict | None:
    stmt = select(Order).where(Order.business_id == business.id)
    if order_id:
        stmt = stmt.where(Order.id == order_id)
    elif customer_phone:
        stmt = stmt.where(Order.customer_phone == customer_phone).order_by(Order.created_at.desc())
    else:
        return None
    result = await db.execute(stmt)
    order = result.scalars().first()
    if not order:
        return None
    return {
        "id": str(order.id),
        "customer_phone": order.customer_phone,
        "product_id": str(order.product_id) if order.product_id else None,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


async def _get_order_api(business: Business, order_id: str | None, customer_phone: str | None) -> dict | None:
    params: dict[str, Any] = {}
    if order_id:
        params["order_id"] = order_id
    if customer_phone:
        params["customer_phone"] = customer_phone
    data = await _client_api_get(business, "/orders", params=params)
    if isinstance(data, list):
        return data[0] if data else None
    return data or None


# ---------------------------------------------------------------------------
# Ratings — ALWAYS our own database, regardless of data_mode.
# ---------------------------------------------------------------------------

async def rate_product(db: AsyncSession, business: Business, product_ref: str, customer_phone: str, stars: int) -> dict:
    """Insert a rating and, for hosted products, recompute the product's average/count."""
    if stars < 1 or stars > 5:
        raise ValueError("stars must be between 1 and 5")

    rating = Rating(business_id=business.id, product_ref=product_ref, customer_phone=customer_phone, stars=stars)
    db.add(rating)
    await db.flush()

    new_avg = None
    new_count = None
    if business.data_mode == "hosted":
        new_avg, new_count = await _recompute_hosted_product_rating(db, business, product_ref)

    await db.commit()
    return {"product_ref": product_ref, "stars": stars, "rating_avg": new_avg, "rating_count": new_count}


async def _recompute_hosted_product_rating(db: AsyncSession, business: Business, product_ref: str) -> tuple[float | None, int | None]:
    stmt = select(Rating.stars).where(Rating.business_id == business.id, Rating.product_ref == product_ref)
    result = await db.execute(stmt)
    all_stars = [r for r in result.scalars().all()]
    if not all_stars:
        return None, None
    avg = sum(all_stars) / len(all_stars)

    # product_ref may be a product id or a name; try id first, then name.
    product = None
    try:
        product = (
            await db.execute(select(Product).where(Product.business_id == business.id, Product.id == product_ref))
        ).scalars().first()
    except Exception:
        product = None
    if not product:
        product = (
            await db.execute(select(Product).where(Product.business_id == business.id, Product.name.ilike(product_ref)))
        ).scalars().first()

    if product:
        product.rating_avg = Decimal(str(round(avg, 2)))
        product.rating_count = len(all_stars)
        db.add(product)

    return round(avg, 2), len(all_stars)


# ---------------------------------------------------------------------------
# Client API helper ("api" data_mode)
# ---------------------------------------------------------------------------

async def _client_api_get(business: Business, path: str, params: dict | None = None) -> Any:
    if not business.client_api_base_url:
        raise DataAccessError(f"business {business.id} is in api mode but has no client_api_base_url configured")

    url = f"{business.client_api_base_url.rstrip('/')}{path}"
    headers = {"Authorization": f"Bearer {business.client_api_key}"} if business.client_api_key else {}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("Client API call failed for business %s: %s", business.id, exc)
            raise DataAccessError(f"client API call failed: {exc}") from exc
