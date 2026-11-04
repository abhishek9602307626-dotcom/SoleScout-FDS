"""
SoleScout FDS - SoleScout API Client
Stage 2: Official SoleScout API Integration

Official SoleScout API Specification:
- Base URL: https://solescout.ai
- Endpoints:
    * GET /api/public/search  (q, brand, category, gender, page, limit)
    * GET /api/public/product (slug, sku)
    * GET /api/public/brands
    * GET /api/public/upc     (upc, style)
- Documentation: https://solescout.ai/for-ai
- OpenAPI 3.1 Spec: https://solescout.ai/openapi.json

Security & Data Integrity Rules:
1. API credentials loaded strictly via python-dotenv.
2. Credentials kept ONLY on the backend; never exposed to frontend or logged.
3. Secret keys are masked in logs, repr, and exception strings.
4. No endpoints or response fields are invented.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables from .env
# Search current directory and parent directories up to project root
_ENV_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    os.path.join(os.getcwd(), ".env"),
]
for _path in _ENV_PATHS:
    if os.path.exists(_path):
        load_dotenv(dotenv_path=_path)
        break
else:
    load_dotenv()

logger = logging.getLogger("solescout.api")

PLACEHOLDER_KEYS = {
    "",
    "your_api_key_here",
    "your_key_here",
    "change_me",
    "placeholder",
    "none",
    "null",
}


def mask_key(key: Optional[str]) -> str:
    """Safely mask an API key for logging without leaking the secret."""
    if not key or key.strip().lower() in PLACEHOLDER_KEYS:
        return "[NOT CONFIGURED]"
    clean = key.strip()
    if len(clean) <= 8:
        return "***"
    return f"{clean[:3]}...{clean[-3:]} (len {len(clean)})"


class SoleScoutAPIError(Exception):
    """Exception raised when SoleScout API communication fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.endpoint = endpoint
        self.details = details

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"[HTTP {self.status_code}]")
        if self.endpoint:
            parts.append(f"[Endpoint: {self.endpoint}]")
        return " ".join(parts)


