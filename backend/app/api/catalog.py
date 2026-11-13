"""Catalogue, home feed, configuration and rule endpoints."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.adapters import adapter_status
from app.api.helpers import DATA_NOTE, build_context, product_card
from app.config import ENGINE_VERSION, MEMBERSHIPS, PLATFORMS, REGIONS
from app.db.base import get_db
from app.db.repository import get_product, load_products, load_rules
from app.engine.stacker import CN_TZ
from app.schemas.api import (
    ConfigResponse,
    HomeResponse,
    OfferBrief,
    PlatformInfo,
    ProductDetailResponse,
    ProductListResponse,
    RuleListResponse,
)

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/home", response_model=HomeResponse)
def home(db: Session = Depends(get_db)) -> HomeResponse:
    products = load_products(db)
    rules = load_rules(db)
    ctx = build_context(region="浙江", now=date.fromisoformat("2026-11-13"))
    featured = [product for product in products.values() if product.featured]
    cards = [product_card(product, ctx, rules) for product in featured]
    return HomeResponse(
        products=cards,
        regions=REGIONS,
        memberships=MEMBERSHIPS,
        default_region="浙江",
        generated_at=datetime.now(CN_TZ),
        data_note=DATA_NOTE,
    )


@router.get("/products", response_model=ProductListResponse)
def list_products(
    q: str = Query(default="", max_length=80),
    category: str = Query(default=""),
    featured: bool | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    products = load_products(db)
    rules = load_rules(db)
    needle = q.strip().lower()
    selected = []
    for product in products.values():
        if category and product.category != category:
            continue
        if featured is not None and product.featured != featured:
            continue
        if needle:
            haystack = " ".join(
                [product.title, product.brand, product.model, product.category, *product.tags]
            ).lower()
            if needle not in haystack:
                continue
        selected.append(product)
    selected.sort(key=lambda item: (not item.featured, item.id))
    ctx = build_context(region="浙江")
    cards = [product_card(product, ctx, rules) for product in selected[:limit]]
    return ProductListResponse(products=cards, total=len(cards))


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
def product_detail(product_id: str, db: Session = Depends(get_db)) -> ProductDetailResponse:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return ProductDetailResponse(
        product=product,
        offers=[
            OfferBrief(
                offer_id=offer.id,
                platform=offer.platform,
                platform_name=offer.platform_name,
                shop_name=offer.shop_name,
                list_price=offer.list_price,
                shipping_fee=offer.shipping_fee,
                source=offer.source,
            )
            for offer in product.offers
        ],
    )


@router.get("/products/{product_id}/offers", response_model=list[OfferBrief])
def product_offers(product_id: str, db: Session = Depends(get_db)) -> list[OfferBrief]:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return [
        OfferBrief(
            offer_id=offer.id,
            platform=offer.platform,
            platform_name=offer.platform_name,
            shop_name=offer.shop_name,
            list_price=offer.list_price,
            shipping_fee=offer.shipping_fee,
            source=offer.source,
        )
        for offer in product.offers
    ]


@router.get("/config", response_model=ConfigResponse)
def config(db: Session = Depends(get_db)) -> ConfigResponse:
    products = load_products(db)
    return ConfigResponse(
        platforms=[PlatformInfo(**platform) for platform in PLATFORMS],
        regions=REGIONS,
        memberships=MEMBERSHIPS,
        categories=sorted({product.category for product in products.values()}),
        engine_version=ENGINE_VERSION,
        data_note=DATA_NOTE,
    )


@router.get("/rules", response_model=RuleListResponse)
def rules(
    region: str = Query(default=""),
    category: str = Query(default=""),
    db: Session = Depends(get_db),
) -> RuleListResponse:
    all_rules = load_rules(db)
    if region:
        all_rules = [
            rule for rule in all_rules if not rule.regions or region in rule.regions or "全国" in rule.regions
        ]
    if category:
        all_rules = [
            rule for rule in all_rules if not rule.categories or category in rule.categories
        ]
    return RuleListResponse(
        rules=all_rules,
        count=len(all_rules),
        notes=[
            "示例规则，可通过数据库/JSON 更新，无需改动求解代码。",
            "实际补贴以当地最新政策、平台页面和实名资格为准。",
        ],
    )


@router.get("/adapters")
def adapters(db: Session = Depends(get_db)) -> dict:
    products = load_products(db)
    return {
        "adapters": adapter_status(products),
        "note": "演示环境仅启用内置模拟数据；联盟适配器需要官方账号与授权。",
    }
