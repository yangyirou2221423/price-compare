"""Tests for cart splitting, order-level deals and filler suggestions."""

from __future__ import annotations

from datetime import date

import pytest

from app.engine.cart_solver import optimize_cart, suggest_fillers
from app.engine.model import (
    Benefit,
    CartItemInput,
    Offer,
    Product,
    Requirements,
    SolverContext,
)
from app.engine.stacker import compare_product

NOW = date(2026, 11, 13)


def benefit(
    benefit_id: str,
    *,
    value: float,
    threshold: float,
    kind: str = "full_reduction",
    stage: int = 3,
    scope: str = "platform",
    value_type: str = "fixed",
    max_discount: float | None = None,
    stack_group: str | None = None,
) -> Benefit:
    return Benefit(
        id=benefit_id,
        name=benefit_id,
        kind=kind,
        scope=scope,
        value_type=value_type,
        value=value,
        threshold=threshold,
        max_discount=max_discount,
        stage=stage,
        stack_group=stack_group,
        requires=Requirements(),
        threshold_base="list",
    )


def offer(product_id: str, platform: str, price: float, benefits: list[Benefit] | None = None) -> Offer:
    names = {"jd": "京东", "taobao": "淘宝", "pdd": "拼多多"}
    return Offer(
        id=f"O-{product_id}-{platform}",
        product_id=product_id,
        platform=platform,
        platform_name=names[platform],
        list_price=price,
        benefits=benefits or [],
    )


def jd_full() -> Benefit:
    return benefit("JD-FULL-3000-300", value=300, threshold=3000)


def tb_full() -> Benefit:
    return benefit("TB-FULL-4000-400", value=400, threshold=4000)


def build_products() -> dict[str, Product]:
    p1 = Product(
        id="P1",
        title="扫地机器人",
        category="家电",
        offers=[
            offer("P1", "jd", 2920, [jd_full()]),
            offer("P1", "taobao", 3199, [tb_full()]),
            offer("P1", "pdd", 2999),
        ],
    )
    p2 = Product(
        id="P2",
        title="降噪耳机",
        category="耳机",
        offers=[
            offer("P2", "jd", 1299, [jd_full()]),
            offer("P2", "taobao", 1199, [tb_full()]),
            offer("P2", "pdd", 1099),
        ],
    )
    p3 = Product(
        id="P3",
        title="投影仪",
        category="影音",
        offers=[
            offer("P3", "jd", 2999, [jd_full()]),
            offer("P3", "taobao", 2899, [tb_full()]),
            offer("P3", "pdd", 2799),
        ],
    )
    p4 = Product(
        id="P4",
        title="桌面收纳盒",
        category="家居",
        offers=[offer("P4", "jd", 89)],
    )
    return {product.id: product for product in [p1, p2, p3, p4]}


def context() -> SolverContext:
    return SolverContext(now=NOW, region="浙江")


def test_cart_splits_items_to_use_platform_thresholds() -> None:
    products = build_products()
    result = optimize_cart(
        [
            CartItemInput(product_id="P1"),
            CartItemInput(product_id="P2"),
            CartItemInput(product_id="P3"),
        ],
        products,
        context(),
    )

    assert result.total_payment == pytest.approx(6618)
    assert result.assignment == {"P1": "jd", "P2": "taobao", "P3": "taobao"}
    assert len(result.orders) == 2
    assert result.baseline_payment == pytest.approx(6897)
    assert result.savings_vs_baseline == pytest.approx(279)
    assert result.optimal is True


def test_cart_single_item_and_filler_suggestion() -> None:
    products = build_products()
    items = [CartItemInput(product_id="P1")]
    result = optimize_cart(items, products, context())

    assert result.total_payment == pytest.approx(2920)
    suggestions = suggest_fillers(items, products, context(), [], result)
    assert suggestions
    assert suggestions[0].gap == pytest.approx(80)
    top = suggestions[0].candidates[0]
    assert top.product_id == "P4"
    assert top.new_total == pytest.approx(2709)
    assert top.net_increase == pytest.approx(-211)


def test_cart_quantity_is_multiplied() -> None:
    products = build_products()
    result = optimize_cart(
        [CartItemInput(product_id="P4", quantity=3)],
        products,
        context(),
    )
    assert result.total_payment == pytest.approx(267)


def test_single_item_full_reduction_not_applied_below_threshold() -> None:
    products = build_products()
    result = compare_product(products["P1"], context())
    assert result.best_platform == "jd"
    assert result.best.final_price == pytest.approx(2920)
    assert any(item.reason_code == "threshold" for item in result.best.rejected)
