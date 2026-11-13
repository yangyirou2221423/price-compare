<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type {
  PriceHistoryAnalysis,
  Product,
  StrategyResult,
} from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import PlatformPriceCard from "../../components/PlatformPriceCard.vue";
import PriceWaterfall from "../../components/PriceWaterfall.vue";
import PriceSparkline from "../../components/PriceSparkline.vue";
import DataSourceBadge from "../../components/DataSourceBadge.vue";
import { formatMoney, platformTone, PLATFORM_META } from "../../utils/format";
import { useAppStore } from "../../stores/app";

const store = useAppStore();
const productId = ref("");
const product = ref<Product | null>(null);
const strategy = ref<StrategyResult | null>(null);
const history = ref<PriceHistoryAnalysis | null>(null);
const loading = ref(true);
const error = ref("");

const best = computed(() => (strategy.value ? strategy.value.best : null));
const isFavorite = computed(() =>
  productId.value ? store.isFavorite(productId.value) : false,
);
const priceRange = computed(() => {
  const offers = product.value?.offers || [];
  if (!offers.length) return "";
  const prices = offers.map((offer) => offer.list_price);
  return `${formatMoney(Math.min(...prices))} – ${formatMoney(Math.max(...prices))}`;
});
const bestMark = computed(() => {
  if (!best.value) return "";
  return PLATFORM_META[best.value.platform]?.mark || best.value.platform.slice(0, 1);
});

onLoad((options) => {
  productId.value = String(options?.id || "");
});

onShow(() => {
  if (productId.value) load();
});

