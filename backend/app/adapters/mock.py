"""Mock adapter backed by the seeded in-memory catalogue."""

from __future__ import annotations

from app.adapters.base import PlatformDataSource
from app.engine.model import Offer, Product


class MockDataSource(PlatformDataSource):
    source_id = "mock"
    platform = "all"
    display_name = "内置演示数据"
    requires_credentials = False

    def __init__(self, products: dict[str, Product]):
        self._products = products

    def fetch_offers(self, product: Product) -> list[Offer]:
        current = self._products.get(product.id, product)
        return list(current.offers)
