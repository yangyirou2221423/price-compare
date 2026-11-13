# 系统架构

## 1. 目标与边界

**目标**：给定商品/购物车与用户条件（地区、会员、以旧换新），计算每个平台的最优到手价与可执行购买步骤，并解释结果。

**边界**：

- 演示数据驱动，不抓取平台页面。
- 不接入真实支付、订单、返利提现。
- 购物车按“同一平台商品合并为一单”建模，未覆盖多店铺、多地址、预售等复杂场景。
- 电商平台数据以官方联盟接口为未来接入方向。

## 2. 总体架构

```
┌──────────────────────────────────────────────────────┐
│ uni-app (Vue 3 + TypeScript + Pinia)                 │
│  ├─ H5（答辩主演示）                                  │
│  └─ 微信小程序（开发者工具 / 体验版）                  │
└──────────────────────┬───────────────────────────────┘
                       │ HTTPS / JSON
┌──────────────────────▼───────────────────────────────┐
│ FastAPI                                               │
│  ├─ api/catalog.py    首页、商品、配置、规则、适配器   │
│  ├─ api/strategy.py   比价、策略、购物车、补贴计算     │
│  ├─ api/history.py    价格历史、用户提交               │
│  ├─ engine/           框架无关的领域模型与求解器       │
│  ├─ db/               SQLAlchemy 2 + SQLite            │
│  └─ adapters/         数据源契约 + Mock + 联盟占位     │
└──────────────────────┬───────────────────────────────┘
                       │
        data/seed/catalog.json + 90 天价格历史生成
```

### 分层原则

- **engine 不依赖 FastAPI / SQLAlchemy**：只依赖 Pydantic，便于单测、基准与未来替换为云函数。
- **规则在请求时物化**：国补/以旧换新规则从 DB 读出，转换成 `Benefit` 后进入统一求解流程。
- **数据源可替换**：`PlatformDataSource` 契约把 Mock、用户提交、联盟 API 隔离开。
- **前端只消费 API**：页面不复制计算逻辑，避免两端结果不一致。

## 3. 后端模块

| 文件 | 职责 |
|---|---|
| `backend/app/engine/model.py` | Product / Offer / Benefit / SubsidyRule / 结果模型；金额按分四舍五入 |
| `backend/app/engine/rules.py` | 资格谓词、门槛、互斥、金额计算、规则物化为 Benefit |
| `backend/app/engine/stacker.py` | 单商品 DFS + 分支限界 + 记忆化；多平台比较与摘要 |
| `backend/app/engine/cart_solver.py` | 平台划分枚举、订单级优惠求解、凑单建议 |
| `backend/app/engine/history.py` | 90 天价格统计、分位、先涨后降识别、演示序列生成 |
| `backend/app/engine/benchmark.py` | 合成实例性能基准 |
| `backend/app/api/*` | HTTP 路由、请求校验、StrategyRun 落库 |
| `backend/app/db/models.py` | ORM 表 |
| `backend/app/db/seed.py` | 建表、载入 catalog、生成价格历史 |
| `backend/app/db/repository.py` | ORM → 领域模型 |
| `backend/app/adapters/*` | 数据源契约、Mock、联盟适配器（凭证门控） |

## 4. 数据模型

| 表 | 关键字段 | 说明 |
|---|---|---|
| `products` | id, title, brand, category, specs, tags, image, featured | 标准化商品 |
| `offers` | id, product_id, platform, shop, list_price, shipping, source | 平台报价 |
| `benefits` | offer_id, benefit_id, kind, value_type, value, threshold, stage, stack_group, requires, 有效期 | 优惠/补贴 |
| `subsidy_rules` | id, type, regions, categories, platforms, price_cap, percent, flat_amount, 生效期, version | 政策/平台补贴规则 |
| `price_history` | product_id, platform, date, price | 90 天价格点 |
| `submissions` | product_id, platform, price, link, note, created_at | 用户提交价格 |
| `strategy_runs` | product_id, request_json, result_json, engine_version | 结果快照，便于复现 |

种子规模：12 个商品、47 条平台报价、6 条补贴规则、4,230 个价格历史点（47 × 90）。

### Benefit 语义

- `kind`：店铺券/平台券/品类券/满减/会员/平台补贴/国补/以旧换新/支付立减/返利/赠品。
- `value_type`：固定金额、百分比、每满减、活动价覆盖。
- `threshold_base`：门槛按原价（list）还是当前价（current）判断。
- `stage`：使用顺序（活动价 0 → 店铺券 1 → 平台券 2 → 满减 3 → 会员 4 → 平台补贴 5 → 国补 6 → 以旧换新 7 → 支付 8 → 返利 9 → 赠品 10）。
- `stack_group`：同组互斥，最多用一张。
- `exclusive_with`：显式互斥。
- `requires`：会员、地区、以旧换新、首单、最小数量。
- `price_cap`：补贴价格上限（如国补 6000 元）。

