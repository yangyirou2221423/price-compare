"""Tests for the single-item discount solver."""

from __future__ import annotations

import random
from datetime import date

import pytest

from app.engine.model import (
    Benefit,
    Offer,
    Product,
    Requirements,
    SolverContext,
    SubsidyRule,
    TradeIn,
    money,
)
from app.engine.rules import check_availability, compute_amount
from app.engine.stacker import compare_product, solve_offer

NOW = date(2026, 11, 13)


def make_benefit(
    benefit_id: str,
    *,
    kind: str = "store_coupon",
    value_type: str = "fixed",
    value: float = 100,
    threshold: float = 0,
    step: float | None = None,
    max_discount: float | None = None,
    stage: int = 1,
    stack_group: str | None = None,
    exclusive_with: list[str] | None = None,
    requires: dict | None = None,
    scope: str = "item",
    threshold_base: str = "list",
    price_cap: float | None = None,
    price_cap_base: str = "list",
) -> Benefit:
    return Benefit(
        id=benefit_id,
        name=benefit_id,
        kind=kind,
        scope=scope,
        value_type=value_type,
        value=value,
        threshold=threshold,
        step=step,
        max_discount=max_discount,
        stage=stage,
        stack_group=stack_group,
        exclusive_with=exclusive_with or [],
        requires=Requirements(**(requires or {})),
        threshold_base=threshold_base,
        price_cap=price_cap,
        price_cap_base=price_cap_base,
    )


def make_offer(offer_id: str, price: float, benefits: list[Benefit], platform: str = "jd") -> Offer:
    return Offer(
        id=offer_id,
        product_id="P1",
        platform=platform,
        platform_name={"jd": "京东", "taobao": "淘宝", "pdd": "拼多多"}.get(platform, platform),
        list_price=price,
        benefits=benefits,
    )


def make_product(category: str, offers: list[Offer]) -> Product:
    return Product(id="P1", title="测试商品", category=category, offers=offers)


def ctx(**kwargs) -> SolverContext:
    data = {"now": NOW, "region": "浙江", "memberships": []}
    data.update(kwargs)
    return SolverContext(**data)


def test_fixed_coupons_and_stack_group() -> None:
    benefits = [
        make_benefit("A", value=100, threshold=500, stage=1),
        make_benefit("B", value=200, threshold=500, stage=2, stack_group="g"),
        make_benefit("C", value=300, threshold=500, stage=2, stack_group="g"),
        make_benefit("D", value_type="percent", value=10, max_discount=50, stage=3),
    ]
    product = make_product("手机", [make_offer("O1", 1000, benefits)])
    result = solve_offer(product.offers[0], product, ctx())

    assert result.final_price == pytest.approx(550)
    assert {step.benefit_id for step in result.applied} == {"A", "C", "D"}
    rejected = {item.benefit_id: item for item in result.rejected}
    assert rejected["B"].reason_code == "stack_group"


def test_national_subsidy_reverses_lowest_list_price() -> None:
    rule = SubsidyRule(
        id="R-MOBILE",
        name="手机购新补贴（示例）",
        type="national_subsidy",
        regions=["全国"],
        categories=["手机"],
        platforms=["taobao"],
        price_cap=6000,
        percent=15,
        max_discount=500,
        stage=6,
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
    )
    jd = make_offer(
        "JD",
        5899,
        [
            make_benefit("JD-PLATFORM", value=200, threshold=5000, stage=2, scope="platform"),
            make_benefit("JD-STORE", value=100, threshold=5000, stage=1),
        ],
        "jd",
    )
    taobao = make_offer(
        "TB",
        5999,
        [make_benefit("TB-STORE", value=400, threshold=5000, stage=1)],
        "taobao",
    )
    pdd = make_offer(
        "PDD",
        5499,
        [make_benefit("PDD-ACTIVITY", value_type="price_override", value=5299, stage=0)],
        "pdd",
    )
    product = make_product("手机", [jd, taobao, pdd])
    strategy = compare_product(product, ctx(), [rule])

    assert strategy.best_platform == "taobao"
    assert strategy.best.final_price == pytest.approx(5099)
    assert strategy.savings_abs == pytest.approx(900)
    assert [r.platform for r in strategy.results] == ["taobao", "pdd", "jd"]
    jd_result = next(r for r in strategy.results if r.platform == "jd")
    assert jd_result.final_price == pytest.approx(5599)
    assert any(item.reason_code == "platform" for item in jd_result.rejected)


