"""Data-source adapter contract.

The demo never scrapes platform pages.  Real integrations (JD Union,
Taobao Ke, PDD Jinbao) implement this interface behind credentials and
commercial agreements, while the mock adapter serves the seeded catalogue.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.engine.model import Offer, Product


class DataSourceUnavailable(RuntimeError):
    """Raised when a real adapter is called without credentials/approval."""


class PlatformDataSource(ABC):
    source_id: str
    platform: str
    display_name: str
    requires_credentials: bool = False

    @property
    def available(self) -> bool:
        return True

    @abstractmethod
    def fetch_offers(self, product: Product) -> list[Offer]:
        """Return platform offers for a canonical product."""

    def describe(self) -> dict:
        return {
            "source_id": self.source_id,
            "platform": self.platform,
            "display_name": self.display_name,
            "available": self.available,
            "requires_credentials": self.requires_credentials,
        }
