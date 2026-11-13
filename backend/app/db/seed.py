"""Create tables and load the deterministic demo catalogue into SQLite."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import DEMO_NOW, SEED_PATH
from app.db.base import Base, SessionLocal, engine
from app.db.models import (
    BenefitModel,
    OfferModel,
    PriceHistoryModel,
    ProductModel,
    SubsidyRuleModel,
)
from app.engine.history import generate_price_series
from app.engine.model import Product, SubsidyRule

logger = logging.getLogger(__name__)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def _current_price(product: Product, offer) -> float:
    overrides = [
        benefit.value
        for benefit in offer.benefits
        if benefit.value_type == "price_override" and benefit.value < offer.list_price
    ]
    return min(overrides) if overrides else offer.list_price


def seed_if_empty(db: Session) -> bool:
    count = db.scalar(select(func.count(ProductModel.id))) or 0
    if count:
        return False

    if not SEED_PATH.exists():
        raise FileNotFoundError(
            f"seed catalogue not found: {SEED_PATH}; run data/build_seed.py first"
        )
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    products = [Product.model_validate(item) for item in raw["products"]]
    rules = [SubsidyRule.model_validate(item) for item in raw["subsidy_rules"]]
    history_meta = raw.get("price_history", {})
    end_date = date.fromisoformat(DEMO_NOW)
    updated_at = datetime(2026, 11, 13, 12, 0)

    for product in products:
        product_row = ProductModel(
            id=product.id,
            title=product.title,
            brand=product.brand,
            model=product.model,
            category=product.category,
            specs=product.specs,
            image=product.image,
            tags=product.tags,
            description=product.description,
            featured=product.featured,
        )
        for offer in product.offers:
            offer_row = OfferModel(
                id=offer.id,
                product_id=product.id,
                platform=offer.platform,
                platform_name=offer.platform_name,
                shop_name=offer.shop_name,
                list_price=offer.list_price,
                shipping_fee=offer.shipping_fee,
                url=offer.url,
                source=offer.source,
                updated_at=updated_at,
            )
            for benefit in offer.benefits:
                offer_row.benefits.append(
                    BenefitModel(
                        benefit_id=benefit.id,
                        name=benefit.name,
                        kind=benefit.kind,
                        scope=benefit.scope,
                        value_type=benefit.value_type,
                        value=benefit.value,
                        threshold=benefit.threshold,
                        step=benefit.step,
                        max_discount=benefit.max_discount,
                        threshold_base=benefit.threshold_base,
                        price_cap=benefit.price_cap,
                        price_cap_base=benefit.price_cap_base,
                        stage=benefit.stage,
                        stack_group=benefit.stack_group,
                        exclusive_with=benefit.exclusive_with,
                        requires=benefit.requires.model_dump(),
                        valid_from=benefit.valid_from,
                        valid_to=benefit.valid_to,
                        description=benefit.description,
                        source=benefit.source,
                        rule_id=benefit.rule_id,
                    )
                )
            product_row.offers.append(offer_row)

            meta = history_meta.get(offer.id, {})
            fake_drop = bool(meta.get("fake_drop", False))
            # A fake-drop history needs a higher "before promotion" baseline,
            # otherwise the current price is not low enough versus the median.
            history_base = offer.list_price * 1.12 if fake_drop else offer.list_price
            points = generate_price_series(
                base_price=history_base,
                days=90,
                end_date=end_date,
                seed=int(meta.get("seed", 7)),
                fake_drop=fake_drop,
            )
            current = _current_price(product, offer)
            if points:
                points[-1] = points[-1].model_copy(update={"price": current})
            for point in points:
                db.add(
                    PriceHistoryModel(
                        product_id=product.id,
                        platform=offer.platform,
                        date=point.date,
                        price=point.price,
                    )
                )
        db.add(product_row)

    for rule in rules:
        db.add(
            SubsidyRuleModel(
                id=rule.id,
                name=rule.name,
                type=rule.type,
                regions=rule.regions,
                categories=rule.categories,
                platforms=rule.platforms,
                price_cap=rule.price_cap,
                price_cap_base=rule.price_cap_base,
                percent=rule.percent,
                flat_amount=rule.flat_amount,
                max_discount=rule.max_discount,
                requires_trade_in=rule.requires_trade_in,
                requires_membership=rule.requires_membership,
                stage=rule.stage,
                stack_group=rule.stack_group,
                exclusive_with=rule.exclusive_with,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                description=rule.description,
                source=rule.source,
                version=rule.version,
                priority=rule.priority,
            )
        )
    db.commit()
    logger.info("seeded %s products, %s rules", len(products), len(rules))
    return True


def bootstrap() -> None:
    init_db()
    with SessionLocal() as db:
        seed_if_empty(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bootstrap()
    print("database ready")
