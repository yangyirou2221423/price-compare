"""Core domain models for the price-strategy engine.

The engine is intentionally framework-free: FastAPI, SQLAlchemy and the
frontend only translate to/from these models.  Money is rounded to cents at
every mutation so results are reproducible and easy to compare in tests.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BenefitKind = Literal[
    "store_coupon",
    "platform_coupon",
    "category_coupon",
    "full_reduction",
    "member",
    "platform_subsidy",
    "national_subsidy",
    "trade_in",
    "payment_discount",
    "rebate",
    "gift",
]

BenefitScope = Literal["item", "shop", "platform", "category", "order"]
ValueType = Literal["fixed", "percent", "per_threshold", "price_override"]
ThresholdBase = Literal["list", "current"]
Preference = Literal["payment", "net"]


def money(value: float) -> float:
    """Round a monetary value to cents without banker's-rounding surprises."""

    return round(float(value) + 1e-7, 2)


class Requirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memberships: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    trade_in: bool = False
    first_order: bool = False
    min_quantity: int = 1


class Benefit(BaseModel):
    """A single discount, subsidy or cash-back item attached to an offer."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: BenefitKind
    scope: BenefitScope = "item"
    value_type: ValueType = "fixed"
    value: float = 0.0
    threshold: float = 0.0
    step: float | None = None
    max_discount: float | None = None
    threshold_base: ThresholdBase = "list"
    price_cap: float | None = None
    price_cap_base: ThresholdBase = "list"
    stage: int = 1
    stack_group: str | None = None
    exclusive_with: list[str] = Field(default_factory=list)
    requires: Requirements = Field(default_factory=Requirements)
    valid_from: date | None = None
    valid_to: date | None = None
    description: str = ""
    source: str = "mock"
    rule_id: str | None = None

    @field_validator("stage")
    @classmethod
    def _stage_in_range(cls, value: int) -> int:
        if not 0 <= value <= 12:
            raise ValueError("stage must be between 0 and 12")
        return value

    @field_validator("value")
    @classmethod
    def _value_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("benefit value must be non-negative")
        return value

    @field_validator("value_type")
    @classmethod
    def _known_value_type(cls, value: str) -> str:
        return value

    @property
    def affects_payment(self) -> bool:
        """Rebates and gifts improve net value but do not lower the cash paid."""

        return self.kind not in {"rebate", "gift"}

    @property
    def is_net_benefit(self) -> bool:
        return not self.affects_payment


class Offer(BaseModel):
    """A platform-specific offer for one canonical product."""

    model_config = ConfigDict(extra="forbid")

    id: str
    product_id: str
    platform: str
    platform_name: str
    shop_name: str = ""
    list_price: float
    shipping_fee: float = 0.0
    url: str = ""
    source: str = "mock"
    updated_at: datetime | None = None
    benefits: list[Benefit] = Field(default_factory=list)

    @field_validator("list_price")
    @classmethod
    def _price_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("list_price must be non-negative")
        return value


class Product(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    brand: str = ""
    model: str = ""
    category: str
    specs: str = ""
    image: str = ""
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    featured: bool = False
    offers: list[Offer] = Field(default_factory=list)

    def offer_for(self, platform: str) -> Offer | None:
        return next((offer for offer in self.offers if offer.platform == platform), None)


class TradeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_name: str = "旧设备"
    estimate: float = 0.0

    @field_validator("estimate")
    @classmethod
    def _estimate_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("trade-in estimate must be non-negative")
        return value


class SolverContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str = "全国"
    memberships: list[str] = Field(default_factory=list)
    trade_in: TradeIn | None = None
    preference: Preference = "payment"
    now: date = Field(default_factory=date.today)
    quantity: int = 1
    first_order: bool = True

    @field_validator("quantity")
    @classmethod
    def _quantity_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("quantity must be at least 1")
        return value


class SubsidyRule(BaseModel):
    """A policy / platform subsidy rule that becomes a Benefit at request time."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    type: Literal["national_subsidy", "province_subsidy", "trade_in", "platform_subsidy"]
    regions: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    price_cap: float | None = None
    price_cap_base: ThresholdBase = "list"
    percent: float | None = None
    flat_amount: float | None = None
    max_discount: float | None = None
    requires_trade_in: bool = False
    requires_membership: str | None = None
    stage: int = 6
    stack_group: str | None = None
    exclusive_with: list[str] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    description: str = ""
    source: str = "示例规则"
    version: str = "2026.1"
    priority: int = 0