class SoleScoutClient:
    """
    Reusable client for the official SoleScout Sneaker Price Intelligence API.

    Features:
    - Official /api/public/search and /api/public/product endpoints
    - Bearer and X-API-Key header authentication
    - Exponential backoff and retry on transient errors (429, 5xx)
    - Timeout handling
    - HTTP error normalization
    - Credential masking (never logs raw API keys)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 15,
        max_retries: int = 3,
        allow_anonymous: bool = False,
    ):
        raw_key = api_key if api_key is not None else os.getenv("SOLESCOUT_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""

        env_url = os.getenv("SOLESCOUT_BASE_URL", "https://solescout.ai")
        self.base_url = (base_url or env_url).rstrip("/")
        self.timeout = timeout
        self.allow_anonymous = allow_anonymous

        # Set up requests session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Configure standard headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "SoleScout-FDS-Price-Intelligence/2.0",
        }
        if self.is_configured():
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
            logger.info("SoleScoutClient initialized with key %s", mask_key(self.api_key))
        else:
            logger.info(
                "SoleScoutClient initialized without API key (allow_anonymous=%s)",
                self.allow_anonymous,
            )

        self.session.headers.update(headers)

    def is_configured(self) -> bool:
        """Check if a real, non-placeholder API key is configured."""
        return bool(self.api_key and self.api_key.lower() not in PLACEHOLDER_KEYS)

    def __repr__(self) -> str:
        return (
            f"SoleScoutClient(base_url='{self.base_url}', "
            f"key={mask_key(self.api_key)}, "
            f"configured={self.is_configured()})"
        )

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: Optional[bool] = None,
    ) -> Any:
        """
        Execute an internal GET request with comprehensive error handling.
        Ensures the secret API key is NEVER leaked in logs or error messages.
        """
        must_auth = require_auth if require_auth is not None else (not self.allow_anonymous)
        if must_auth and not self.is_configured():
            raise SoleScoutAPIError(
                "SoleScout API key is not configured. Set SOLESCOUT_API_KEY in backend .env.",
                status_code=401,
                endpoint=endpoint,
            )

        clean_endpoint = endpoint.lstrip("/")
        # Map legacy stub endpoints if called by older test code
        if clean_endpoint == "sneakers":
            clean_endpoint = "api/public/search"

        url = f"{self.base_url}/{clean_endpoint}"
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        logger.info("GET %s (params: %s)", clean_endpoint, list(clean_params.keys()))

        try:
            response = self.session.get(url, params=clean_params, timeout=self.timeout)
        except requests.exceptions.Timeout:
            logger.error("Request to %s timed out after %ds", clean_endpoint, self.timeout)
            raise SoleScoutAPIError(
                f"SoleScout API request timed out after {self.timeout}s.",
                status_code=504,
                endpoint=clean_endpoint,
            )
        except requests.exceptions.ConnectionError as ce:
            logger.error("Connection error reaching %s: %s", self.base_url, ce)
            raise SoleScoutAPIError(
                f"Failed to connect to SoleScout API at {self.base_url}.",
                status_code=502,
                endpoint=clean_endpoint,
            )
        except requests.exceptions.RequestException as re:
            logger.error("Network request failed: %s", re)
            raise SoleScoutAPIError(
                "Network request to SoleScout API failed.",
                status_code=500,
                endpoint=clean_endpoint,
            )

        # Handle specific HTTP error status codes
        status = response.status_code
        if status == 401:
            logger.warning("SoleScout API rejected authentication (401 Unauthorized)")
            raise SoleScoutAPIError(
                "Invalid or expired SoleScout API key.",
                status_code=401,
                endpoint=clean_endpoint,
            )
        elif status == 403:
            logger.warning("SoleScout API returned 403 Forbidden")
            raise SoleScoutAPIError(
                "Access forbidden by SoleScout API.",
                status_code=403,
                endpoint=clean_endpoint,
            )
        elif status == 404:
            raise SoleScoutAPIError(
                f"Resource not found at /{clean_endpoint}",
                status_code=404,
                endpoint=clean_endpoint,
            )
        elif status == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            logger.warning("Rate limit exceeded on SoleScout API. Retry-After: %s", retry_after)
            raise SoleScoutAPIError(
                f"SoleScout API rate limit exceeded (Retry-After: {retry_after}s).",
                status_code=429,
                endpoint=clean_endpoint,
            )
        elif status >= 500:
            logger.error("SoleScout API server error: HTTP %d", status)
            raise SoleScoutAPIError(
                f"SoleScout API remote server error (HTTP {status}).",
                status_code=status,
                endpoint=clean_endpoint,
            )
        elif status >= 400:
            raise SoleScoutAPIError(
                f"SoleScout API returned HTTP {status}.",
                status_code=status,
                endpoint=clean_endpoint,
            )

        try:
            return response.json()
        except ValueError:
            logger.error("Failed to parse JSON response from %s", clean_endpoint)
            raise SoleScoutAPIError(
                "SoleScout API returned non-JSON response.",
                status_code=500,
                endpoint=clean_endpoint,
            )

    # ---------------------------------------------------------------------------
    # Official SoleScout Endpoints
    # ---------------------------------------------------------------------------

    def search_products(
        self,
        query: str = "Jordan",
        page: int = 1,
        limit: int = 10,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Official Endpoint: GET /api/public/search
        Search sneakers, apparel, and accessories by name, brand, colorway, or style code.

        Parameters:
        - query (q): Model, colorway, or style code (e.g. "samba og", "DD1391-100", "Jordan 1")
        - page: Integer page number (minimum 1, default 1)
        - limit: Number of results (minimum 1, maximum 25, default 10)
        - brand: Exact brand name (grounded via /api/public/brands)
        - category: One of ['shoes', 'clothing', 'accessories', 'bags']
        - gender: One of ['men', 'women', 'youth', 'infant']

        Returns:
        Dict with keys: 'total', 'page', 'limit', 'count', 'results', 'source', 'docs'
        """
        # Validate limit to OpenAPI bounds (1 to 25)
        clamped_limit = max(1, min(limit, 25))
        clamped_page = max(1, page)

        params: Dict[str, Any] = {
            "q": query,
            "page": clamped_page,
            "limit": clamped_limit,
        }
        if brand:
            params["brand"] = brand
        if category:
            params["category"] = category
        if gender:
            params["gender"] = gender

        data = self._get("api/public/search", params=params)
        if isinstance(data, dict):
            return data
        return {"results": data if isinstance(data, list) else [], "count": len(data) if isinstance(data, list) else 0}

    def search_sneakers(
        self,
        query: str = "Jordan",
        limit: int = 10,
        page: int = 1,
        brand: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper returning the list of product items from search.
        Compatible with collector and analytics pipelines.
        """
        response = self.search_products(query=query, page=page, limit=limit, brand=brand)
        if isinstance(response, dict):
            return response.get("results", response.get("data", []))
        return response if isinstance(response, list) else []

    def get_product(
        self,
        slug: Optional[str] = None,
        sku: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Official Endpoint: GET /api/public/product
        Retrieve every store carrying one product, its live price, and in-stock US sizes.

        Parameters:
        - slug: Product slug from searchProducts (e.g. "16-7-jordan-collezione-323941-992")
        - sku: Manufacturer style code (e.g. "DD1391-100", "323941 992")
        """
        if not slug and not sku:
            raise ValueError("Either 'slug' or 'sku' must be provided to get_product.")

        params: Dict[str, Any] = {}
        if slug:
            params["slug"] = slug
        if sku:
            params["sku"] = sku

        return self._get("api/public/product", params=params)

    def get_brands(self) -> Dict[str, Any]:
        """
        Official Endpoint: GET /api/public/brands
        Retrieve all tracked brands with product counts and catalog totals.
        """
        return self._get("api/public/brands")

    def get_price_history(self, identifier: str) -> List[Dict[str, Any]]:
        """
        Retrieve retailer price snapshots for a sneaker by slug or SKU.
        Queries /api/public/product and extracts individual retailer listings.
        """
        try:
            prod = self.get_product(slug=identifier, sku=identifier)
            stores = prod.get("stores", [])
            price_records = []
            for store in stores:
                price = store.get("price_usd")
                if price is not None:
                    price_records.append({
                        "platform": store.get("name", "Retailer"),
                        "price": float(price),
                        "url": store.get("url"),
                        "sizes": store.get("sizes_in_stock", []),
                        "below_retail": store.get("below_retail", False),
                    })
            return price_records
        except SoleScoutAPIError as e:
            logger.warning("Could not retrieve store prices for '%s': %s", identifier, e)
            return []

    # ---------------------------------------------------------------------------
    # Data Normalization
    # ---------------------------------------------------------------------------

    def normalize_product(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw SoleScout product record into a clean, standard schema.
        Maps official response fields safely:
        - style_code -> sku
        - title -> name
        - brand -> brand
        - color -> colorway
        - retail_price_usd -> retail_price
        - lowest_price_usd -> lowest_price
        """
        if not isinstance(raw_item, dict):
            return {}

        sku = raw_item.get("style_code") or raw_item.get("sku")
        title = raw_item.get("title") or raw_item.get("name")
        brand = raw_item.get("brand")
        color = raw_item.get("color") or raw_item.get("colorway")

        # Parse numeric prices safely
        def _to_float(v: Any) -> Optional[float]:
            if v is None:
                return None
            try:
                return round(float(v), 2)
            except (ValueError, TypeError):
                return None

        retail_price = _to_float(raw_item.get("retail_price_usd") or raw_item.get("retail_price"))
        lowest_price = _to_float(raw_item.get("lowest_price_usd") or raw_item.get("price"))

        return {
            "sku": sku or "N/A",
            "name": title or "N/A",
            "brand": brand or "N/A",
            "colorway": color or "N/A",
            "retail_price_usd": retail_price,
            "lowest_price_usd": lowest_price,
            "category": raw_item.get("category", "shoes"),
            "gender": raw_item.get("gender", "unisex"),
            "slug": raw_item.get("slug"),
            "url": raw_item.get("url"),
            "image_url": raw_item.get("image"),
        }
