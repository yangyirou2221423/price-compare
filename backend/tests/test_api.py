"""End-to-end API tests against the seeded demo catalogue."""

from __future__ import annotations

import pytest


def test_health_and_home(client) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    home = client.get("/api/home")
    assert home.status_code == 200
    body = home.json()
    assert len(body["products"]) >= 5
    ids = {item["id"] for item in body["products"]}
    assert {"P001", "P002", "P004", "P005"} <= ids
    assert body["data_note"]


def test_product_search_and_detail(client) -> None:
    search = client.get("/api/products", params={"q": "耳机"})
    assert search.status_code == 200
    assert [item["id"] for item in search.json()["products"]] == ["P003"]

    detail = client.get("/api/products/P001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["product"]["title"].startswith("星海")
    assert len(body["offers"]) == 4

    missing = client.get("/api/products/NOPE")
    assert missing.status_code == 404


def test_strategy_reverses_lowest_list_price(client) -> None:
    response = client.post(
        "/api/strategy",
        json={"product_id": "P001", "region": "浙江", "memberships": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["best_platform"] == "taobao"
    assert body["best"]["final_price"] == pytest.approx(5099)
    assert body["savings_abs"] == pytest.approx(900)
    assert body["best"]["applied"]
    pdd = next(item for item in body["results"] if item["platform"] == "pdd")
    assert pdd["list_price"] == pytest.approx(5499)
    assert pdd["final_price"] == pytest.approx(5299)


def test_membership_changes_the_winner(client) -> None:
    without = client.post(
        "/api/compare",
        json={"product_id": "P002", "region": "浙江", "memberships": []},
    ).json()
    with_vip = client.post(
        "/api/compare",
        json={"product_id": "P002", "region": "浙江", "memberships": ["88VIP"]},
    ).json()

    assert without["best_platform"] == "jd"
    assert with_vip["best_platform"] == "taobao"
    assert with_vip["best"]["net_price"] < with_vip["best"]["final_price"]


def test_cart_split_and_filler(client) -> None:
    response = client.post(
        "/api/cart/optimize",
        json={
            "items": [
                {"product_id": "P005"},
                {"product_id": "P003"},
                {"product_id": "P006"},
            ],
            "region": "浙江",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cart"]["total_payment"] == pytest.approx(6538)
    assert body["cart"]["baseline_payment"] == pytest.approx(6817)
    assert body["cart"]["assignment"] == {
        "P005": "jd",
        "P003": "taobao",
        "P006": "taobao",
    }
    assert body["fillers"]
    assert body["fillers"][0]["candidates"][0]["product_id"] == "P012"
    assert body["fillers"][0]["candidates"][0]["net_increase"] < 0


def test_price_history_flags_fake_drop(client) -> None:
    response = client.get("/api/products/P001/history", params={"days": 90})
    assert response.status_code == 200
    series = response.json()["series"]
    assert len(series) == 4
    pdd = next(item for item in series if item["platform"] == "pdd")
    assert pdd["fake_drop"] is True
    assert "先涨后降" in pdd["verdict"]
    assert len(pdd["points"]) == 90


def test_subsidy_calculator(client) -> None:
    response = client.post(
        "/api/subsidy/check",
        json={
            "category": "手机",
            "price": 5999,
            "platform": "taobao",
            "region": "浙江",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_estimated"] == pytest.approx(500)
    mobile = next(item for item in body["items"] if item["rule_id"] == "R-MOBILE-15")
    assert mobile["eligible"] is True

    jd = client.post(
        "/api/subsidy/check",
        json={
            "category": "手机",
            "price": 5999,
            "platform": "jd",
            "region": "浙江",
        },
    ).json()
    mobile_jd = next(item for item in jd["items"] if item["rule_id"] == "R-MOBILE-15")
    assert mobile_jd["eligible"] is False
    assert "平台" in mobile_jd["reason"]


def test_adapters_show_mock_and_gated_league_sources(client) -> None:
    response = client.get("/api/adapters")
    assert response.status_code == 200
    adapters = {item["source_id"]: item for item in response.json()["adapters"]}
    assert adapters["mock"]["available"] is True
    assert adapters["jd_union"]["available"] is False
    assert adapters["jd_union"]["requires_credentials"] is True


def test_submission_roundtrip(client) -> None:
    response = client.post(
        "/api/submissions",
        json={
            "product_id": "P001",
            "platform": "jd",
            "price": 5799,
            "link": "https://example.com/demo",
            "note": "测试提交",
        },
    )
    assert response.status_code == 200
    created = response.json()["id"]
    assert created > 0

    listing = client.get("/api/submissions")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    deleted = client.delete(f"/api/submissions/{created}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == created

    after = client.get("/api/submissions").json()["submissions"]
    assert all(item["id"] != created for item in after)
