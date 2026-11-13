"""ORM models for catalogue, policy rules, price history and submissions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(80), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    category: Mapped[str] = mapped_column(String(40), index=True)
    specs: Mapped[str] = mapped_column(String(200), default="")
    image: Mapped[str] = mapped_column(String(200), default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    offers: Mapped[list[OfferModel]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="OfferModel.id"
    )


class OfferModel(Base):
    __tablename__ = "offers"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20), index=True)
    platform_name: Mapped[str] = mapped_column(String(40))
    shop_name: Mapped[str] = mapped_column(String(120), default="")
    list_price: Mapped[float] = mapped_column(Float)
    shipping_fee: Mapped[float] = mapped_column(Float, default=0.0)
    url: Mapped[str] = mapped_column(String(300), default="")
    source: Mapped[str] = mapped_column(String(40), default="mock")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    product: Mapped[ProductModel] = relationship(back_populates="offers")
    benefits: Mapped[list[BenefitModel]] = relationship(
        back_populates="offer", cascade="all, delete-orphan", order_by="BenefitModel.pk"
    )


class BenefitModel(Base):
    __tablename__ = "benefits"
    __table_args__ = (UniqueConstraint("offer_id", "benefit_id", name="uq_offer_benefit"),)

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[str] = mapped_column(ForeignKey("offers.id"), index=True)
    benefit_id: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(40))
    scope: Mapped[str] = mapped_column(String(20), default="item")
    value_type: Mapped[str] = mapped_column(String(30), default="fixed")
    value: Mapped[float] = mapped_column(Float, default=0.0)
    threshold: Mapped[float] = mapped_column(Float, default=0.0)
    step: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_discount: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_base: Mapped[str] = mapped_column(String(20), default="list")
    price_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_cap_base: Mapped[str] = mapped_column(String(20), default="list")
    stage: Mapped[int] = mapped_column(Integer, default=1)
    stack_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exclusive_with: Mapped[list[str]] = mapped_column(JSON, default=list)
    requires: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(80), default="mock")
    rule_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    offer: Mapped[OfferModel] = relationship(back_populates="benefits")


class SubsidyRuleModel(Base):
    __tablename__ = "subsidy_rules"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(40))
    regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    platforms: Mapped[list[str]] = mapped_column(JSON, default=list)
    price_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_cap_base: Mapped[str] = mapped_column(String(20), default="list")
    percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    flat_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_discount: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_trade_in: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_membership: Mapped[str | None] = mapped_column(String(60), nullable=True)
    stage: Mapped[int] = mapped_column(Integer, default=6)
    stack_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exclusive_with: Mapped[list[str]] = mapped_column(JSON, default=list)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(80), default="示例政策")
    version: Mapped[str] = mapped_column(String(30), default="2026.1")
    priority: Mapped[int] = mapped_column(Integer, default=0)


class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(20), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    price: Mapped[float] = mapped_column(Float)


class SubmissionModel(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    price: Mapped[float] = mapped_column(Float)
    link: Mapped[str] = mapped_column(String(500), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class StrategyRunModel(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), index=True)
    request_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    engine_version: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
