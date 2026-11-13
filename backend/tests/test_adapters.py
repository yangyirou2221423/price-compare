"""Adapter contract tests (no network access)."""

from __future__ import annotations

import pytest

from app.adapters import build_adapters
from app.adapters.base import DataSourceUnavailable
from app.adapters.league import JDUnionDataSource
from app.engine.model import Offer, Product


def sample_product() -> Product:
    return Product(
        id="P1",
        title="测试商品",
        category="手机",
        offers=[
            Offer(
                id="O1",
                product_id="P1",
                platform="jd",
                platform_name="京东",
                list_price=1000,
            )
        ],
    )


def test_mock_adapter_returns_seeded_offers() -> None:
    product = sample_product()
    adapters = build_adapters({product.id: product})
    mock = adapters[0]
    assert mock.available is True
    assert mock.fetch_offers(product)[0].id == "O1"


def test_league_adapter_is_credential_gated() -> None:
    adapter = JDUnionDataSource()
    assert adapter.available is False
    with pytest.raises(DataSourceUnavailable):
        adapter.fetch_offers(sample_product())