async function load() {
  if (!productId.value) {
    error.value = "缺少商品参数";
    loading.value = false;
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const [detail, result] = await Promise.all([
      api.product(productId.value),
      api.compare({
        product_id: productId.value,
        ...store.contextPayload,
      }),
    ]);
    product.value = detail.product;
    strategy.value = result;
    try {
      const response = await api.history(
        productId.value,
        90,
        result.best_platform,
      );
      history.value = response.series[0] || null;
    } catch {
      history.value = null;
    }
  } catch (err: any) {
    error.value = err?.message || "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function openStrategy() {
  uni.navigateTo({
    url: `/pages/strategy/strategy?id=${encodeURIComponent(productId.value)}`,
  });
}

function openHistory() {
  if (!best.value) return;
  uni.navigateTo({
    url: `/pages/history/history?id=${encodeURIComponent(
      productId.value,
    )}&platform=${best.value.platform}`,
  });
}

function addToCart() {
  if (!product.value || !best.value) return;
  store.addToCart({
    productId: product.value.id,
    title: product.value.title,
    image: product.value.image,
    category: product.value.category,
    unitPrice: best.value.final_price,
  });
  uni.showToast({ title: "已加入购物车", icon: "none" });
}

function toggleFavorite() {
  if (!product.value || !best.value) return;
  const added = store.toggleFavorite({
    id: product.value.id,
    title: product.value.title,
    image: product.value.image,
    price: best.value.final_price,
    category: product.value.category,
  });
  uni.showToast({ title: added ? "已收藏" : "已取消收藏", icon: "none" });
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      back
      title="比价详情"
      :subtitle="product?.title || '正在加载'"
      @change="load"
    />

    <view v-if="loading" class="loading-wrap">
      <view class="skeleton" style="height: 118px"></view>
      <view class="skeleton mt-16" style="height: 190px"></view>
      <view class="skeleton mt-16" style="height: 260px"></view>
    </view>

    <view v-else-if="error" class="notice notice--red mt-12">
      {{ error }}
      <view class="retry" @click="load">重新加载</view>
    </view>

    <template v-else-if="product && strategy && best">
      <view class="product-hero card fade-in">
        <image class="product-cover" :src="product.image" mode="aspectFill" />
        <view class="product-info">
          <view class="brand-line">
            <text class="brand">{{ product.brand }}</text>
            <text class="pill">{{ product.category }}</text>
          </view>
          <view class="product-title">{{ product.title }}</view>
          <view class="specs">{{ product.specs }}</view>
          <view class="tags">
            <text v-for="tag in product.tags" :key="tag" class="tag">{{ tag }}</text>
          </view>
          <view class="range">平台标价 {{ priceRange }}</view>
        </view>
        <view class="fav" :class="{ on: isFavorite }" @click="toggleFavorite">
          {{ isFavorite ? "♥" : "♡" }}
        </view>
      </view>

      <view class="best-card fade-in">
        <view class="best-head">
          <view class="flex">
            <view class="best-mark" :class="`mark-${platformTone(best.platform)}`">
              {{ bestMark }}
            </view>
            <view>
              <text class="best-eyebrow">BEST STRATEGY</text>
              <view class="best-platform">{{ best.platform_name }} · 最优到手</view>
            </view>
          </view>
          <DataSourceBadge :source="strategy.data_source" />
        </view>

        <view class="best-price-row">
          <view class="best-price money">{{ formatMoney(best.final_price) }}</view>
          <view v-if="best.promo_savings > 0.005" class="save-pill">
            省 {{ formatMoney(best.promo_savings) }}
          </view>
          <view v-else class="save-pill save-pill--soft">暂无额外优惠</view>
        </view>

        <view class="best-stats">
          <view class="best-stat">
            <text class="stat-label">页面标价</text>
            <text class="stat-value money">{{ formatMoney(best.list_price) }}</text>
          </view>
          <view class="best-stat">
            <text class="stat-label">共优惠</text>
            <text class="stat-value money">{{ formatMoney(best.discount_total) }}</text>
          </view>
          <view class="best-stat">
            <text class="stat-label">
              {{ best.net_price < best.final_price ? "计返利净价" : "执行步骤" }}
            </text>
            <text class="stat-value money">
              {{ best.net_price < best.final_price ? formatMoney(best.net_price) : best.applied.length + " 步" }}
            </text>
          </view>
        </view>

        <view class="best-summary">{{ strategy.summary }}</view>

        <view class="best-actions">
          <button class="btn btn-amber" @click="openStrategy">查看购买策略</button>
          <button class="btn btn-ghost best-ghost" @click="addToCart">加入购物车</button>
        </view>
      </view>

      <view class="section">
        <PriceWaterfall :result="best" />
      </view>

      <view class="section">
        <view class="section-head">
          <view>
            <view class="section-title">各平台到手价</view>
            <view class="section-sub">按当前地区、会员与以旧换新条件计算</view>
          </view>
        </view>
        <PlatformPriceCard
          v-for="item in strategy.results"
          :key="item.offer_id"
          :result="item"
          :best="item.platform === strategy.best_platform"
        />
      </view>

      <view v-if="history" class="section">
        <view class="section-head">
          <view>
            <view class="section-title">价格走势</view>
            <view class="section-sub">{{ history.platform_name }} · 近 {{ history.days }} 天</view>
          </view>
          <view class="section-link" @click="openHistory">展开 →</view>
        </view>
        <view class="history-card card" @click="openHistory">
          <view class="history-top">
            <view>
              <view class="history-price money">{{ formatMoney(history.current_price) }}</view>
              <view class="history-label">当前价格</view>
            </view>
            <view
              class="chip"
              :class="history.fake_drop ? 'chip-red' : history.is_low ? 'chip-green' : 'chip-amber'"
            >
              {{ history.fake_drop ? "疑似先涨后降" : history.is_low ? "历史低位" : "常规区间" }}
            </view>
          </view>
          <PriceSparkline :points="history.points" :height="86" :max-bars="38" />
          <view class="history-verdict">{{ history.verdict }}</view>
        </view>
      </view>

      <view class="notice mt-24">
        {{ strategy.assumptions[0] }}
      </view>
      <view class="notice mt-8">
        当前条件：{{ store.contextLabel }}。改变条件后，最优平台可能变化。
      </view>
    </template>
  </view>
</template>

<style scoped>
.loading-wrap {
  margin-top: 8px;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}

.product-hero {
  position: relative;
  display: flex;
  align-items: center;
  padding: 13px;
  margin-top: 6px;
}

.product-cover {
  width: 112px;
  height: 112px;
  border-radius: 15px;
  flex-shrink: 0;
  background: var(--paper-deep);
}

.product-info {
  flex: 1;
  min-width: 0;
  padding-left: 13px;
}

.brand-line {
  display: flex;
  align-items: center;
}

.brand {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--muted);
  margin-right: 7px;
}

.product-title {
  margin-top: 3px;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: -0.3px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.specs {
  margin-top: 3px;
  font-size: 10px;
  color: var(--muted);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  margin-top: 6px;
}

.tag {
  padding: 2px 6px;
  border-radius: 5px;
  background: var(--paper);
  color: var(--muted);
  font-size: 8px;
  margin: 0 5px 4px 0;
}

.range {
  margin-top: 2px;
  font-size: 9px;
  color: var(--muted-light);
}

.fav {
  position: absolute;
  right: 13px;
  bottom: 13px;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--paper);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.fav.on {
  background: var(--red-soft);
  color: var(--red);
}

.best-card {
  margin-top: 14px;
  padding: 19px;
  border-radius: 22px;
  background: radial-gradient(circle at 88% 0%, #2b4564 0, #14263b 42%, #0b1728 100%);
  color: #fff8ea;
  box-shadow: 0 18px 36px rgba(14, 27, 44, 0.2);
}

.best-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.best-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  margin-right: 9px;
}

.mark-jd {
  background: #d92b22;
}

.mark-taobao {
  background: #e85712;
}

.mark-pdd {
  background: #d63027;
}

.mark-douyin {
  background: #15171c;
}

.mark-default {
  background: var(--ink-soft);
}

.best-eyebrow {
  display: block;
  font-size: 8px;
  letter-spacing: 2px;
  font-weight: 800;
  color: rgba(255, 248, 234, 0.48);
}

.best-platform {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 248, 234, 0.9);
}

.best-price-row {
  display: flex;
  align-items: center;
  margin-top: 13px;
}

.best-price {
  font-size: 40px;
  line-height: 1;
  color: var(--amber);
}

.save-pill {
  margin-left: 10px;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(233, 162, 59, 0.16);
  color: var(--amber);
  font-size: 10px;
  font-weight: 800;
}

.save-pill--soft {
  background: rgba(255, 248, 234, 0.08);
  color: rgba(255, 248, 234, 0.5);
}

.best-stats {
  display: flex;
  margin-top: 15px;
  padding: 11px 0;
  border-top: 1px solid rgba(255, 248, 234, 0.1);
  border-bottom: 1px solid rgba(255, 248, 234, 0.1);
}

.best-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.48);
}

