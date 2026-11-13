"""Single-item strategy solver: constrained benefit selection + branch & bound."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .model import (
    AppliedBenefit,
    Benefit,
    Offer,
    PlatformResult,
    Product,
    RejectedBenefit,
    SolverContext,
    StrategyResult,
    SubsidyRule,
    money,
)
from .rules import (
    benefit_upper_bound,
    build_rule_benefits,
    check_availability,
    compute_amount,
    result_note,
)

ENGINE_VERSION = "0.1.0"
MAX_EXACT_BENEFITS = 18
CN_TZ = timezone(timedelta(hours=8))
EPS = 0.005


@dataclass
class _State:
    price: float
    net: float
    used: dict[str, Benefit]
    groups: set[str]
    stage: int
    trace: list[AppliedBenefit] = field(default_factory=list)


def _objective(price: float, net: float, shipping: float, preference: str) -> tuple[float, float]:
    final = money(price + shipping)
    net_price = money(max(0.0, price - net) + shipping)
    if preference == "net":
        return net_price, final
    return final, net_price


def _make_step(
    benefit: Benefit,
    amount: float,
    price_before: float,
    price_after: float,
) -> AppliedBenefit:
    return AppliedBenefit(
        benefit_id=benefit.id,
        name=benefit.name,
        kind=benefit.kind,
        stage=benefit.stage,
        amount=money(amount),
        price_before=money(price_before),
        price_after=money(price_after),
        is_net_benefit=benefit.is_net_benefit,
        description=benefit.description,
        rule_id=benefit.rule_id,
    )


def _prepare(
    offer: Offer,
    ctx: SolverContext,
    allowed_scopes: set[str] | None = None,
) -> tuple[float, dict[str, Benefit], set[str], list[AppliedBenefit], list[Benefit], list[RejectedBenefit]]:
    """Choose the activity price, merge policy benefits and dedupe by id."""

    all_benefits: dict[str, Benefit] = {}
    for benefit in offer.benefits:
        all_benefits.setdefault(benefit.id, benefit)

    def in_scope(benefit: Benefit) -> bool:
        return allowed_scopes is None or benefit.scope in allowed_scopes

    overrides = [
        b for b in all_benefits.values() if b.value_type == "price_override" and in_scope(b)
    ]
    eligible_overrides: list[Benefit] = []
    override_rejections: list[RejectedBenefit] = []
    for benefit in overrides:
        ok, code, reason = check_availability(
            benefit,
            offer,
            ctx,
            offer.list_price,
            ignore_thresholds=True,
        )
        if ok and benefit.value < offer.list_price - EPS:
            eligible_overrides.append(benefit)
        elif ok:
            override_rejections.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code="not_lower",
                    reason="活动价不低于页面标价，未采用",
                )
            )
        else:
            override_rejections.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code=code,
                    reason=reason,
                )
            )

    chosen: Benefit | None = None
    if eligible_overrides:
        chosen = min(eligible_overrides, key=lambda b: (b.value, b.id))
        for benefit in eligible_overrides:
            if benefit.id != chosen.id:
                override_rejections.append(
                    RejectedBenefit(
                        benefit_id=benefit.id,
                        name=benefit.name,
                        reason_code="better_override",
                        reason=f"存在更低的平台活动价 ¥{chosen.value:,.0f}",
                    )
                )

    base_price = money(chosen.value if chosen else offer.list_price)
    used: dict[str, Benefit] = {}
    groups: set[str] = set()
    trace: list[AppliedBenefit] = []
    if chosen:
        used[chosen.id] = chosen
        if chosen.stack_group:
            groups.add(chosen.stack_group)
        if base_price < offer.list_price - EPS:
            trace.append(
                _make_step(
                    chosen,
                    offer.list_price - base_price,
                    offer.list_price,
                    base_price,
                )
            )

    optional = [
        b
        for b in all_benefits.values()
        if b.value_type != "price_override" and b.id not in used and in_scope(b)
    ]
    optional.sort(key=lambda b: (b.stage, b.id))
    return base_price, used, groups, trace, optional, override_rejections


def _rejections_for_best(
    optional: list[Benefit],
    offer: Offer,
    ctx: SolverContext,
    best: _State,
    initial_rejections: list[RejectedBenefit],
) -> list[RejectedBenefit]:
    rejections: list[RejectedBenefit] = list(initial_rejections)
    seen = {item.benefit_id for item in rejections}
    for benefit in optional:
        if benefit.id in best.used or benefit.id in seen:
            continue
        ok, code, reason = check_availability(
            benefit,
            offer,
            ctx,
            best.price,
            best.used,
            best.groups,
        )
        if not ok:
            rejections.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code=code,
                    reason=reason,
                )
            )
        else:
            rejections.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code="not_optimal",
                    reason="未采用：加入组合后不能进一步降低实付",
                )
            )
        seen.add(benefit.id)
    return rejections


def _greedy(
    optional: list[Benefit],
    offer: Offer,
    ctx: SolverContext,
    base_price: float,
    used: dict[str, Benefit],
    groups: set[str],
    trace: list[AppliedBenefit],
) -> _State:
    """Fallback for unusually large instances; results are marked non-optimal."""

    state = _State(price=base_price, net=0.0, used=dict(used), groups=set(groups), stage=0, trace=list(trace))
    while True:
        candidates: list[tuple[float, Benefit]] = []
        for benefit in optional:
            if benefit.id in state.used or benefit.stage < state.stage:
                continue
            ok, _, _ = check_availability(
                benefit,
                offer,
                ctx,
                state.price,
                state.used,
                state.groups,
            )
            if ok:
                candidates.append((benefit_upper_bound(benefit, offer, ctx, state.price), benefit))
        if not candidates:
            break
        candidates.sort(key=lambda item: (-item[0], item[1].stage, item[1].id))
        _, benefit = candidates[0]
        amount = compute_amount(benefit, offer, ctx, state.price)
        if amount <= EPS:
            break
        before = state.price
        if benefit.is_net_benefit:
            state.net = money(state.net + amount)
            after = state.price
        else:
            state.price = money(max(0.0, state.price - amount))
            after = state.price
        state.used[benefit.id] = benefit
        if benefit.stack_group:
            state.groups.add(benefit.stack_group)
        state.stage = benefit.stage
        state.trace.append(_make_step(benefit, amount, before, after))
    return state


def solve_offer(
    offer: Offer,
    product: Product,
    ctx: SolverContext,
    rules: list[SubsidyRule] | None = None,
    allowed_scopes: set[str] | None = None,
) -> PlatformResult:
    """Find the cheapest legal benefit combination for one platform offer.

    ``allowed_scopes`` is used by the cart solver to price a line with only
    item/shop benefits; order-level benefits are applied once per platform
    order instead.
    """

    rules = rules or []
    rule_benefits, rule_rejections = build_rule_benefits(rules, offer, product.category, ctx)
    merged: dict[str, Benefit] = {}
    for benefit in [*offer.benefits, *rule_benefits]:
        merged.setdefault(benefit.id, benefit)
    offer_with_rules = offer.model_copy(update={"benefits": list(merged.values())})

    base_price, used, groups, trace, optional, override_rejections = _prepare(
        offer_with_rules, ctx, allowed_scopes
    )
    initial_rejections = [*rule_rejections, *override_rejections]

    initial = _State(
        price=base_price,
        net=0.0,
        used=dict(used),
        groups=set(groups),
        stage=0,
        trace=list(trace),
    )
    best = initial
    best_key = _objective(initial.price, initial.net, offer.shipping_fee, ctx.preference)
    optimal = True

    if len(optional) > MAX_EXACT_BENEFITS:
        best = _greedy(optional, offer, ctx, base_price, used, groups, trace)
        optimal = False
    else:
        optional_ids = {b.id: index for index, b in enumerate(optional)}
        memo: dict[tuple[int, int, int], float] = {}

        def dfs(state: _State) -> None:
            nonlocal best, best_key
            key = _objective(state.price, state.net, offer.shipping_fee, ctx.preference)
            if key < best_key:
                best_key = key
                best = state

            remaining = [b for b in optional if b.id not in state.used and b.stage >= state.stage]
            if not remaining:
                return

            payment_bound = sum(
                benefit_upper_bound(b, offer, ctx, state.price)
                for b in remaining
                if b.affects_payment
            )
            net_bound = sum(
                benefit_upper_bound(b, offer, ctx, state.price)
                for b in remaining
                if b.is_net_benefit
            )
            optimistic_final = money(max(0.0, state.price - payment_bound) + offer.shipping_fee)
            optimistic_net = money(
                max(0.0, state.price - payment_bound - net_bound) + offer.shipping_fee
            )
            if ctx.preference == "net":
                optimistic_key = (optimistic_net, optimistic_final)
            else:
                optimistic_key = (optimistic_final, optimistic_net)
            if optimistic_key >= best_key:
                return

            mask = 0
            for benefit_id in state.used:
                index = optional_ids.get(benefit_id)
                if index is not None:
                    mask |= 1 << index
            memo_key = (mask, state.stage, round(state.price * 100))
            previous_net = memo.get(memo_key)
            if previous_net is not None and previous_net <= state.net + EPS:
                return
            memo[memo_key] = state.net

            for benefit in optional:
                if benefit.id in state.used or benefit.stage < state.stage:
                    continue
                ok, _, _ = check_availability(
                    benefit,
                    offer,
                    ctx,
                    state.price,
                    state.used,
                    state.groups,
                )
                if not ok:
                    continue
                amount = compute_amount(benefit, offer, ctx, state.price)
                if amount <= EPS:
                    continue
                before = state.price
                if benefit.is_net_benefit:
                    new_price = state.price
                    new_net = money(state.net + amount)
                else:
                    new_price = money(max(0.0, state.price - amount))
                    new_net = state.net
                new_state = _State(
                    price=new_price,
                    net=new_net,
                    used={**state.used, benefit.id: benefit},
                    groups=set(state.groups),
                    stage=benefit.stage,
                    trace=[*state.trace, _make_step(benefit, amount, before, new_price)],
                )
                if benefit.stack_group:
                    new_state.groups.add(benefit.stack_group)
                dfs(new_state)

        dfs(initial)

    final_price = money(best.price + offer.shipping_fee)
    net_price = money(max(0.0, best.price - best.net) + offer.shipping_fee)
    discount_total = money(offer.list_price + offer.shipping_fee - final_price)
    trade_in_value = money(sum(s.amount for s in best.trace if s.kind == "trade_in"))
    rebate_value = money(sum(s.amount for s in best.trace if s.kind == "rebate"))
    gift_value = money(sum(s.amount for s in best.trace if s.kind == "gift"))
    promo_savings = money(max(0.0, discount_total - trade_in_value))
    gross = offer.list_price + offer.shipping_fee
    savings_pct = round(promo_savings / gross * 100, 2) if gross > 0 else 0.0

    rejected = _rejections_for_best(optional, offer, ctx, best, initial_rejections)
    return PlatformResult(
        offer_id=offer.id,
        platform=offer.platform,
        platform_name=offer.platform_name,
        shop_name=offer.shop_name,
        list_price=money(offer.list_price),
        shipping_fee=money(offer.shipping_fee),
        base_price=money(base_price),
        goods_price=money(best.price),
        final_price=final_price,
        net_price=net_price,
        discount_total=discount_total,
        promo_savings=promo_savings,
        trade_in_value=trade_in_value,
        rebate_value=rebate_value,
        gift_value=gift_value,
        savings_pct=savings_pct,
        applied=best.trace,
        rejected=rejected,
        optimal=optimal,
    )


def compare_product(
    product: Product,
    ctx: SolverContext,
    rules: list[SubsidyRule] | None = None,
) -> StrategyResult:
    """Compare every offer for a product and return the recommended strategy."""

    rules = rules or []
    results = [solve_offer(offer, product, ctx, rules) for offer in product.offers]
    if not results:
        raise ValueError(f"product {product.id} has no offers")

    results.sort(
        key=lambda r: (
            (r.net_price, r.final_price)
            if ctx.preference == "net"
            else (r.final_price, r.net_price)
        )
    )
    best = results[0]
    worst = results[-1]
    for result in results[1:]:
        note = result_note(result)
        if ctx.preference == "net":
            gap = money(result.net_price - best.net_price)
        else:
            gap = money(result.final_price - best.final_price)
        if gap <= EPS:
            result.note = "与最优方案同价"
        elif note:
            result.note = f"{note}；比最优方案高 ¥{gap:,.0f}"
        else:
            result.note = f"比最优方案{'净价' if ctx.preference == 'net' else '实付'}高 ¥{gap:,.0f}"

    gross = best.list_price + best.shipping_fee
    savings_abs = best.promo_savings
    savings_pct = round(savings_abs / gross * 100, 2) if gross > 0 else 0.0

    if savings_abs > 0:
        parts = [
            f"在{best.platform_name}下单最省：预计实付 ¥{best.final_price:,.0f}",
            f"比页面标价省 ¥{savings_abs:,.0f}",
        ]
    else:
        parts = [
            f"在{best.platform_name}下单：当前预计实付 ¥{best.final_price:,.0f}",
            "页面优惠后已是演示数据中的最低价",
        ]
    if best.trade_in_value > 0:
        parts.append(f"其中旧机抵扣 ¥{best.trade_in_value:,.0f}")
    if best.net_price < best.final_price - EPS:
        parts.append(f"计入返利/赠品后约 ¥{best.net_price:,.0f}")
    if len(results) > 1:
        gap = money(worst.final_price - best.final_price)
        if gap > 0:
            parts.append(f"比最贵的平台（{worst.platform_name}）少 ¥{gap:,.0f}")
    threshold_hint = next(
        (item.reason for item in best.rejected if item.reason_code == "threshold"),
        "",
    )
    summary = "，".join(parts) + "。"
    if threshold_hint:
        summary += f"提示：{threshold_hint}，可考虑凑单。"

    assumptions = [
        "价格为演示数据，仅用于验证比价与优惠叠加逻辑，不代表实时售价。",
        "国补与平台补贴为可配置示例规则，实际以当地最新政策和平台页面为准。",
        "返利按实付比例估算，未考虑提现门槛、到账周期与平台风控。",
    ]
    if ctx.region:
        assumptions.append(f"当前地区：{ctx.region}；会员：{'、'.join(ctx.memberships) or '无'}。")
    if ctx.trade_in:
        assumptions.append(
            f"旧机估值 ¥{ctx.trade_in.estimate:,.0f} 按用户输入计算，实际以回收商检测为准。"
        )

    sources = {offer.source for offer in product.offers}
    data_source = "mock" if sources <= {"mock"} else ("mixed" if "mock" in sources else "affiliate")

    return StrategyResult(
        product_id=product.id,
        product_title=product.title,
        product_image=product.image,
        product_category=product.category,
        region=ctx.region,
        preference=ctx.preference,
        best_platform=best.platform,
        best_offer_id=best.offer_id,
        best=best,
        results=results,
        savings_abs=money(savings_abs),
        savings_pct=savings_pct,
        summary=summary,
        assumptions=assumptions,
        engine_version=ENGINE_VERSION,
        data_source=data_source,
        generated_at=datetime.now(CN_TZ),
        optimal=all(result.optimal for result in results),
    )
