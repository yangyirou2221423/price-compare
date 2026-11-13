"""HTTP request/response models."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.engine.model import (
    CartItemInput,
    CartResult,
    FillerSuggestion,
    Preference,
    PriceHistoryAnalysis,
    Product,
    SubsidyRule,
)


class TradeInInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_name: str = "旧设备"
    estimate: float = 0.0


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    region: str = "全国"
    memberships: list[str] = Field(default_factory=list)
    trade_in: TradeInInput | None = None
    preference: Preference = "payment"
    now: date | None = None


class CartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CartItemInput]
    region: str = "浙江"
    memberships: list[str] = Field(default_factory=list)
    trade_in: TradeInInput | None = None
    preference: Preference = "payment"
    include_fillers: bool = True
    now: date | None = None


class CartResponse(BaseModel):
    cart: CartResult
    fillers: list[FillerSuggestion] = Field(default_factory=list)


class ProductCard(BaseModel):
    id: str
    title: str
    brand: str
    category: str
    specs: str
    image: str
    tags: list[str]
    featured: bool
    offer_count: int
    best_platform: str
    best_platform_name: str
    best_price: float
    net_price: float
    list_price: float
    savings: float
    savings_pct: float
    summary: str
    data_source: str


class ProductListResponse(BaseModel):
    products: list[ProductCard]
    total: int


class OfferBrief(BaseModel):
    offer_id: str
    platform: str
    platform_name: str
    shop_name: str
    list_price: float
    shipping_fee: float
    source: str


class ProductDetailResponse(BaseModel):
    product: Product
    offers: list[OfferBrief]


class HomeResponse(BaseModel):
    products: list[ProductCard]
    regions: list[str]
    memberships: list[str]
    default_region: str
    generated_at: datetime
    data_note: str


class HistoryResponse(BaseModel):
    product_id: str
    product_title: str
    days: int
    series: list[PriceHistoryAnalysis]
    data_note: str


class SubsidyCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    price: float = Field(gt=0)
    platform: str = "taobao"
    region: str = "全国"
    memberships: list[str] = Field(default_factory=list)
    trade_in: TradeInInput | None = None
    now: date | None = None


class SubsidyCheckItem(BaseModel):
    rule_id: str
    name: str
    eligible: bool
    amount: float
    reason: str
    description: str
    source: str
    version: str
    effective: str


class SubsidyCheckResponse(BaseModel):
    category: str
    price: float
    platform: str
    platform_name: str
    region: str
    total_estimated: float
    items: list[SubsidyCheckItem]
    notes: list[str]


class RuleListResponse(BaseModel):
    rules: list[SubsidyRule]
    count: int
    notes: list[str]


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    platform: str
    price: float = Field(gt=0)
    link: str = ""
    note: str = ""


class SubmissionResponse(BaseModel):
    id: int
    message: str
    created_at: datetime


class SubmissionListResponse(BaseModel):
    submissions: list[SubmissionResponse]
    total: int


class PlatformInfo(BaseModel):
    id: str
    name: str
    short: str


class ConfigResponse(BaseModel):
    platforms: list[PlatformInfo]
    regions: list[str]
    memberships: list[str]
    categories: list[str]
    engine_version: str
    data_note: str
