"""Comparison, strategy, cart optimisation and subsidy-calculator endpoints."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.helpers import PLATFORM_NAME
from app.config import ENGINE_VERSION
from app.db.base import get_db
from app.db.models import StrategyRunModel
from app.db.repository import get_product, load_products, load_rules
from app.engine.cart_solver import optimize_cart, suggest_fillers
from app.engine.model import Offer, SolverContext, TradeIn
from app.engine.rules import build_rule_benefits, compute_amount
from app.engine.stacker import CN_TZ, compare_product
from app.schemas.api import (
    CartRequest,
    CartResponse,
    CompareRequest,
    SubsidyCheckItem,
    SubsidyCheckRequest,
    SubsidyCheckResponse,
)

router = APIRouter(prefix="/api", tags=["strategy"])


def _to_trade_in(request) -> TradeIn | None:
    if not request.trade_in:
        return None
    return TradeIn(
        device_name=request.trade_in.device_name,
        estimate=request.trade_in.estimate,
    )


def _context(request: CompareRequest | CartRequest) -> SolverContext:
    return SolverContext(
        region=request.region,
        memberships=request.memberships,
        trade_in=_to_trade_in(request),
        preference=request.preference,
        now=request.now or date.fromisoformat("2026-11-13"),
    )


@router.post("/compare")
def compare(request: CompareRequest, db: Session = Depends(get_db)):
    product = get_product(db, request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    rules = load_rules(db)
    return compare_product(product, _context(request), rules)


@router.post("/strategy")
def strategy(request: CompareRequest, db: Session = Depends(get_db)):
    product = get_product(db, request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    rules = load_rules(db)
    result = compare_product(product, _context(request), rules)
    run = StrategyRunModel(
        product_id=product.id,
        request_json=request.model_dump(mode="json"),
        result_json=result.model_dump(mode="json"),
        engine_version=ENGINE_VERSION,
        created_at=datetime.now(CN_TZ).replace(tzinfo=None),
    )
    db.add(run)
    db.commit()
    return result


@router.post("/cart/optimize", response_model=CartResponse)
def cart_optimize(request: CartRequest, db: Session = Depends(get_db)) -> CartResponse:
    products = load_products(db)
    rules = load_rules(db)
    ctx = _context(request)
    try:
        result = optimize_cart(request.items, products, ctx, rules)
        fillers = (
            suggest_fillers(request.items, products, ctx, rules, result)
            if request.include_fillers
            else []
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CartResponse(cart=result, fillers=fillers)


@router.post("/subsidy/check", response_model=SubsidyCheckResponse)
def subsidy_check(
    request: SubsidyCheckRequest, db: Session = Depends(get_db)
) -> SubsidyCheckResponse:
    rules = load_rules(db)
    platform_name = PLATFORM_NAME.get(request.platform, request.platform)
    synthetic_offer = Offer(
        id="SUBSIDY-CALC",
        product_id="SUBSIDY-CALC",
        platform=request.platform,
        platform_name=platform_name,
        list_price=request.price,
        shipping_fee=0.0,
        benefits=[],
    )
    ctx = SolverContext(
        region=request.region,
        memberships=request.memberships,
        trade_in=_to_trade_in(request),
        now=request.now or date.fromisoformat("2026-11-13"),
    )
    benefits, rejections = build_rule_benefits(
        rules, synthetic_offer, request.category, ctx
    )
    benefit_by_rule = {benefit.rule_id: benefit for benefit in benefits}
    rejection_by_rule = {
        rejection.benefit_id.removeprefix("rule:"): rejection for rejection in rejections
    }

    items: list[SubsidyCheckItem] = []
    total = 0.0
    for rule in rules:
        if rule.categories and request.category not in rule.categories:
            continue
        benefit = benefit_by_rule.get(rule.id)
        rejection = rejection_by_rule.get(rule.id)
        if benefit is not None:
            amount = compute_amount(benefit, synthetic_offer, ctx, request.price)
            total += amount
            reason = (
                f"符合条件，预计可减 ¥{amount:,.0f}"
                if amount > 0
                else "符合条件，实际金额以旧机估价或平台结算为准"
            )
            eligible = True
        else:
            amount = 0.0
            reason = rejection.reason if rejection else "未匹配到补贴资格"
            eligible = False
        effective = (
            f"{rule.effective_from.isoformat()} 至 {rule.effective_to.isoformat()}"
            if rule.effective_from and rule.effective_to
            else "长期有效（示例）"
        )
        items.append(
            SubsidyCheckItem(
                rule_id=rule.id,
                name=rule.name,
                eligible=eligible,
                amount=amount,
                reason=reason,
                description=rule.description,
                source=rule.source,
                version=rule.version,
                effective=effective,
            )
        )

    return SubsidyCheckResponse(
        category=request.category,
        price=request.price,
        platform=request.platform,
        platform_name=platform_name,
        region=request.region,
        total_estimated=round(total, 2),
        items=items,
        notes=[
            "金额按示例规则与当前商品价格估算，未考虑地区名额、实名限制和平台结算差异。",
            "规则带生效期和版本号，实际以当地最新政策和平台页面为准。",
        ],
    )
