"""Price-history statistics and "is this a real drop?" heuristics."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from .model import PriceHistoryAnalysis, PricePoint, money
from .stacker import CN_TZ


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def analyze_history(
    product_id: str,
    platform: str,
    platform_name: str,
    points: list[PricePoint],
    days: int = 90,
) -> PriceHistoryAnalysis:
    """Compute low-price position and a simple pre-hike-then-drop flag."""

    if not points:
        raise ValueError("price history is empty")

    ordered = sorted(points, key=lambda point: point.date)
    prices = [point.price for point in ordered]
    sorted_prices = sorted(prices)
    current = ordered[-1].price
    last_date = ordered[-1].date
    median = _quantile(sorted_prices, 0.5)
    p25 = _quantile(sorted_prices, 0.25)
    p75 = _quantile(sorted_prices, 0.75)
    minimum = min(prices)
    maximum = max(prices)
    lower_or_equal = sum(1 for price in prices if price <= current + 0.005)
    percentile = round(lower_or_equal / len(prices) * 100, 1)

    last_30 = [p.price for p in ordered if p.date >= last_date - timedelta(days=30)]
    lowest_30d = min(last_30) if last_30 else minimum
    lowest_90d = min(
        [p.price for p in ordered if p.date >= last_date - timedelta(days=90)] or prices
    )

    target = last_date - timedelta(days=7)
    prior = [p for p in ordered if p.date <= target]
    price_7d_ago = prior[-1].price if prior else ordered[0].price
    trend_7d = money(current - price_7d_ago)
    trend_7d_pct = round(trend_7d / price_7d_ago * 100, 2) if price_7d_ago else 0.0

    # A real drop should not be preceded by a sharp, short-lived price hike.
    pre_window = [p.price for p in ordered if last_date - timedelta(days=16) <= p.date < last_date - timedelta(days=3)]
    fake_drop = False
    if len(pre_window) >= 5 and median > 0:
        pre_max = max(pre_window)
        fake_drop = (
            pre_max >= median * 1.06
            and current <= median * 0.95
            and current <= pre_max * 0.90
        )

    is_low = current <= p25 * 1.01 or current <= minimum * 1.02
    if fake_drop:
        verdict = "疑似先涨后降，建议核对历史价格后再决定"
    elif is_low:
        verdict = "当前处于近 90 天低位，适合入手"
    elif current > median * 1.05:
        verdict = "当前高于近 90 天中位价，建议观望"
    else:
        verdict = "当前价格处于常规区间"

    return PriceHistoryAnalysis(
        product_id=product_id,
        platform=platform,
        platform_name=platform_name,
        days=days,
        points=ordered[-days:],
        current_price=money(current),
        median_price=money(median),
        min_price=money(minimum),
        max_price=money(maximum),
        p25=money(p25),
        p75=money(p75),
        percentile=percentile,
        is_low=is_low,
        lowest_30d=money(lowest_30d),
        lowest_90d=money(lowest_90d),
        trend_7d=trend_7d,
        trend_7d_pct=trend_7d_pct,
        fake_drop=fake_drop,
        verdict=verdict,
        generated_at=datetime.now(CN_TZ),
    )


def generate_price_series(
    base_price: float,
    days: int = 90,
    end_date: date | None = None,
    seed: int = 7,
    fake_drop: bool = False,
) -> list[PricePoint]:
    """Deterministic synthetic history for demo data.

    Prices stay in a believable band around ``base_price`` with occasional
    promotion dips.  ``fake_drop`` creates the pre-hike pattern used to
    demonstrate the "先涨后降" detector.
    """

    import math
    import random

    rng = random.Random(seed)
    end_date = end_date or date(2026, 11, 13)
    points: list[PricePoint] = []
    for offset in range(days - 1, -1, -1):
        day = end_date - timedelta(days=offset)
        wave = math.sin((days - offset) / 9.0) * base_price * 0.015
        noise = rng.uniform(-base_price * 0.008, base_price * 0.008)
        price = base_price + wave + noise
        # A few short promotion windows.
        position = days - offset
        if position % 31 in (0, 1, 2):
            price -= base_price * 0.035
        if fake_drop:
            if 3 <= offset <= 12:
                price += base_price * 0.09
            elif offset <= 2:
                price -= base_price * 0.10
        points.append(PricePoint(date=day, price=money(round(price, 2))))
    return points
