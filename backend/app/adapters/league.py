"""Credential-gated stubs for official affiliate data sources.

They intentionally do not fetch anything.  The competition demo uses the mock
catalogue and documents the real integration path; production access requires
an approved account, signatures, rate limits and commercial terms.
"""

from __future__ import annotations

from app.adapters.base import DataSourceUnavailable, PlatformDataSource
from app.engine.model import Offer, Product


class _LeagueSource(PlatformDataSource):
    requires_credentials = True
    note = "需要官方联盟账号、应用审核与接口权限。"

    def __init__(self, credentials: dict | None = None):
        self._credentials = credentials or {}

    @property
    def available(self) -> bool:
        return bool(self._credentials)

    def fetch_offers(self, product: Product) -> list[Offer]:
        if not self.available:
            raise DataSourceUnavailable(
                f"{self.display_name} 未配置凭证；{self.note}"
            )
        raise DataSourceUnavailable(
            f"{self.display_name} 已配置凭证，但演示环境未启用真实请求。"
        )


class JDUnionDataSource(_LeagueSource):
    source_id = "jd_union"
    platform = "jd"
    display_name = "京东联盟"


class TaobaoKeDataSource(_LeagueSource):
    source_id = "taobao_ke"
    platform = "taobao"
    display_name = "淘宝客"


class PDDUnionDataSource(_LeagueSource):
    source_id = "pdd_union"
    platform = "pdd"
    display_name = "多多进宝"


class DouyinUnionDataSource(_LeagueSource):
    source_id = "douyin_union"
    platform = "douyin"
    display_name = "抖音精选联盟"
