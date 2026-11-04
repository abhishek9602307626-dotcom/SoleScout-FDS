"""
SoleScout FDS - Data Models

Plain Python dataclasses representing database rows.
Follows non-negotiable rules:
- Missing fields are stored as None (SQL NULL).
- Enforces product_id and collection_date for historical snapshot tracking.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Sneaker:
    product_id: str
    sku: str
    name: str
    brand: Optional[str] = None
    colorway: Optional[str] = None
    retail_price: Optional[float] = None
    release_date: Optional[str] = None
    image_url: Optional[str] = None
    is_demo: int = 0
    id: Optional[int] = None
    fetched_at: Optional[str] = None


@dataclass
class PriceHistory:
    sneaker_id: int
    product_id: str
    platform: str
    price: float
    collection_date: str
    size: Optional[str] = None
    condition: str = "new"
    seller: Optional[str] = None
    rating: Optional[float] = None
    is_demo: int = 0
    id: Optional[int] = None
    recorded_at: Optional[str] = None