class AppliedBenefit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benefit_id: str
    name: str
    kind: BenefitKind
    stage: int
    amount: float
    price_before: float
    price_after: float
    is_net_benefit: bool = False
    description: str = ""
    rule_id: str | None = None


class RejectedBenefit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benefit_id: str
    name: str
    reason_code: str
    reason: str


class PlatformResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer_id: str
    platform: str
    platform_name: str
    shop_name: str = ""
    list_price: float
    shipping_fee: float = 0.0
    base_price: float
    goods_price: float
    final_price: float
    net_price: float
    discount_total: float
    promo_savings: float
    trade_in_value: float = 0.0
    rebate_value: float = 0.0
    gift_value: float = 0.0
    savings_pct: float = 0.0
    applied: list[AppliedBenefit] = Field(default_factory=list)
    rejected: list[RejectedBenefit] = Field(default_factory=list)
    optimal: bool = True
    note: str = ""


class PlatformSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    platform_name: str
    offer_id: str
    final_price: float
    net_price: float
    discount_total: float
    qualified_subsidies: list[str] = Field(default_factory=list)


class StrategyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_title: str
    product_image: str = ""
    product_category: str = ""
    region: str
    preference: Preference
    best_platform: str
    best_offer_id: str
    best: PlatformResult
    results: list[PlatformResult]
    savings_abs: float
    savings_pct: float
    summary: str
    assumptions: list[str] = Field(default_factory=list)
    engine_version: str
    data_source: str = "mock"
    generated_at: datetime
    optimal: bool = True


class PricePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    price: float


class PriceHistoryAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    platform: str
    platform_name: str
    days: int
    points: list[PricePoint]
    current_price: float
    median_price: float
    min_price: float
    max_price: float
    p25: float
    p75: float
    percentile: float
    is_low: bool
    lowest_30d: float
    lowest_90d: float
    trend_7d: float
    trend_7d_pct: float
    fake_drop: bool
    verdict: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Cart models
# ---------------------------------------------------------------------------


class CartItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def _quantity_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("quantity must be at least 1")
        return value


class CartLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    title: str
    category: str
    quantity: int
    unit_price: float
    list_subtotal: float
    line_discount: float
    line_final: float
    applied: list[AppliedBenefit] = Field(default_factory=list)


class CartOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    platform_name: str
    lines: list[CartLine]
    list_subtotal: float
    line_discount_total: float
    order_discount_total: float
    final_price: float
    net_price: float
    rebate_value: float = 0.0
    order_applied: list[AppliedBenefit] = Field(default_factory=list)
    order_rejected: list[RejectedBenefit] = Field(default_factory=list)


class CartResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str
    preference: Preference
    orders: list[CartOrder]
    total_payment: float
    total_net: float
    baseline_payment: float
    baseline_platform: str
    savings_vs_baseline: float
    optimal: bool = True
    assignment: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    engine_version: str
    generated_at: datetime


class FillerCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: str
    title: str
    image: str = ""
    price: float
    new_total: float
    net_increase: float
    reason: str


class FillerSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    platform_name: str
    benefit_id: str
    benefit_name: str
    gap: float
    candidates: list[FillerCandidate] = Field(default_factory=list)
    warning: str = "为凑单购买不需要的商品，可能反而多花钱。"
