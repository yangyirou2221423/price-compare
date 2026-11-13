"""Translate SQLAlchemy rows into engine domain models."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    BenefitModel,
    OfferModel,
    PriceHistoryModel,
    ProductModel,
    SubsidyRuleModel,
)
from app.engine.model import (
    Benefit,
    Offer,
    PricePoint,
    Product,
    Requirements,
    SubsidyRule,
)

PLATFORM_RANK = {"jd": 0, "taobao": 1, "pdd": 2, "douyin": 3}


def benefit_to_domain(row: BenefitModel) -> Benefit:
    return Benefit(
        id=row.benefit_id,
        name=row.name,
        kind=row.kind,
        scope=row.scope,
        value_type=row.value_type,
        value=row.value,
        threshold=row.threshold,
        step=row.step,
        max_discount=row.max_discount,
        threshold_base=row.threshold_base,
        price_cap=row.price_cap,
        price_cap_base=row.price_cap_base,
        stage=row.stage,
        stack_group=row.stack_group,
        exclusive_with=row.exclusive_with or [],
        requires=Requirements(**(row.requires or {})),
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        description=row.description,
        source=row.source,
        rule_id=row.rule_id,
    )


def offer_to_domain(row: OfferModel) -> Offer:
    return Offer(
        id=row.id,
        product_id=row.product_id,
        platform=row.platform,
        platform_name=row.platform_name,
        shop_name=row.shop_name,
        list_price=row.list_price,
        shipping_fee=row.shipping_fee,
        url=row.url,
        source=row.source,
        updated_at=row.updated_at,
        benefits=[benefit_to_domain(benefit) for benefit in row.benefits],
    )


def product_to_domain(row: ProductModel) -> Product:
    return Product(
        id=row.id,
        title=row.title,
        brand=row.brand,
        model=row.model,
        category=row.category,
        specs=row.specs,
        image=row.image,
        tags=row.tags or [],
        description=row.description,
        featured=row.featured,
        offers=sorted(
            (offer_to_domain(offer) for offer in row.offers),
            key=lambda offer: (PLATFORM_RANK.get(offer.platform, 9), offer.id),
        ),
    )


def rule_to_domain(row: SubsidyRuleModel) -> SubsidyRule:
    return SubsidyRule(
        id=row.id,
        name=row.name,
        type=row.type,
        regions=row.regions or [],
        categories=row.categories or [],
        platforms=row.platforms or [],
        price_cap=row.price_cap,
        price_cap_base=row.price_cap_base,
        percent=row.percent,
        flat_amount=row.flat_amount,
        max_discount=row.max_discount,
        requires_trade_in=row.requires_trade_in,
        requires_membership=row.requires_membership,
        stage=row.stage,
        stack_group=row.stack_group,
        exclusive_with=row.exclusive_with or [],
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        description=row.description,
        source=row.source,
        version=row.version,
        priority=row.priority,
    )


def load_products(db: Session) -> dict[str, Product]:
    statement = select(ProductModel).options(
        selectinload(ProductModel.offers).selectinload(OfferModel.benefits)
    )
    rows = db.scalars(statement).all()
    return {row.id: product_to_domain(row) for row in rows}


def get_product(db: Session, product_id: str) -> Product | None:
    statement = (
        select(ProductModel)
        .where(ProductModel.id == product_id)
        .options(selectinload(ProductModel.offers).selectinload(OfferModel.benefits))
    )
    row = db.scalar(statement)
    return product_to_domain(row) if row else None


def load_rules(db: Session) -> list[SubsidyRule]:
    statement = select(SubsidyRuleModel).order_by(
        SubsidyRuleModel.priority, SubsidyRuleModel.id
    )
    return [rule_to_domain(row) for row in db.scalars(statement).all()]


def load_history_points(
    db: Session, product_id: str, platform: str, days: int = 90
) -> list[PricePoint]:
    statement = (
        select(PriceHistoryModel)
        .where(
            PriceHistoryModel.product_id == product_id,
            PriceHistoryModel.platform == platform,
        )
        .order_by(PriceHistoryModel.date.desc())
        .limit(days)
    )
    rows = db.scalars(statement).all()
    return [
        PricePoint(date=row.date, price=row.price)
        for row in reversed(rows)
    ]
