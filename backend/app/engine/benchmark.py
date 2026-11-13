"""Small reproducible benchmark for the strategy engine.

Run from backend/:  python -m app.engine.benchmark

It measures the single-offer branch-and-bound solver and the cart split
optimiser on synthetic instances.  The numbers are illustrative; run on the
same machine as the competition demo for a fair comparison.
"""

from __future__ import annotations

import json
import random
import statistics
import time
from datetime import date

from app.engine.cart_solver import optimize_cart
from app.engine.model import (
    Benefit,
    CartItemInput,
    Offer,
    Product,
    Requirements,
    SolverContext,
)
from app.engine.stacker import solve_offer

NOW = date(2026, 11, 13)
PLATFORMS = [("jd", "京东"), ("taobao", "淘宝"), ("pdd", "拼多多"), ("douyin", "抖音")]


def random_benefit(rng: random.Random, index: int) -> Benefit:
    kind = rng.choice(
        ["store_coupon", "platform_coupon", "full_reduction", "member", "rebate", "gift"]
    )
    value_type = rng.choice(["fixed", "percent"])
    if kind in {"rebate", "gift"}:
        value = rng.randint(1, 8) if value_type == "percent" else rng.randint(20, 120)
        stage = 9 if kind == "rebate" else 10
    else:
        value = rng.randint(30, 300) if value_type == "fixed" else rng.randint(3, 18)
        stage = rng.randint(1, 4)
    return Benefit(
        id=f"B{index}",
        name=f"bench-{index}",
        kind=kind,
        scope="platform" if stage >= 3 else "item",
        value_type=value_type,
        value=value,
        threshold=rng.choice([0, 0, 0, 500, 1500, 3000]),
        max_discount=rng.choice([None, 100, 300]) if value_type == "percent" else None,
        stage=stage,
        stack_group=rng.choice([None, None, "g1", "g2"]),
        requires=Requirements(),
    )


def make_offer(rng: random.Random, product_id: str, platform: str, name: str, count: int) -> Offer:
    benefits = [random_benefit(rng, index) for index in range(count)]
    return Offer(
        id=f"{product_id}-{platform}",
        product_id=product_id,
        platform=platform,
        platform_name=name,
        list_price=rng.randint(800, 8000),
        benefits=benefits,
    )


def solve_many(count: int, cases: int, seed: int) -> dict:
    rng = random.Random(seed)
    timings: list[float] = []
    for case in range(cases):
        platform, name = rng.choice(PLATFORMS)
        offer = make_offer(rng, f"P{case}", platform, name, count)
        product = Product(id=offer.product_id, title="bench", category="测试", offers=[offer])
        context = SolverContext(now=NOW, region="浙江")
        start = time.perf_counter()
        result = solve_offer(offer, product, context)
        timings.append((time.perf_counter() - start) * 1000)
        assert result.final_price >= 0
    timings.sort()
    return {
        "benefits": count,
        "cases": cases,
        "avg_ms": round(statistics.mean(timings), 3),
        "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 3),
        "max_ms": round(max(timings), 3),
    }


def cart_products(rng: random.Random, count: int) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for index in range(count):
        product_id = f"C{index}"
        offers = []
        for platform, name in PLATFORMS:
            benefits = [
                Benefit(
                    id=f"{platform.upper()}-FULL",
                    name="bench full reduction",
                    kind="full_reduction",
                    scope="platform",
                    value_type="fixed",
                    value=300,
                    threshold=3000,
                    stage=3,
                    requires=Requirements(),
                )
            ]
            if rng.random() < 0.6:
                benefits.append(
                    Benefit(
                        id=f"{product_id}-{platform}-STORE",
                        name="bench store coupon",
                        kind="store_coupon",
                        scope="shop",
                        value_type="fixed",
                        value=rng.choice([50, 100, 150]),
                        threshold=1000,
                        stage=1,
                        requires=Requirements(),
                    )
                )
            offers.append(
                Offer(
                    id=f"{product_id}-{platform}",
                    product_id=product_id,
                    platform=platform,
                    platform_name=name,
                    list_price=rng.randint(700, 3500),
                    benefits=benefits,
                )
            )
        products[product_id] = Product(
            id=product_id, title=f"bench {product_id}", category="测试", offers=offers
        )
    return products


def benchmark_cart(items: int, cases: int, seed: int) -> dict:
    rng = random.Random(seed)
    timings: list[float] = []
    for _ in range(cases):
        products = cart_products(rng, items)
        cart_items = [CartItemInput(product_id=f"C{index}") for index in range(items)]
        context = SolverContext(now=NOW, region="浙江")
        start = time.perf_counter()
        result = optimize_cart(cart_items, products, context)
        timings.append((time.perf_counter() - start) * 1000)
        assert result.total_payment >= 0
    timings.sort()
    return {
        "items": items,
        "cases": cases,
        "avg_ms": round(statistics.mean(timings), 3),
        "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 3),
        "max_ms": round(max(timings), 3),
    }


def main() -> None:
    report = {
        "single_offer": [solve_many(count, 120, seed=100 + count) for count in (6, 10, 14)],
        "cart": [benchmark_cart(items, 60, seed=200 + items) for items in (3, 5)],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