def test_trade_in_and_subsidy_sequence() -> None:
    rules = [
        SubsidyRule(
            id="R-APPLIANCE",
            name="家电补贴（示例）",
            type="national_subsidy",
            regions=["全国"],
            categories=["家电"],
            platforms=["jd"],
            price_cap=6000,
            percent=15,
            max_discount=500,
            stage=6,
        ),
        SubsidyRule(
            id="R-TRADEIN",
            name="以旧换新（示例）",
            type="trade_in",
            regions=["全国"],
            categories=["家电"],
            platforms=["jd"],
            requires_trade_in=True,
            flat_amount=0,
            stage=7,
        ),
    ]
    offer = make_offer(
        "JD",
        3299,
        [make_benefit("JD-PLATFORM", value=200, threshold=2000, stage=2, scope="platform")],
        "jd",
    )
    product = make_product("家电", [offer])
    result = solve_offer(
        offer,
        product,
        ctx(trade_in=TradeIn(device_name="旧净化器", estimate=300)),
        rules,
    )

    # 3299 - 200 = 3099; 国补 15% = 464.85; 旧机 300
    assert result.final_price == pytest.approx(2334.15)
    assert result.trade_in_value == pytest.approx(300)
    assert result.promo_savings == pytest.approx(664.85)
    kinds = [step.kind for step in result.applied]
    assert kinds.index("national_subsidy") < kinds.index("trade_in")


def test_member_price_and_rebate_improve_net_value() -> None:
    offer = make_offer(
        "TB",
        4999,
        [
            make_benefit("TB-STORE", value=200, threshold=1000, stage=1),
            make_benefit(
                "TB-VIP",
                kind="member",
                value_type="percent",
                value=5,
                stage=4,
                scope="platform",
                requires={"memberships": ["88VIP"]},
            ),
            make_benefit(
                "TB-REBATE",
                kind="rebate",
                value_type="percent",
                value=2,
                max_discount=100,
                stage=9,
                scope="platform",
            ),
        ],
        "taobao",
    )
    product = make_product("笔记本", [offer])
    with_vip = solve_offer(offer, product, ctx(memberships=["88VIP"]))
    without_vip = solve_offer(offer, product, ctx())

    assert with_vip.final_price == pytest.approx(4559.05)
    assert with_vip.net_price == pytest.approx(4467.87)
    assert with_vip.rebate_value == pytest.approx(91.18)
    assert without_vip.final_price == pytest.approx(4799)
    assert without_vip.net_price == pytest.approx(4703.02)


def test_price_cap_rejection_is_explained() -> None:
    rule = SubsidyRule(
        id="R-LAPTOP",
        name="电脑补贴（示例）",
        type="national_subsidy",
        regions=["全国"],
        categories=["笔记本"],
        price_cap=7000,
        percent=10,
        max_discount=500,
        stage=6,
    )
    offer = make_offer("JD", 7999, [], "jd")
    product = make_product("笔记本", [offer])
    result = solve_offer(offer, product, ctx(), [rule])

    assert result.final_price == pytest.approx(7999)
    assert any(item.reason_code == "price_cap" for item in result.rejected)


def brute_force(offer: Offer, context: SolverContext) -> tuple[float, float]:
    """Enumerate every legal application sequence without pruning."""

    best = (offer.list_price + offer.shipping_fee, offer.list_price + offer.shipping_fee)

    def key(price: float, net: float) -> tuple[float, float]:
        final = money(price + offer.shipping_fee)
        net_price = money(max(0.0, price - net) + offer.shipping_fee)
        return (net_price, final) if context.preference == "net" else (final, net_price)

    best = key(offer.list_price, 0.0)

    def dfs(price: float, net: float, used: dict[str, Benefit], groups: set[str], stage: int) -> None:
        nonlocal best
        best = min(best, key(price, net))
        for benefit in offer.benefits:
            if benefit.id in used or benefit.stage < stage:
                continue
            ok, _, _ = check_availability(benefit, offer, context, price, used, groups)
            if not ok:
                continue
            amount = compute_amount(benefit, offer, context, price)
            if amount <= 0.005:
                continue
            if benefit.is_net_benefit:
                dfs(price, money(net + amount), {**used, benefit.id: benefit}, set(groups), benefit.stage)
            else:
                dfs(
                    money(max(0.0, price - amount)),
                    net,
                    {**used, benefit.id: benefit},
                    groups | ({benefit.stack_group} if benefit.stack_group else set()),
                    benefit.stage,
                )

    dfs(offer.list_price, 0.0, {}, set(), 0)
    return best


def test_branch_and_bound_matches_brute_force() -> None:
    rng = random.Random(20261113)
    for case in range(100):
        benefits: list[Benefit] = []
        count = rng.randint(3, 6)
        for index in range(count):
            value_type = rng.choice(["fixed", "percent"])
            value = rng.randint(20, 300) if value_type == "fixed" else rng.randint(3, 20)
            benefits.append(
                make_benefit(
                    f"B{index}",
                    value_type=value_type,
                    value=value,
                    threshold=rng.choice([0, 0, 0, 200, 500]),
                    max_discount=rng.choice([None, 50, 100]) if value_type == "percent" else None,
                    stage=rng.randint(1, 4),
                    stack_group=rng.choice([None, None, "g1", "g2"]),
                    exclusive_with=[f"B{index - 1}"] if index and rng.random() < 0.15 else [],
                )
            )
        offer = make_offer(f"CASE{case}", rng.randint(500, 2500), benefits)
        product = make_product("测试", [offer])
        result = solve_offer(offer, product, ctx())
        expected_final, expected_net = brute_force(offer, ctx())
        assert result.final_price == pytest.approx(expected_final), f"case {case} final"
        assert result.net_price == pytest.approx(expected_net), f"case {case} net"