.stat-value {
  font-size: 15px;
  margin-top: 2px;
  color: #fff8ea;
}

.best-summary {
  margin-top: 11px;
  font-size: 11px;
  line-height: 1.65;
  color: rgba(255, 248, 234, 0.68);
}

.best-actions {
  display: flex;
  margin-top: 15px;
}

.best-actions .btn {
  flex: 1;
}

.best-ghost {
  margin-left: 9px;
  background: transparent;
  border-color: rgba(255, 248, 234, 0.22);
  color: #fff8ea;
}

.section-link {
  font-size: 11px;
  font-weight: 800;
  color: var(--amber-deep);
}

.history-card {
  padding: 15px;
}

.history-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.history-price {
  font-size: 25px;
  line-height: 1;
}

.history-label {
  font-size: 9px;
  color: var(--muted);
  margin-top: 3px;
}

.history-verdict {
  margin-top: 9px;
  font-size: 10px;
  color: var(--muted);
  line-height: 1.55;
}

@media (max-width: 520px) {
  .product-cover {
    width: 92px;
    height: 92px;
  }

  .product-title {
    font-size: 15px;
  }

  .best-price {
    font-size: 34px;
  }

  .best-actions .btn {
    font-size: 13px;
    padding: 0 10px;
  }
}
</style>
