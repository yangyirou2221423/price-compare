"""Build the deterministic demo catalogue used by the competition prototype.

Run:  python data/build_seed.py
Out:  data/seed/catalog.json

All prices, coupons and policy rules are illustrative.  The UI labels them as
demo data; no page is scraped and no platform credential is required.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "seed" / "catalog.json"

PLATFORM_NAME = {
    "jd": "京东",
    "taobao": "淘宝",
    "pdd": "拼多多",
    "douyin": "抖音",
}
PLATFORM_SUFFIX = {"jd": "JD", "taobao": "TB", "pdd": "PDD", "douyin": "DY"}


def b(
    benefit_id: str,
    name: str,
    kind: str,
    value: float = 0,
    stage: int = 1,
    scope: str = "item",
    value_type: str = "fixed",
    **extra,
) -> dict:
    data = {
        "id": benefit_id,
        "name": name,
        "kind": kind,
        "stage": stage,
        "scope": scope,
        "value_type": value_type,
        "value": value,
        "source": "mock",
    }
    data.update({key: value for key, value in extra.items() if value is not None})
    return data


def offer(
    product_id: str,
    platform: str,
    price: float,
    benefits: list[dict] | None = None,
    *,
    list_price: float | None = None,
    shop: str | None = None,
) -> dict:
    suffix = PLATFORM_SUFFIX[platform]
    shop = shop or {
        "jd": "品牌京东自营旗舰店",
        "taobao": "品牌官方旗舰店",
        "pdd": "百亿补贴官方频道",
        "douyin": "品牌官方直播间",
    }[platform]
    return {
        "id": f"O{product_id[1:]}-{suffix}",
        "product_id": product_id,
        "platform": platform,
        "platform_name": PLATFORM_NAME[platform],
        "shop_name": shop,
        "list_price": price if list_price is None else list_price,
        "shipping_fee": 0,
        "url": f"https://example.com/demo/{platform}/{product_id}",
        "source": "mock",
        "benefits": benefits or [],
    }


def product(
    product_id: str,
    title: str,
    brand: str,
    model: str,
    category: str,
    specs: str,
    tags: list[str],
    description: str,
    offers: list[dict],
    *,
    featured: bool = False,
) -> dict:
    return {
        "id": product_id,
        "title": title,
        "brand": brand,
        "model": model,
        "category": category,
        "specs": specs,
        "image": f"/static/products/{product_id.lower()}.png",
        "tags": tags,
        "description": description,
        "featured": featured,
        "offers": offers,
    }


JD_FULL_3000_300 = lambda: b(
    "JD-FULL-3000-300",
    "京东跨店满 3000 减 300",
    "full_reduction",
    value=300,
    stage=3,
    scope="platform",
    threshold=3000,
    description="示例：订单小计满 3000 元可用，同一平台订单合并计算。",
)
TB_FULL_4000_400 = lambda: b(
    "TB-FULL-4000-400",
    "淘宝跨店满 4000 减 400",
    "full_reduction",
    value=400,
    stage=3,
    scope="platform",
    threshold=4000,
    description="示例：订单小计满 4000 元可用，同一平台订单合并计算。",
)


def build() -> dict:
    products = [
        product(
            "P001",
            "星海 X1 Pro 5G 手机 256GB",
            "星海",
            "X1 Pro",
            "手机",
            "12GB + 256GB，曜石黑",
            ["国补示例", "旗舰", "百亿补贴"],
            "旗舰影像与长续航，演示“标价最低不等于到手最低”的核心场景。",
            [
                offer(
                    "P001",
                    "jd",
                    5899,
                    [
                        b(
                            "B001-JD-STORE",
                            "店铺券 满 5000 减 100",
                            "store_coupon",
                            value=100,
                            stage=1,
                            scope="shop",
                            threshold=5000,
                        ),
                        b(
                            "B-JD-PLATFORM-5000-200",
                            "京东平台券 满 5000 减 200",
                            "platform_coupon",
                            value=200,
                            stage=2,
                            scope="platform",
                            threshold=5000,
                            stack_group="jd_platform_coupon",
                        ),
                    ],
                ),
                offer(
                    "P001",
                    "taobao",
                    5999,
                    [
                        b(
                            "B001-TB-STORE",
                            "店铺券 满 5000 减 400",
                            "store_coupon",
                            value=400,
                            stage=1,
                            scope="shop",
                            threshold=5000,
                        )
                    ],
                ),
                offer(
                    "P001",
                    "pdd",
                    5299,
                    [
                        b(
                            "B001-PDD-BAIYI",
                            "百亿补贴活动价",
                            "platform_subsidy",
                            value=5299,
                            stage=0,
                            scope="item",
                            value_type="price_override",
                            description="平台活动价 5299 元，作为到手价计算的起点。",
                        )
                    ],
                    list_price=5499,
                    shop="百亿补贴官方频道",
                ),
                offer(
                    "P001",
                    "douyin",
                    5799,
                    [
                        b(
                            "B001-DY-PLATFORM",
                            "直播间平台券 满 5000 减 150",
                            "platform_coupon",
                            value=150,
                            stage=2,
                            scope="platform",
                            threshold=5000,
                        )
                    ],
                ),
            ],
            featured=True,
        ),
        product(
            "P002",
            "灵越 Air 14 轻薄本 16GB+512GB",
            "灵越",
            "Air 14",
            "笔记本",
            "16GB + 512GB，月光银",
            ["电脑补贴示例", "88VIP", "返利"],
            "演示会员折扣、平台券与返利组合后的净价比较。",
            [
                offer(
                    "P002",
                    "jd",
                    4899,
                    [
                        b(
                            "B002-JD-PLATFORM",
                            "京东平台券 满 4000 减 100",
                            "platform_coupon",
                            value=100,
                            stage=2,
                            scope="platform",
                            threshold=4000,
                        ),
                        b(
                            "B002-JD-PAY",
                            "白条支付立减 50",
                            "payment_discount",
                            value=50,
                            stage=8,
                            scope="platform",
                        ),
                    ],
                ),
                offer(
                    "P002",
                    "taobao",
                    4999,
                    [
                        b(
                            "B002-TB-STORE",
                            "店铺券 满 4000 减 200",
                            "store_coupon",
                            value=200,
                            stage=1,
                            scope="shop",
                            threshold=4000,
                        ),
                        b(
                            "B002-TB-VIP",
                            "88VIP 95 折",
                            "member",
                            value=5,
                            stage=4,
                            scope="platform",
                            value_type="percent",
                            max_discount=300,
                            requires={"memberships": ["88VIP"]},
                        ),
                        b(
                            "B002-TB-REBATE",
                            "淘宝返利 2%",
                            "rebate",
                            value=2,
                            stage=9,
                            scope="platform",
                            value_type="percent",
                            max_discount=100,
                            description="按实付金额估算返利，不直接降低支付金额。",
                        ),
                    ],
                ),
                offer("P002", "pdd", 4999, []),
                offer(
                    "P002",
                    "douyin",
                    4899,
                    [
                        b(
                            "B002-DY-PLATFORM",
                            "直播间优惠券 50",
                            "platform_coupon",
                            value=50,
                            stage=2,
                            scope="platform",
                            threshold=4000,
                        )
                    ],
                ),
            ],
            featured=True,
        ),
        product(
            "P003",
            "声阔 Pods Pro 主动降噪耳机",
            "声阔",
            "Pods Pro",
            "耳机",
            "入耳式，星云白",
            ["降噪", "凑单候选"],
            "价格较低，适合演示购物车拆单与店铺券的行级计算。",
            [
                offer(
                    "P003",
                    "jd",
                    1299,
                    [
                        b(
                            "B003-JD-STORE",
                            "店铺券 满 1000 减 100",
                            "store_coupon",
                            value=100,
                            stage=1,
                            scope="shop",
                            threshold=1000,
                        ),
                        JD_FULL_3000_300(),
                    ],
                ),
                offer(
                    "P003",
                    "taobao",
                    1199,
                    [
                        b(
                            "B003-TB-STORE",
                            "店铺券 满 1000 减 80",
                            "store_coupon",
                            value=80,
                            stage=1,
                            scope="shop",
                            threshold=1000,
                        ),
                        TB_FULL_4000_400(),
                    ],
                ),
                offer("P003", "pdd", 1099, []),
                offer(
                    "P003",
                    "douyin",
                    1249,
                    [
                        b(
                            "B003-DY-PLATFORM",
                            "直播间券 50",
                            "platform_coupon",
                            value=50,
                            stage=2,
                            scope="platform",
                            threshold=1000,
                        )
                    ],
                ),
            ],
        ),
        product(
            "P004",
            "净界 空气净化器 Pro",
            "净界",
            "Air Pro",
            "家电",
            "适用 60㎡，除醛增强版",
            ["国补示例", "以旧换新", "浙江加码"],
            "演示国补、地区加码与以旧换新三类补贴的叠加和顺序。",
            [
                offer(
                    "P004",
                    "jd",
                    3299,
                    [
                        b(
                            "B004-JD-PLATFORM",
                            "京东平台券 满 3000 减 200",
                            "platform_coupon",
                            value=200,
                            stage=2,
                            scope="platform",
                            threshold=3000,
                        )
                    ],
                ),
                offer(
                    "P004",
                    "taobao",
                    3399,
                    [
                        b(
                            "B004-TB-STORE",
                            "店铺券 满 3000 减 300",
                            "store_coupon",
                            value=300,
                            stage=1,
                            scope="shop",
                            threshold=3000,
                        )
                    ],
                ),
                offer("P004", "pdd", 3199, []),
                offer(
                    "P004",
                    "douyin",
                    3399,
                    [
                        b(
                            "B004-DY-PLATFORM",
                            "直播间券 100",
                            "platform_coupon",
                            value=100,
                            stage=2,
                            scope="platform",
                            threshold=3000,
                        )
                    ],
                ),
            ],
            featured=True,
        ),
        product(
            "P005",
            "云鲸 扫地机器人 J6",
            "云鲸",
            "J6",
            "清洁电器",
            "自动集尘，银灰",
            ["满减凑单", "拆单示例"],
            "演示“差 80 元满减”时，如何用凑单或换平台降低实付。",
            [
                offer("P005", "jd", 2920, [JD_FULL_3000_300()]),
                offer("P005", "taobao", 3199, [TB_FULL_4000_400()]),
                offer("P005", "pdd", 2999, []),
                offer("P005", "douyin", 2949, []),
            ],
            featured=True,
        ),
        product(
            "P006",
            "极光 智能投影仪 P3",
            "极光",
            "P3",
            "影音",
            "1080P，自动对焦",
            ["跨平台拆单"],
            "与扫地机、耳机组成三件购物车，演示跨平台拆单。",
            [
                offer("P006", "jd", 2999, [JD_FULL_3000_300()]),
                offer("P006", "taobao", 2899, [TB_FULL_4000_400()]),
                offer("P006", "pdd", 2799, []),
                offer("P006", "douyin", 2899, []),
            ],
        ),
        product(
            "P007",
            "星环 智能手表 S2",
            "星环",
            "S2",
            "穿戴",
            "46mm，蓝牙通话",
            ["百亿补贴"],
            "多个平台到手价接近，用于演示同价时的净价与规则排序。",
            [
                offer(
                    "P007",
                    "jd",
                    999,
                    [
                        b(
                            "B007-JD-PLATFORM",
                            "平台券 满 800 减 100",
                            "platform_coupon",
                            value=100,
                            stage=2,
                            scope="platform",
                            threshold=800,
                        )
                    ],
                ),
                offer(
                    "P007",
                    "taobao",
                    999,
                    [
                        b(
                            "B007-TB-STORE",
                            "店铺券 50",
                            "store_coupon",
                            value=50,
                            stage=1,
                            scope="shop",
                            threshold=800,
                        ),
                        b(
                            "B007-TB-PLATFORM",
                            "平台券 50",
                            "platform_coupon",
                            value=50,
                            stage=2,
                            scope="platform",
                            threshold=800,
                        ),
                    ],
                ),
                offer(
                    "P007",
                    "pdd",
                    899,
                    [
                        b(
                            "B007-PDD-BAIYI",
                            "百亿补贴价",
                            "platform_subsidy",
                            value=899,
                            stage=0,
                            scope="item",
                            value_type="price_override",
                        )
                    ],
                    list_price=949,
                ),
                offer(
                    "P007",
                    "douyin",
                    949,
                    [
                        b(
                            "B007-DY-PLATFORM",
                            "直播间券 50",
                            "platform_coupon",
                            value=50,
                            stage=2,
                            scope="platform",
                            threshold=800,
                        )
                    ],
                ),
            ],
        ),
        product(
            "P008",
            "松下 滚筒洗衣机 10kg",
            "松下",
            "XQG100",
            "家电",
            "10kg 变频，除菌洗",
            ["国补示例", "以旧换新"],
            "高客单价家电，演示平台券、国补、地区加码与旧机抵扣。",
            [
                offer(
                    "P008",
                    "jd",
                    4599,
                    [
                        b(
                            "B008-JD-PLATFORM",
                            "京东平台券 满 4000 减 300",
                            "platform_coupon",
                            value=300,
                            stage=2,
                            scope="platform",
                            threshold=4000,
                        )
                    ],
                ),
                offer(
                    "P008",
                    "taobao",
                    4699,
                    [
                        b(
                            "B008-TB-STORE",
                            "店铺券 满 4000 减 400",
                            "store_coupon",
                            value=400,
                            stage=1,
                            scope="shop",
                            threshold=4000,
                        )
                    ],
                ),
                offer("P008", "pdd", 4499, []),
                offer(
                    "P008",
                    "douyin",
                    4599,
                    [
                        b(
                            "B008-DY-PLATFORM",
                            "直播间券 200",
                            "platform_coupon",
                            value=200,
                            stage=2,
                            scope="platform",
                            threshold=4000,
                        )
                    ],
                ),
            ],
            featured=True,
        ),
        product(
            "P009",
            "追风 高速吹风机",
            "追风",
            "Hurricane",
            "个护",
            "11 万转，恒温护发",
            ["个护"],
            "无国补品类，演示纯平台优惠的组合。",
            [
                offer(
                    "P009",
                    "jd",
                    2999,
                    [
                        b(
                            "B009-JD-PLATFORM",
                            "平台券 满 2500 减 200",
                            "platform_coupon",
                            value=200,
                            stage=2,
                            scope="platform",
                            threshold=2500,
                        )
                    ],
                ),
                offer(
                    "P009",
                    "taobao",
                    2899,
                    [
                        b(
                            "B009-TB-STORE",
                            "店铺券 满 2000 减 150",
                            "store_coupon",
                            value=150,
                            stage=1,
                            scope="shop",
                            threshold=2000,
                        )
                    ],
                ),
                offer("P009", "pdd", 2799, []),
                offer(
                    "P009",
                    "douyin",
                    2849,
                    [
                        b(
                            "B009-DY-PLATFORM",
                            "直播间券 50",
                            "platform_coupon",
                            value=50,
                            stage=2,
                            scope="platform",
                            threshold=2000,
                        )
                    ],
                ),
            ],
        ),
        product(
            "P010",
            "星海 Pad Air 11 平板",
            "星海",
            "Pad Air 11",
            "平板",
            "8GB + 256GB，星光色",
            ["平板补贴示例", "88VIP"],
            "演示会员权益对平板补贴场景的影响。",
            [
                offer(
                    "P010",
                    "jd",
                    3899,
                    [
                        b(
                            "B010-JD-PLATFORM",
                            "平台券 满 3500 减 200",
                            "platform_coupon",
                            value=200,
                            stage=2,
                            scope="platform",
                            threshold=3500,
                        )
                    ],
                ),
                offer(
                    "P010",
                    "taobao",
                    3999,
                    [
                        b(
                            "B010-TB-STORE",
                            "店铺券 满 3500 减 300",
                            "store_coupon",
                            value=300,
                            stage=1,
                            scope="shop",
                            threshold=3500,
                        ),
                        b(
                            "B010-TB-VIP",
                            "88VIP 95 折",
                            "member",
                            value=5,
                            stage=4,
                            scope="platform",
                            value_type="percent",
                            max_discount=300,
                            requires={"memberships": ["88VIP"]},
                        ),
                        b(
                            "B010-TB-REBATE",
                            "返利 2%",
                            "rebate",
                            value=2,
                            stage=9,
                            scope="platform",
                            value_type="percent",
                            max_discount=80,
                        ),
                    ],
                ),
                offer("P010", "pdd", 3799, []),
                offer(
                    "P010",
                    "douyin",
                    3899,
                    [
                        b(
                            "B010-DY-PLATFORM",
                            "直播间券 100",
                            "platform_coupon",
                            value=100,
                            stage=2,
                            scope="platform",
                            threshold=3500,
                        )
                    ],
                ),
            ],
            featured=True,
        ),
        product(
            "P011",
            "战刃 游戏本 16  RTX 独显",
            "战刃",
            "Blade 16",
            "笔记本",
            "16GB + 1TB，2.5K 165Hz",
            ["价格上限示例"],
            "售价超过示例补贴上限，用于演示“有补贴规则但不符合资格”。",
            [
                offer(
                    "P011",
                    "jd",
                    7999,
                    [
                        b(
                            "B011-JD-PLATFORM",
                            "平台券 满 7000 减 300",
                            "platform_coupon",
                            value=300,
                            stage=2,
                            scope="platform",
                            threshold=7000,
                        )
                    ],
                ),
                offer(
                    "P011",
                    "taobao",
                    7899,
                    [
                        b(
                            "B011-TB-STORE",
                            "店铺券 满 7000 减 400",
                            "store_coupon",
                            value=400,
                            stage=1,
                            scope="shop",
                            threshold=7000,
                        )
                    ],
                ),
                offer("P011", "pdd", 7699, []),
                offer(
                    "P011",
                    "douyin",
                    7799,
                    [
                        b(
                            "B011-DY-PLATFORM",
                            "直播间券 100",
                            "platform_coupon",
                            value=100,
                            stage=2,
                            scope="platform",
                            threshold=7000,
                        )
                    ],
                ),
            ],
        ),
        product(
            "P012",
            "简物 桌面收纳盒",
            "简物",
            "Box Mini",
            "家居",
            "双层抽屉式，米白",
            ["凑单候选"],
            "89 元的低价商品，用于演示凑单后实付反而下降。",
            [
                offer("P012", "jd", 89, [], shop="简物京东自营旗舰店"),
                offer("P012", "taobao", 99, [], shop="简物官方旗舰店"),
                offer("P012", "pdd", 79, [], shop="简物工厂店"),
            ],
        ),
    ]

    subsidy_rules = [
        {
            "id": "R-MOBILE-15",
            "name": "手机购新补贴（示例）",
            "type": "national_subsidy",
            "regions": ["全国"],
            "categories": ["手机"],
            "platforms": ["taobao"],
            "price_cap": 6000,
            "price_cap_base": "list",
            "percent": 15,
            "max_discount": 500,
            "stage": 6,
            "stack_group": "national_subsidy",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "description": "按券后价 15% 估算，单件最高 500 元；本示例仅淘宝参与。",
            "source": "示例政策",
            "version": "2026.1",
            "priority": 10,
        },
        {
            "id": "R-APPLIANCE-15",
            "name": "家电购新补贴（示例）",
            "type": "national_subsidy",
            "regions": ["全国"],
            "categories": ["家电"],
            "platforms": ["jd", "taobao", "pdd", "douyin"],
            "price_cap": 6000,
            "price_cap_base": "list",
            "percent": 15,
            "max_discount": 500,
            "stage": 6,
            "stack_group": "national_subsidy",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "description": "按券后价 15% 估算，单件最高 500 元。",
            "source": "示例政策",
            "version": "2026.1",
            "priority": 10,
        },
        {
            "id": "R-ZHEJIANG-EXTRA",
            "name": "浙江家电加码补贴（示例）",
            "type": "province_subsidy",
            "regions": ["浙江"],
            "categories": ["家电"],
            "platforms": ["jd", "taobao", "pdd", "douyin"],
            "percent": 5,
            "max_discount": 200,
            "stage": 6,
            "stack_group": "province_extra_zhejiang",
            "effective_from": "2026-06-01",
            "effective_to": "2026-12-31",
            "description": "示例：浙江地区家电加码 5%，最高 200 元，可与国补叠加。",
            "source": "示例政策",
            "version": "2026.2",
            "priority": 20,
        },
        {
            "id": "R-LAPTOP-10",
            "name": "电脑购新补贴（示例）",
            "type": "national_subsidy",
            "regions": ["全国"],
            "categories": ["笔记本"],
            "platforms": ["jd", "taobao", "pdd", "douyin"],
            "price_cap": 7000,
            "price_cap_base": "list",
            "percent": 10,
            "max_discount": 500,
            "stage": 6,
            "stack_group": "national_subsidy",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "description": "售价不超过 7000 元的部分电脑可享 10% 补贴，单件最高 500 元。",
            "source": "示例政策",
            "version": "2026.1",
            "priority": 10,
        },
        {
            "id": "R-TABLET-10",
            "name": "平板购新补贴（示例）",
            "type": "national_subsidy",
            "regions": ["全国"],
            "categories": ["平板"],
            "platforms": ["jd", "taobao", "pdd", "douyin"],
            "price_cap": 7000,
            "price_cap_base": "list",
            "percent": 10,
            "max_discount": 500,
            "stage": 6,
            "stack_group": "national_subsidy",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "description": "售价不超过 7000 元的平板可享 10% 补贴，单件最高 500 元。",
            "source": "示例政策",
            "version": "2026.1",
            "priority": 10,
        },
        {
            "id": "R-TRADEIN",
            "name": "京东以旧换新（示例）",
            "type": "trade_in",
            "regions": ["全国"],
            "categories": ["手机", "家电", "笔记本", "平板"],
            "platforms": ["jd"],
            "requires_trade_in": True,
            "flat_amount": 0,
            "stage": 7,
            "stack_group": "trade_in",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "description": "旧机估值按用户在比价上下文中填写的金额计入，整单抵扣一次。",
            "source": "示例政策",
            "version": "2026.1",
            "priority": 30,
        },
    ]

    price_history: dict[str, dict] = {}
    for item in products:
        for current_offer in item["offers"]:
            offer_id = current_offer["id"]
            digest = hashlib.md5(offer_id.encode("utf-8")).hexdigest()
            price_history[offer_id] = {
                "seed": int(digest[:8], 16) % 100000,
                "fake_drop": offer_id in {"O001-PDD", "O011-JD"},
            }

    return {
        "version": "2026.11-demo",
        "generated_by": "data/build_seed.py",
        "products": products,
        "subsidy_rules": subsidy_rules,
        "price_history": price_history,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    offers = sum(len(item["offers"]) for item in data["products"])
    print(f"wrote {OUT} ({len(data['products'])} products, {offers} offers)")


if __name__ == "__main__":
    main()