## 5. API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/home` | 首页推荐卡与默认条件 |
| GET | `/api/products?q=&category=&featured=` | 商品搜索/列表 |
| GET | `/api/products/{id}` | 商品详情 + 平台报价 |
| GET | `/api/products/{id}/offers` | 平台报价列表 |
| GET | `/api/products/{id}/history?days=90&platform=` | 价格历史分析 |
| POST | `/api/compare` | 单商品多平台到手价对比 |
| POST | `/api/strategy` | 最优策略 + 解释，并落库 StrategyRun |
| POST | `/api/cart/optimize` | 购物车拆单 + 凑单建议 |
| POST | `/api/subsidy/check` | 国补/以旧换新资格计算器 |
| GET | `/api/rules?region=&category=` | 规则查询 |
| GET | `/api/adapters` | 数据源状态（Mock 可用、联盟待授权） |
| POST | `/api/submissions` | 用户提交价格 |
| GET | `/api/submissions` | 最近提交 |
| DELETE | `/api/submissions/{id}` | 删除用户提交 |
| GET | `/docs` | OpenAPI 文档 |

统一条件字段：`region`、`memberships[]`、`trade_in`、`preference`（`payment` / `net`）。`now` 可覆盖演示日期，便于测试规则生效期。

## 6. 前端

### 页面

| 页面 | 作用 |
|---|---|
| `pages/index` | 首页：搜索、快捷入口、价格侦探、推荐商品 |
| `pages/discover` | 商品搜索/品类筛选 |
| `pages/compare` | 商品详情、最优卡、价格瀑布、平台对比、历史预览 |
| `pages/strategy` | 购买步骤时间线、备选平台、未采用优惠、复制步骤 |
| `pages/cart` | 本地购物车、拆单结果、凑单建议、一键示例 |
| `pages/history` | 90 天价格带、统计、先涨后降提示 |
| `pages/subsidy` | 国补/地区加码/以旧换新资格计算器 |
| `pages/profile` | 购买条件、收藏、提交价格、数据合规、重置 |

### 组件

- `PageHeader`：品牌/返回、条件 chip、条件抽屉入口。
- `ContextSheet`：地区、会员、以旧换新、排序偏好。
- `PlatformPriceCard`：平台报价、优惠 chips、拒绝原因。
- `PriceWaterfall`：标价 → 优惠 → 到手价。
- `StrategyTimeline`：按顺序执行的步骤与执行后价格。
- `PriceSparkline`：纯 CSS 的 90 天价格带，H5/小程序通用。
- `ProductCard`、`DataSourceBadge`、`EmptyState`。

### 状态

`stores/app.ts` 持久化到本地：

- 地区、会员、以旧换新、排序偏好；
- 购物车（productId、title、image、unitPrice、quantity）；
- 收藏。

条件变化会触发页面重新请求，因此“88VIP 切换改变最优平台”不需要前端重算。

## 7. 请求流示例：单商品策略

```
[Compare page]
  POST /api/strategy {product_id, region, memberships, trade_in, preference}
        │
        ▼
[API] get_product + load_rules
        │
        ▼
[compare_product]
  for each offer:
    build_rule_benefits()          # 国补/以旧换新物化
    _prepare()                     # 活动价、去重
    DFS + 分支限界 + 记忆化         # 选优惠组合
    _rejections_for_best()         # 解释未采用优惠
  sort by (final_price, net_price) 或 (net, final)
        │
        ▼
[Response] best + results + steps + rejected + assumptions + engineVersion
```

## 8. 部署

### 本地演示（推荐）

- FastAPI `127.0.0.1:8000` + H5 `127.0.0.1:5173`。
- CORS 在开发环境允许所有来源；生产应收紧。
- SQLite 零配置；删除 DB 文件后重启自动重建。

### 微信开发者工具

- 导入 `frontend/dist/build/mp-weixin`。
- `manifest.json` 的 `mp-weixin.appid` 为 `touristappid`，可替换。
- 勾选“不校验合法域名”访问本地 API。

### 手机体验版 / 生产

- 需要 HTTPS 合法域名（通常需要备案）并配置 request 合法域名。
- 可选：微信云托管 / 已备案服务器 + 反向代理。
- 由于平台外链限制，小程序内不做直接跳转淘宝/京东；采用展示步骤 + 复制口令。

## 9. 设计取舍

| 决策 | 原因 |
|---|---|
| FastAPI + Python | 算法/测试/基准最顺手，pytest 差分测试成本低 |
| uni-app | 一套代码覆盖 H5 + 微信小程序，H5 保证评委可访问 |
| SQLite | 演示零运维；ORM 可平滑换 PostgreSQL |
| 纯 Python 求解器 | 无 OR-Tools 依赖，逻辑透明、易解释；ILP 作为未来扩展 |
| 请求时物化规则 | 规则更新无需改代码；结果可带版本与生效期 |
| 演示数据 | 避免合规与稳定性风险；数据源契约保留真实接入路径 |
| H5 主演示 | 规避小程序域名、审核、网络风险 |

## 10. 失败与降级

- API 不可达：页面显示错误与重试，不白屏。
- 某个优惠不合法：进入 `rejected`，不影响其他优惠。
- 商品无报价：返回 404 / 空状态。
- 购物车无法分配：API 返回 400，前端提示。
- 超出精确搜索规模：退货启发式并标注 `optimal: false`。
- 规则过期/未生效：资格判定解释原因。
