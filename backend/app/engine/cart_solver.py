"""Cart optimisation: split items across platforms and apply order-level deals."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from datetime import datetime

from .model import (
    AppliedBenefit,
    Benefit,
    CartItemInput,
    CartLine,
    CartOrder,
    CartResult,
    FillerCandidate,
    FillerSuggestion,
    Offer,
    PlatformResult,
    Product,
    RejectedBenefit,
    SolverContext,
    SubsidyRule,
    money,
)
from .rules import (
    benefit_upper_bound,
    build_rule_benefits,
    check_availability,
    compute_amount,
)
from .stacker import CN_TZ, ENGINE_VERSION, solve_offer

MAX_EXACT_ASSIGNMENTS = 100_000
MAX_EXACT_ITEMS = 7
EPS = 0.005
PLATFORM_ORDER = ["jd", "taobao", "pdd", "douyin"]


@dataclass
class _LineCandidate:
    product: Product
    offer: Offer
    quantity: int
    result: PlatformResult
    goods_price: float
    list_subtotal: float
    discount: float
    shipping: float


@dataclass
class _OrderState:
    subtotal: float
    net: float
    used: dict[str, Benefit]
    groups: set[str]
    stage: int
    trace: list[AppliedBenefit] = field(default_factory=list)


@dataclass
class _OrderSolution:
    platform: str
    platform_name: str
    lines: list[CartLine]
    list_subtotal: float
    line_discount_total: float
    order_discount_total: float
    final_price: float
    net_price: float
    rebate_value: float
    order_applied: list[AppliedBenefit]
    order_rejected: list[RejectedBenefit]
    optimal: bool


@dataclass
class _Evaluation:
    orders: list[_OrderSolution]
    total_payment: float
    total_net: float
    optimal: bool
    assignment: dict[str, str]


def _platform_rank(platform: str) -> int:
    return PLATFORM_ORDER.index(platform) if platform in PLATFORM_ORDER else len(PLATFORM_ORDER)


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


def _order_key(payment: float, net: float, preference: str) -> tuple[float, float]:
    return (net, payment) if preference == "net" else (payment, net)


def _line_candidates(
    product: Product,
    quantity: int,
    ctx: SolverContext,
    rules: list[SubsidyRule],
) -> dict[str, _LineCandidate]:
    """Price every platform option using item/shop benefits only."""

    by_platform: dict[str, _LineCandidate] = {}
    for offer in product.offers:
        result = solve_offer(
            offer,
            product,
            ctx,
            rules,
            allowed_scopes={"item", "shop"},
        )
        goods = money(result.goods_price * quantity)
        list_subtotal = money(offer.list_price * quantity)
        discount = money(list_subtotal - goods)
        candidate = _LineCandidate(
            product=product,
            offer=offer,
            quantity=quantity,
            result=result,
            goods_price=goods,
            list_subtotal=list_subtotal,
            discount=discount,
            shipping=money(offer.shipping_fee),
        )
        previous = by_platform.get(offer.platform)
        if previous is None or (goods, offer.id) < (previous.goods_price, previous.offer.id):
            by_platform[offer.platform] = candidate
    return by_platform


def _collect_order_benefits(
    lines_data: list[_LineCandidate],
    ctx: SolverContext,
    rules: list[SubsidyRule],
) -> dict[str, Benefit]:
    benefits: dict[str, Benefit] = {}
    for line in lines_data:
        for benefit in line.offer.benefits:
            if benefit.scope in {"platform", "order"}:
                benefits.setdefault(benefit.id, benefit)
        rule_benefits, _ = build_rule_benefits(
            rules, line.offer, line.product.category, ctx
        )
        for benefit in rule_benefits:
            if benefit.scope in {"platform", "order"}:
                benefits.setdefault(benefit.id, benefit)
    return benefits


def _solve_order(
    platform: str,
    lines_data: list[_LineCandidate],
    ctx: SolverContext,
    rules: list[SubsidyRule],
) -> _OrderSolution:
    """Apply order-level benefits to one platform order."""

    platform_name = lines_data[0].offer.platform_name if lines_data else platform
    subtotal_before = money(sum(line.goods_price for line in lines_data))
    list_subtotal = money(sum(line.list_subtotal for line in lines_data))
    line_discount_total = money(sum(line.discount for line in lines_data))
    shipping = money(sum(line.shipping for line in lines_data))

    order_offer = Offer(
        id=f"ORDER-{platform}",
        product_id="CART",
        platform=platform,
        platform_name=platform_name,
        list_price=list_subtotal,
        shipping_fee=0.0,
        benefits=[],
    )
    order_benefits = _collect_order_benefits(lines_data, ctx, rules)
    optional = list(order_benefits.values())
    optional.sort(key=lambda benefit: (benefit.stage, benefit.id))

    order_ctx = ctx.model_copy(update={"quantity": 1})
    initial = _OrderState(
        subtotal=subtotal_before,
        net=0.0,
        used={},
        groups=set(),
        stage=0,
        trace=[],
    )
    best = initial
    best_key = _order_key(
        money(initial.subtotal + shipping),
        money(max(0.0, initial.subtotal - initial.net) + shipping),
        ctx.preference,
    )
    optimal = True

    def dfs(state: _OrderState) -> None:
        nonlocal best, best_key
        final = money(state.subtotal + shipping)
        net_price = money(max(0.0, state.subtotal - state.net) + shipping)
        key = _order_key(final, net_price, ctx.preference)
        if key < best_key:
            best_key = key
            best = state

        remaining = [
            b for b in optional if b.id not in state.used and b.stage >= state.stage
        ]
        if not remaining:
            return
        payment_bound = sum(
            benefit_upper_bound(b, order_offer, order_ctx, state.subtotal)
            for b in remaining
            if b.affects_payment
        )
        net_bound = sum(
            benefit_upper_bound(b, order_offer, order_ctx, state.subtotal)
            for b in remaining
            if b.is_net_benefit
        )
        optimistic_final = money(max(0.0, state.subtotal - payment_bound) + shipping)
        optimistic_net = money(
            max(0.0, state.subtotal - payment_bound - net_bound) + shipping
        )
        optimistic_key = _order_key(optimistic_final, optimistic_net, ctx.preference)
        if optimistic_key >= best_key:
            return

        for benefit in optional:
            if benefit.id in state.used or benefit.stage < state.stage:
                continue
            ok, _, _ = check_availability(
                benefit,
                order_offer,
                order_ctx,
                state.subtotal,
                state.used,
                state.groups,
            )
            if not ok:
                continue
            amount = compute_amount(benefit, order_offer, order_ctx, state.subtotal)
            if amount <= EPS:
                continue
            before = state.subtotal
            if benefit.is_net_benefit:
                new_subtotal = state.subtotal
                new_net = money(state.net + amount)
            else:
                new_subtotal = money(max(0.0, state.subtotal - amount))
                new_net = state.net
            new_state = _OrderState(
                subtotal=new_subtotal,
                net=new_net,
                used={**state.used, benefit.id: benefit},
                groups=set(state.groups),
                stage=benefit.stage,
                trace=[*state.trace, _make_step(benefit, amount, before, new_subtotal)],
            )
            if benefit.stack_group:
                new_state.groups.add(benefit.stack_group)
            dfs(new_state)

    dfs(initial)

    if len(optional) > 18:  # pragma: no cover - guard for pathological data
        optimal = False

    order_applied = best.trace
    rebate_value = money(sum(step.amount for step in order_applied if step.kind == "rebate"))
    order_discount_total = money(subtotal_before - best.subtotal)
    final_price = money(best.subtotal + shipping)
    net_price = money(max(0.0, best.subtotal - best.net) + shipping)

    rejected: list[RejectedBenefit] = []
    for benefit in optional:
        if benefit.id in best.used:
            continue
        ok, code, reason = check_availability(
            benefit,
            order_offer,
            order_ctx,
            best.subtotal,
            best.used,
            best.groups,
        )
        if not ok:
            rejected.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code=code,
                    reason=reason,
                )
            )
        else:
            rejected.append(
                RejectedBenefit(
                    benefit_id=benefit.id,
                    name=benefit.name,
                    reason_code="not_optimal",
                    reason="未采用：加入组合后不能进一步降低整单实付",
                )
            )

    cart_lines = [
        CartLine(
            product_id=line.product.id,
            title=line.product.title,
            category=line.product.category,
            quantity=line.quantity,
            unit_price=money(line.offer.list_price),
            list_subtotal=line.list_subtotal,
            line_discount=line.discount,
            line_final=line.goods_price,
            applied=line.result.applied,
        )
        for line in lines_data
    ]

    return _OrderSolution(
        platform=platform,
        platform_name=platform_name,
        lines=cart_lines,
        list_subtotal=list_subtotal,
        line_discount_total=line_discount_total,
        order_discount_total=order_discount_total,
        final_price=final_price,
        net_price=net_price,
        rebate_value=rebate_value,
        order_applied=order_applied,
        order_rejected=rejected,
        optimal=optimal,
    )


def _to_cart_order(solution: _OrderSolution) -> CartOrder:
    return CartOrder(
        platform=solution.platform,
        platform_name=solution.platform_name,
        lines=solution.lines,
        list_subtotal=solution.list_subtotal,
        line_discount_total=solution.line_discount_total,
        order_discount_total=solution.order_discount_total,
        final_price=solution.final_price,
        net_price=solution.net_price,
        rebate_value=solution.rebate_value,
        order_applied=solution.order_applied,
        order_rejected=solution.order_rejected,
    )


def _evaluate_assignment(
    assignment: dict[str, str],
    line_map: dict[tuple[str, str], _LineCandidate],
    item_order: list[str],
    ctx: SolverContext,
    rules: list[SubsidyRule],
) -> _Evaluation | None:
    grouped: dict[str, list[_LineCandidate]] = {}
    for product_id in item_order:
        platform = assignment[product_id]
        line = line_map.get((product_id, platform))
        if line is None:
            return None
        grouped.setdefault(platform, []).append(line)

    orders: list[_OrderSolution] = []
    for platform in sorted(grouped, key=_platform_rank):
        orders.append(_solve_order(platform, grouped[platform], ctx, rules))

    total_payment = money(sum(order.final_price for order in orders))
    total_net = money(sum(order.net_price for order in orders))
    return _Evaluation(
        orders=orders,
        total_payment=total_payment,
        total_net=total_net,
        optimal=all(order.optimal for order in orders),
        assignment=dict(assignment),
    )


def _best_all_on_one(
    platforms: list[str],
    line_map: dict[tuple[str, str], _LineCandidate],
    item_order: list[str],
    ctx: SolverContext,
    rules: list[SubsidyRule],
) -> _Evaluation | None:
    candidates: list[_Evaluation] = []
    for platform in platforms:
        if any((product_id, platform) not in line_map for product_id in item_order):
            continue
        evaluation = _evaluate_assignment(
            {product_id: platform for product_id in item_order},
            line_map,
            item_order,
            ctx,
            rules,
        )
        if evaluation:
            candidates.append(evaluation)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: _order_key(
            item.total_payment, item.total_net, ctx.preference
        ),
    )


def _assignment_key(evaluation: _Evaluation, preference: str) -> tuple[float, float]:
    return _order_key(evaluation.total_payment, evaluation.total_net, preference)


def optimize_cart(
    items: list[CartItemInput],
    products: dict[str, Product],
    ctx: SolverContext,
    rules: list[SubsidyRule] | None = None,
) -> CartResult:
    """Enumerate platform assignments (exact for small carts) and recommend a split."""

    rules = rules or []
    if not items:
        raise ValueError("cart is empty")

    merged: dict[str, int] = {}
    item_order: list[str] = []
    for item in items:
        if item.product_id not in products:
            raise ValueError(f"unknown product: {item.product_id}")
        if item.product_id not in merged:
            item_order.append(item.product_id)
            merged[item.product_id] = 0
        merged[item.product_id] += item.quantity

    line_map: dict[tuple[str, str], _LineCandidate] = {}
    options: dict[str, list[str]] = {}
    all_platforms: set[str] = set()
    for product_id in item_order:
        product = products[product_id]
        candidates = _line_candidates(product, merged[product_id], ctx, rules)
        if not candidates:
            raise ValueError(f"product has no offer: {product_id}")
        options[product_id] = list(candidates.keys())
        all_platforms.update(candidates.keys())
        for platform, candidate in candidates.items():
            line_map[(product_id, platform)] = candidate

    platforms = sorted(all_platforms, key=_platform_rank)
    combinations = math.prod(len(options[product_id]) for product_id in item_order)
    exact = len(item_order) <= MAX_EXACT_ITEMS and combinations <= MAX_EXACT_ASSIGNMENTS

    best: _Evaluation | None = None
    if exact:
        for choice in itertools.product(*(options[product_id] for product_id in item_order)):
            assignment = dict(zip(item_order, choice, strict=True))
            evaluation = _evaluate_assignment(assignment, line_map, item_order, ctx, rules)
            if evaluation is None:
                continue
            if best is None or _assignment_key(evaluation, ctx.preference) < _assignment_key(
                best, ctx.preference
            ):
                best = evaluation
    else:
        # Greedy start, then a few local-search passes.
        assignment = {
            product_id: min(
                options[product_id],
                key=lambda p: (
                    line_map[(product_id, p)].goods_price,
                    line_map[(product_id, p)].result.final_price,
                ),
            )
            for product_id in item_order
        }
        best = _evaluate_assignment(assignment, line_map, item_order, ctx, rules)
        for _ in range(3):
            improved = False
            assert best is not None
            for product_id in item_order:
                for platform in options[product_id]:
                    if best.assignment[product_id] == platform:
                        continue
                    trial = dict(best.assignment)
                    trial[product_id] = platform
                    evaluation = _evaluate_assignment(
                        trial, line_map, item_order, ctx, rules
                    )
                    if evaluation is None:
                        continue
                    if _assignment_key(evaluation, ctx.preference) < _assignment_key(
                        best, ctx.preference
                    ):
                        best = evaluation
                        improved = True
            if not improved:
                break

    if best is None:
        raise ValueError("no valid cart assignment")

    baseline = _best_all_on_one(platforms, line_map, item_order, ctx, rules)
    if baseline is None:
        baseline = best
        baseline_platform = "mixed"
    else:
        baseline_platform = baseline.orders[0].platform if len(baseline.orders) == 1 else "mixed"
    savings = money(baseline.total_payment - best.total_payment)

    split_platforms = "、".join(order.platform_name for order in best.orders)
    notes = [
        f"当前方案拆成 {len(best.orders)} 单，分别在 {split_platforms} 下单。",
        "同一平台商品合并为一单；平台券、满减按订单小计计算。",
        "店铺券/国补计入商品行价，平台券/满减/以旧换新/返利按整单计算。",
    ]
    if any(step.kind == "trade_in" for order in best.orders for step in order.order_applied):
        notes.append("以旧换新按整单抵扣一次，未在不同订单重复计算。")
    if not exact:
        notes.append("商品数量超出精确搜索规模，当前结果为启发式，不保证全局最优。")
    if savings <= 0:
        notes.append("当前组合下拆单没有比单平台更省。")

    return CartResult(
        region=ctx.region,
        preference=ctx.preference,
        orders=[_to_cart_order(order) for order in best.orders],
        total_payment=best.total_payment,
        total_net=best.total_net,
        baseline_payment=baseline.total_payment,
        baseline_platform=baseline_platform,
        savings_vs_baseline=max(0.0, savings),
        optimal=best.optimal and exact,
        assignment=best.assignment,
        notes=notes,
        engine_version=ENGINE_VERSION,
        generated_at=datetime.now(CN_TZ),
    )


def suggest_fillers(
    items: list[CartItemInput],
    products: dict[str, Product],
    ctx: SolverContext,
    rules: list[SubsidyRule] | None,
    cart: CartResult,
) -> list[FillerSuggestion]:
    """Find cheap add-ons that unlock an order-level threshold."""

    rules = rules or []
    merged: dict[str, int] = {}
    for item in items:
        merged[item.product_id] = merged.get(item.product_id, 0) + item.quantity
    in_cart = set(merged)

    line_map: dict[tuple[str, str], _LineCandidate] = {}
    for product_id, quantity in merged.items():
        product = products[product_id]
        for platform, candidate in _line_candidates(product, quantity, ctx, rules).items():
            line_map[(product_id, platform)] = candidate

    suggestions: list[FillerSuggestion] = []
    for order in cart.orders:
        product_ids = [
            line.product_id
            for line in order.lines
        ]
        lines_data = [
            line_map[(product_id, order.platform)] for product_id in product_ids
        ]
        order_benefits = _collect_order_benefits(lines_data, ctx, rules)
        base_current = money(sum(line.line_final for line in order.lines))

        for rejection in order.order_rejected:
            if rejection.reason_code != "threshold":
                continue
            benefit = order_benefits.get(rejection.benefit_id)
            if benefit is None:
                continue
            threshold_base = (
                order.list_subtotal if benefit.threshold_base == "list" else base_current
            )
            gap = money(benefit.threshold - threshold_base)
            if gap <= EPS:
                continue

            candidates: list[FillerCandidate] = []
            for product in products.values():
                if product.id in in_cart:
                    continue
                target_offer = next(
                    (offer for offer in product.offers if offer.platform == order.platform),
                    None,
                )
                if target_offer is None or target_offer.list_price <= 0:
                    continue
                if target_offer.list_price > gap + 300:
                    continue
                filler_candidates = _line_candidates(product, 1, ctx, rules)
                filler_line = filler_candidates.get(order.platform)
                if filler_line is None:
                    continue
                new_lines = [*lines_data, filler_line]
                new_order = _solve_order(order.platform, new_lines, ctx, rules)
                applied = any(
                    step.benefit_id == benefit.id for step in new_order.order_applied
                )
                if not applied:
                    continue
                net_increase = money(new_order.final_price - order.final_price)
                if net_increase <= 0:
                    reason = f"加购后本单实付反而减少 ¥{abs(net_increase):,.0f}"
                else:
                    reason = f"多花 ¥{net_increase:,.0f} 得到该商品"
                candidates.append(
                    FillerCandidate(
                        product_id=product.id,
                        title=product.title,
                        image=product.image,
                        price=money(target_offer.list_price),
                        new_total=new_order.final_price,
                        net_increase=net_increase,
                        reason=reason,
                    )
                )
            candidates.sort(key=lambda item: (item.net_increase, item.product_id))
            if candidates:
                suggestions.append(
                    FillerSuggestion(
                        platform=order.platform,
                        platform_name=order.platform_name,
                        benefit_id=benefit.id,
                        benefit_name=benefit.name,
                        gap=gap,
                        candidates=candidates[:3],
                    )
                )
    return suggestions
