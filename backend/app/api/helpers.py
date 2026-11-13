"""Shared route helpers."""

from __future__ import annotations

from datetime import date

from app.config import DEMO_NOW
from app.engine.model import Product, SolverContext, SubsidyRule, TradeIn
from app.engine.stacker import compare_product
from app.schemas.api import ProductCard

PLATFORM_NAME = {"jd": "京东", "taobao": "淘宝", "pdd": "拼多多", "douyin": "抖音"}
DATA_NOTE = "演示数据，非实时价格；国补与平台规则为可配置示例。"


def default_now() -> date:
    """Keep the demo reproducible even if the machine clock changes."""

    return date.fromisoformat(DEMO_NOW)


def build_context(
    *,
    region: str = "浙江",
    memberships: list[str] | None = None,
    trade_in: TradeIn | None = None,
    preference: str = "payment",
    now: date | None = None,
) -> SolverContext:
    return SolverContext(
        region=region,
        memberships=memberships or [],
        trade_in=trade_in,
        preference=preference,  # type: ignore[arg-type]
        now=now or default_now(),
    )


def product_card(product: Product, ctx: SolverContext, rules: list[SubsidyRule]) -> ProductCard:
    strategy = compare_product(product, ctx, rules)
    best = strategy.best
    return ProductCard(
        id=product.id,
        title=product.title,
        brand=product.brand,
        category=product.category,
        specs=product.specs,
        image=product.image,
        tags=product.tags,
        featured=product.featured,
        offer_count=len(product.offers),
        best_platform=best.platform,
        best_platform_name=best.platform_name,
        best_price=best.final_price,
        net_price=best.net_price,
        list_price=best.list_price,
        savings=strategy.savings_abs,
        savings_pct=strategy.savings_pct,
        summary=strategy.summary,
        data_source=strategy.data_source,
    )
