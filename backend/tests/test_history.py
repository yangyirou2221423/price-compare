"""Tests for price-history analysis."""

from __future__ import annotations

from datetime import date

from app.engine.history import analyze_history, generate_price_series


def test_fake_drop_is_detected() -> None:
    points = generate_price_series(
        3000, days=90, end_date=date(2026, 11, 13), seed=3, fake_drop=True
    )
    analysis = analyze_history("P1", "jd", "京东", points)

    assert analysis.fake_drop is True
    assert analysis.current_price < analysis.median_price
    assert "先涨后降" in analysis.verdict


def test_stable_history_reports_position() -> None:
    points = generate_price_series(
        3000, days=90, end_date=date(2026, 11, 13), seed=11, fake_drop=False
    )
    analysis = analyze_history("P1", "jd", "京东", points)

    assert analysis.median_price > 0
    assert 0 <= analysis.percentile <= 100
    assert analysis.lowest_90d <= analysis.current_price + 0.01
    assert analysis.verdict
