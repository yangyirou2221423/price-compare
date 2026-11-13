"""Adapter registry used by the API / documentation."""

from __future__ import annotations

from app.adapters.base import DataSourceUnavailable, PlatformDataSource
from app.adapters.league import (
    DouyinUnionDataSource,
    JDUnionDataSource,
    PDDUnionDataSource,
    TaobaoKeDataSource,
)
from app.adapters.mock import MockDataSource
from app.engine.model import Product

__all__ = [
    "DataSourceUnavailable",
    "DouyinUnionDataSource",
    "JDUnionDataSource",
    "MockDataSource",
    "PDDUnionDataSource",
    "PlatformDataSource",
    "TaobaoKeDataSource",
    "adapter_status",
    "build_adapters",
]


def build_adapters(products: dict[str, Product]) -> list[PlatformDataSource]:
    return [
        MockDataSource(products),
        JDUnionDataSource(),
        TaobaoKeDataSource(),
        PDDUnionDataSource(),
        DouyinUnionDataSource(),
    ]


def adapter_status(products: dict[str, Product]) -> list[dict]:
    return [adapter.describe() for adapter in build_adapters(products)]
