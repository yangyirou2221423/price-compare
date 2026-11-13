"""Eligibility checks, discount arithmetic and policy-rule materialisation."""

from __future__ import annotations

import math

from .model import (
    Benefit,
    Offer,
    PlatformResult,
    RejectedBenefit,
    SolverContext,
    SubsidyRule,
    money,
)

EPS = 0.005


def _base_for_threshold(benefit: Benefit, offer: Offer, price: float) -> float:
    return offer.list_price if benefit.threshold_base == "list" else price


def _base_for_cap(benefit: Benefit, offer: Offer, price: float) -> float:
    return offer.list_price if benefit.price_cap_base == "list" else price


def check_availability(
    benefit: Benefit,
    offer: Offer,
    ctx: SolverContext,
    price: float,
    used: dict[str, Benefit] | None = None,
    used_groups: set[str] | None = None,
    ignore_thresholds: bool = False,
) -> tuple[bool, str, str]:
    """Return ``(eligible, reason_code, human_reason)`` for a benefit.

    ``price`` is the current price at the point the benefit would be applied.
    The function is pure and is also used to explain rejections in results.
    """

    used = used or {}
    used_groups = used_groups or set()

    if benefit.valid_from and ctx.now < benefit.valid_from:
        return False, "not_started", f"优惠尚未生效（{benefit.valid_from} 起）"
    if benefit.valid_to and ctx.now > benefit.valid_to:
        return False, "expired", f"优惠已于 {benefit.valid_to} 结束"

    req = benefit.requires
    if req.regions and ctx.region not in req.regions and "全国" not in req.regions:
        return False, "region", f"所在地区（{ctx.region}）不参与该优惠"
    if req.memberships:
        missing = [name for name in req.memberships if name not in ctx.memberships]
        if missing:
            return False, "membership", f"需要开通 {'、'.join(missing)} 会员"
    if req.trade_in and ctx.trade_in is None:
        return False, "trade_in", "需要以旧换新资格"
    if req.first_order and not ctx.first_order:
        return False, "first_order", "仅限首单用户"
    if ctx.quantity < req.min_quantity:
        return False, "quantity", f"至少购买 {req.min_quantity} 件"

    if not ignore_thresholds:
        if benefit.price_cap is not None:
            cap_base = _base_for_cap(benefit, offer, price)
            if cap_base > benefit.price_cap + EPS:
                return (
                    False,
                    "price_cap",
                    f"价格 ¥{cap_base:,.0f} 超出补贴上限 ¥{benefit.price_cap:,.0f}",
                )

        threshold_base = _base_for_threshold(benefit, offer, price)
        if threshold_base + EPS < benefit.threshold:
            gap = money(benefit.threshold - threshold_base)
            return (
                False,
                "threshold",
                f"还差 ¥{gap:,.0f} 达到 ¥{benefit.threshold:,.0f} 的使用门槛",
            )

    if benefit.id in used:
        return False, "duplicate", "该优惠已使用"
    if benefit.exclusive_with:
        for other_id in benefit.exclusive_with:
            if other_id in used:
                return (
                    False,
                    "exclusive",
                    f"与已选优惠「{used[other_id].name}」互斥",
                )
    for other in used.values():
        if benefit.id in other.exclusive_with:
            return False, "exclusive", f"与已选优惠「{other.name}」互斥"
    if benefit.stack_group and benefit.stack_group in used_groups:
        return (
            False,
            "stack_group",
            f"与已选优惠属于同一互斥组（{benefit.stack_group}）",
        )

    return True, "", ""


def compute_amount(benefit: Benefit, offer: Offer, ctx: SolverContext, price: float) -> float:
    """Compute the monetary effect of a benefit at ``price`` (always >= 0)."""

    if benefit.kind == "trade_in":
        estimate = ctx.trade_in.estimate if ctx.trade_in else 0.0
        raw = estimate + benefit.value
        return money(max(0.0, min(raw, price)))

    if benefit.value_type == "fixed":
        raw = benefit.value
    elif benefit.value_type == "percent":
        raw = price * benefit.value / 100.0
        if benefit.max_discount is not None:
            raw = min(raw, benefit.max_discount)
    elif benefit.value_type == "per_threshold":
        step = benefit.step or benefit.threshold
        if step <= 0:
            return 0.0
        base = _base_for_threshold(benefit, offer, price)
        raw = math.floor((base + EPS) / step) * benefit.value
        if benefit.max_discount is not None:
            raw = min(raw, benefit.max_discount)
    else:  # price_override is a base-price replacement, not a discount
        raw = max(0.0, price - benefit.value)

    return money(max(0.0, min(raw, price)))


