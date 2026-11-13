<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { HomeResponse, PriceHistoryAnalysis } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import ProductCard from "../../components/ProductCard.vue";
import PriceSparkline from "../../components/PriceSparkline.vue";
import DataSourceBadge from "../../components/DataSourceBadge.vue";
import { formatMoney } from "../../utils/format";

const loading = ref(true);
const error = ref("");
const home = ref<HomeResponse | null>(null);
const signal = ref<PriceHistoryAnalysis | null>(null);
const keyword = ref("");

const featured = computed(() => home.value?.products || []);
const signalBadge = computed(() => {
  if (!signal.value) return "";
  if (signal.value.fake_drop) return "疑似先涨后降";
  if (signal.value.is_low) return "历史低位";
  return "价格观察";
});
const signalTone = computed(() => {
  if (!signal.value) return "";
  if (signal.value.fake_drop) return "chip-red";
  if (signal.value.is_low) return "chip-green";
  return "chip-amber";
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api.home();
    home.value = data;
    try {
      const history = await api.history("P001", 90);
      signal.value =
        history.series.find((item) => item.fake_drop) ||
        history.series.find((item) => item.is_low) ||
        history.series[0] ||
        null;
    } catch {
      signal.value = null;
    }
  } catch (err: any) {
    error.value = err?.message || "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

onShow(() => {
  load();
});

function search() {
  const value = keyword.value.trim();
  uni.navigateTo({
    url: `/pages/discover/discover?q=${encodeURIComponent(value)}`,
  });
}

function goSubsidy() {
  uni.navigateTo({ url: "/pages/subsidy/subsidy" });
}

function goCart() {
  uni.switchTab({ url: "/pages/cart/cart" });
}

function goDiscover() {
  uni.switchTab({ url: "/pages/discover/discover" });
}

function goSignal() {
  if (!signal.value) {
    goDiscover();
    return;
  }
  uni.navigateTo({
    url: `/pages/history/history?id=P001&platform=${signal.value.platform}`,
  });
}
</script>

<template>
  <view class="page-shell">
    <PageHeader
      title="价策"
      subtitle="把复杂的优惠，算成一条购买路径"
      @change="load"
    />

    <view class="hero fade-in">
      <view class="hero-orb orb-a"></view>
      <view class="hero-orb orb-b"></view>
      <view class="hero-head">
        <text class="hero-eyebrow">PRICE STRATEGY / DEMO</text>
        <DataSourceBadge source="mock" />
      </view>
      <view class="hero-title">别只看标价，</view>
      <view class="hero-title">看最终<text class="accent">到手价</text>。</view>
      <view class="hero-sub">
        店铺券、平台券、满减、国补、以旧换新和返利，放在一起算。
      </view>

      <view class="search-box">
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜商品，如：手机 / 耳机 / 洗衣机"
          placeholder-class="input-placeholder"
          confirm-type="search"
          @confirm="search"
        />
        <button class="btn btn-amber btn-sm search-btn" @click="search">
          算一算
        </button>
      </view>

      <view class="hero-chips">
        <text class="hero-chip">4 个平台</text>
        <text class="hero-chip">国补资格</text>
        <text class="hero-chip">以旧换新</text>
        <text class="hero-chip">可解释策略</text>
      </view>
    </view>

    <view v-if="error" class="notice notice--red mt-16">
      {{ error }}
      <view class="retry" @click="load">重新连接</view>
    </view>

    <view class="action-grid section">
      <view class="action-card card" @click="goSubsidy">
        <view class="action-icon amber">¥</view>
        <view class="action-title">国补计算器</view>
        <view class="action-desc">先看资格与金额</view>
      </view>
      <view class="action-card card" @click="goCart">
        <view class="action-icon ink">≡</view>
        <view class="action-title">购物车拆单</view>
        <view class="action-desc">几件商品怎么拆</view>
      </view>
      <view class="action-card card" @click="goSignal">
        <view class="action-icon green">↘</view>
        <view class="action-title">价格侦探</view>
        <view class="action-desc">识别先涨后降</view>
      </view>
      <view class="action-card card" @click="goDiscover">
        <view class="action-icon soft">→</view>
        <view class="action-title">全部比价</view>
        <view class="action-desc">12 件演示商品</view>
      </view>
    </view>

    <view v-if="signal" class="signal-card card section" @click="goSignal">
      <view class="signal-main">
        <view class="flex between">
          <text class="eyebrow">PRICE WATCH</text>
          <text class="chip" :class="signalTone">{{ signalBadge }}</text>
        </view>
        <view class="signal-title">
          {{ signal.platform_name }} · 90 天价格带
        </view>
        <view class="signal-price money">
          {{ formatMoney(signal.current_price) }}
        </view>
        <view class="signal-verdict">{{ signal.verdict }}</view>
        <view class="signal-meta">
          中位 {{ formatMoney(signal.median_price) }} · 最低
          {{ formatMoney(signal.min_price) }}
        </view>
      </view>
      <view class="signal-chart">
        <PriceSparkline :points="signal.points" :height="92" :max-bars="38" />
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">值得算一算</view>
          <view class="section-sub">标价最低的平台，未必到手最低</view>
        </view>
        <view class="section-link" @click="goDiscover">全部 →</view>
      </view>

      <view v-if="loading" class="grid-products">
        <view v-for="index in 4" :key="index" class="grid-item">
          <view class="card">
            <view class="skeleton" style="height: 168px; border-radius: 20px 20px 0 0"></view>
            <view style="padding: 14px">
              <view class="skeleton" style="height: 14px; width: 60%"></view>
              <view class="skeleton mt-12" style="height: 22px; width: 90%"></view>
              <view class="skeleton mt-12" style="height: 30px; width: 40%"></view>
            </view>
          </view>
        </view>
      </view>

      <view v-else-if="featured.length" class="grid-products">
        <view v-for="item in featured" :key="item.id" class="grid-item">
          <ProductCard :product="item" />
        </view>
      </view>

      <view v-else class="notice">
        暂无商品数据。请确认后端已启动，并在 backend 目录执行种子初始化。
      </view>
    </view>

    <view class="data-foot">
      <text>演示数据 · 不抓取平台页面 · 国补/平台规则为可配置示例</text>
      <text class="data-foot-sub">价策 v0.1 · FastAPI + uni-app</text>
    </view>
  </view>
</template>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  margin-top: 8px;
  padding: 24px;
  border-radius: 26px;
  background: radial-gradient(circle at 82% 8%, #29415e 0, #122238 42%, #0a1626 100%);
  color: #fff8ea;
  box-shadow: 0 18px 40px rgba(14, 27, 44, 0.22);
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(233, 162, 59, 0.2);
  pointer-events: none;
}

.orb-a {
  width: 220px;
  height: 220px;
  right: -80px;
  top: -90px;
}

.orb-b {
  width: 120px;
  height: 120px;
  right: 20px;
  bottom: -70px;
  background: rgba(233, 162, 59, 0.08);
}

.hero-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.hero-eyebrow {
  font-size: 9px;
  letter-spacing: 2.4px;
  font-weight: 800;
  color: rgba(255, 248, 234, 0.55);
}

.hero-title {
  position: relative;
  z-index: 1;
  margin-top: 4px;
  font-size: 31px;
  font-weight: 800;
  letter-spacing: -1.2px;
  line-height: 1.2;
}

.hero-title:first-of-type {
  margin-top: 18px;
}

.accent {
  color: var(--amber);
}

.hero-sub {
  position: relative;
  z-index: 1;
  margin-top: 10px;
  max-width: 520px;
  font-size: 12px;
  line-height: 1.65;
  color: rgba(255, 248, 234, 0.66);
}

.search-box {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  margin-top: 18px;
  padding: 5px;
  border-radius: 16px;
  background: #fffdf8;
}

.search-input {
  flex: 1;
  height: 38px;
  padding: 0 11px;
  font-size: 13px;
  color: var(--ink);
}

.search-btn {
  flex-shrink: 0;
  min-width: 82px;
}

.hero-chips {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  margin-top: 14px;
}

.hero-chip {
  padding: 4px 9px;
  border: 1px solid rgba(255, 248, 234, 0.16);
  border-radius: 999px;
  color: rgba(255, 248, 234, 0.66);
  font-size: 9px;
  margin: 0 7px 6px 0;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}

.action-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.action-card {
  width: 48.6%;
  padding: 15px;
  margin-bottom: 12px;
  border-radius: 18px;
}

.action-card:active {
  transform: scale(0.99);
}

.action-icon {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 800;
  margin-bottom: 9px;
}

.action-icon.amber {
  background: var(--amber-soft);
  color: var(--amber-deep);
}

.action-icon.ink {
  background: var(--ink);
  color: var(--amber);
}

.action-icon.green {
  background: var(--green-soft);
  color: var(--green);
}

.action-icon.soft {
  background: var(--paper-deep);
  color: var(--ink-soft);
}

.action-title {
  font-size: 14px;
  font-weight: 800;
}

.action-desc {
  font-size: 10px;
  color: var(--muted);
  margin-top: 2px;
}

.signal-card {
  display: flex;
  align-items: stretch;
  padding: 16px;
  border-radius: 20px;
}

.signal-main {
  flex: 1;
  min-width: 0;
  padding-right: 12px;
}

.signal-title {
  margin-top: 10px;
  font-size: 11px;
  color: var(--muted);
}

.signal-price {
  margin-top: 3px;
  font-size: 26px;
  line-height: 1.1;
}

.signal-verdict {
  margin-top: 5px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--ink-soft);
}

.signal-meta {
  margin-top: 5px;
  font-size: 9px;
  color: var(--muted-light);
}

.signal-chart {
  width: 42%;
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
}

.section-link {
  font-size: 11px;
  font-weight: 800;
  color: var(--amber-deep);
}

.data-foot {
  margin-top: 30px;
  padding: 18px 0 8px;
  border-top: 1px solid var(--line);
  text-align: center;
  font-size: 10px;
  line-height: 1.7;
  color: var(--muted-light);
}

.data-foot-sub {
  display: block;
  font-size: 9px;
  margin-top: 2px;
}

@media (max-width: 720px) {
  .hero {
    padding: 20px;
    border-radius: 22px;
  }

  .hero-title {
    font-size: 27px;
  }

  .action-card {
    width: 48%;
  }

  .signal-card {
    flex-direction: column;
  }

  .signal-chart {
    width: 100%;
    margin-top: 12px;
  }
}
</style>