def benefit_upper_bound(benefit: Benefit, offer: Offer, ctx: SolverContext, price: float) -> float:
    """Optimistic amount used for branch-and-bound pruning.

    It deliberately ignores exclusivity and thresholds that depend on the
    future, so it must never underestimate the achievable amount.
    """

    if benefit.kind == "trade_in":
        estimate = ctx.trade_in.estimate if ctx.trade_in else 0.0
        return money(max(0.0, estimate + benefit.value))

    if benefit.value_type == "fixed":
        return money(max(0.0, benefit.value))
    if benefit.value_type == "percent":
        raw = price * benefit.value / 100.0
        if benefit.max_discount is not None:
            raw = min(raw, benefit.max_discount)
        return money(max(0.0, raw))
    if benefit.value_type == "per_threshold":
        step = benefit.step or benefit.threshold
        if step <= 0:
            return 0.0
        base = max(price, offer.list_price)
        raw = math.floor((base + EPS) / step) * benefit.value
        if benefit.max_discount is not None:
            raw = min(raw, benefit.max_discount)
        return money(max(0.0, raw))
    return 0.0


def _rule_matches_category(rule: SubsidyRule, category: str) -> bool:
    return not rule.categories or category in rule.categories


def rule_rejection(
    rule: SubsidyRule,
    offer: Offer,
    ctx: SolverContext,
    category: str,
) -> tuple[bool, str, str]:
    """Check a policy rule against product/platform/region/date/context."""

    if not _rule_matches_category(rule, category):
        return False, "category", "商品品类不参与该补贴"
    if rule.platforms and offer.platform not in rule.platforms:
        return False, "platform", "该平台暂不参与这项补贴"
    if rule.regions and ctx.region not in rule.regions and "全国" not in rule.regions:
        return False, "region", f"所在地区（{ctx.region}）不参与该补贴"
    if rule.effective_from and ctx.now < rule.effective_from:
        return False, "not_started", f"补贴尚未生效（{rule.effective_from} 起）"
    if rule.effective_to and ctx.now > rule.effective_to:
        return False, "expired", f"补贴已于 {rule.effective_to} 结束"
    if rule.requires_membership and rule.requires_membership not in ctx.memberships:
        return False, "membership", f"需要 {rule.requires_membership} 会员"
    if rule.requires_trade_in and ctx.trade_in is None:
        return False, "trade_in", "需要以旧换新资格"
    if (
        rule.price_cap is not None
        and rule.price_cap_base == "list"
        and offer.list_price > rule.price_cap + EPS
    ):
        return (
            False,
            "price_cap",
            f"商品价格 ¥{offer.list_price:,.0f} 超出补贴上限 ¥{rule.price_cap:,.0f}",
        )
    return True, "", ""


def materialize_rule(
    rule: SubsidyRule,
    offer: Offer,
    ctx: SolverContext,
    category: str,
) -> Benefit:
    """Convert a matched subsidy rule into a regular Benefit."""

    kind = "national_subsidy"
    scope = "item"
    if rule.type == "trade_in":
        kind = "trade_in"
        scope = "order"
    elif rule.type == "platform_subsidy":
        kind = "platform_subsidy"
        scope = "platform"

    if rule.percent is not None:
        value_type = "percent"
        value = rule.percent
    else:
        value_type = "fixed"
        value = rule.flat_amount or 0.0

    return Benefit(
        id=f"rule:{rule.id}",
        name=rule.name,
        kind=kind,
        scope=scope,
        value_type=value_type,
        value=value,
        threshold=0.0,
        max_discount=rule.max_discount,
        threshold_base="current",
        price_cap=rule.price_cap,
        price_cap_base=rule.price_cap_base,
        stage=rule.stage,
        stack_group=rule.stack_group,
        exclusive_with=rule.exclusive_with,
        requires={
            "memberships": [rule.requires_membership] if rule.requires_membership else [],
            "regions": rule.regions,
            "trade_in": rule.requires_trade_in,
        },
        valid_from=rule.effective_from,
        valid_to=rule.effective_to,
        description=rule.description,
        source=rule.source,
        rule_id=rule.id,
    )


def build_rule_benefits(
    rules: list[SubsidyRule],
    offer: Offer,
    category: str,
    ctx: SolverContext,
) -> tuple[list[Benefit], list[RejectedBenefit]]:
    """Return benefits generated from rules plus human-readable rejections."""

    benefits: list[Benefit] = []
    rejections: list[RejectedBenefit] = []
    for rule in rules:
        if not _rule_matches_category(rule, category):
            continue
        eligible, code, reason = rule_rejection(rule, offer, ctx, category)
        if not eligible:
            rejections.append(
                RejectedBenefit(
                    benefit_id=f"rule:{rule.id}",
                    name=rule.name,
                    reason_code=code,
                    reason=reason,
                )
            )
            continue
        benefits.append(materialize_rule(rule, offer, ctx, category))
    return benefits, rejections


def result_note(result: PlatformResult) -> str:
    """One-line explanation used in alternative platform cards.

    Missing trade-in eligibility is not a useful headline: it is optional and
    is handled by the main price-gap message.  A failed national/province
    subsidy or a price cap is much more informative.
    """

    for rejection in result.rejected:
        if rejection.reason_code not in {
            "region",
            "platform",
            "price_cap",
            "membership",
            "trade_in",
        }:
            continue
        if "以旧换新" in rejection.name or "trade_in" in rejection.benefit_id:
            continue
        return rejection.reason
    return ""


