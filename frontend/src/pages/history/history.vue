<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { HistoryResponse } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import PriceSparkline from "../../components/PriceSparkline.vue";
import EmptyState from "../../components/EmptyState.vue";
import {
  formatMoney,
  formatPercent,
  trendText,
} from "../../utils/format";

const productId = ref("");
const initialPlatform = ref("");
const data = ref<HistoryResponse | null>(null);
const activePlatform = ref("");
const loading = ref(true);
const error = ref("");

const analysis = computed(() => {
  if (!data.value) return null;
  return (
    data.value.series.find((item) => item.platform === activePlatform.value) ||
    data.value.series[0] ||
    null
  );
});

const badge = computed(() => {
  if (!analysis.value) return "";
  if (analysis.value.fake_drop) return "疑似先涨后降";
  if (analysis.value.is_low) return "历史低位";
  return "常规区间";
});

const badgeClass = computed(() => {
  if (!analysis.value) return "";
  if (analysis.value.fake_drop) return "chip-red";
  if (analysis.value.is_low) return "chip-green";
  return "chip-amber";
});

onLoad((options) => {
  productId.value = String(options?.id || "");
  initialPlatform.value = String(options?.platform || "");
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
    const response = await api.history(productId.value, 90);
    data.value = response;
    const exists = response.series.some(
      (item) => item.platform === initialPlatform.value,
    );
    activePlatform.value = exists
      ? initialPlatform.value
      : response.series[0]?.platform || "";
  } catch (err: any) {
    error.value = err?.message || "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function selectPlatform(platform: string) {
  activePlatform.value = platform;
}

function goCompare() {
  uni.navigateTo({
    url: `/pages/compare/compare?id=${encodeURIComponent(productId.value)}`,
  });
}

function trendClass(value: number) {
  if (value < -0.005) return "down";
  if (value > 0.005) return "up";
  return "";
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      back
      title="价格走势"
      :subtitle="data?.product_title || '近 90 天价格带'"
      @change="load"
    />

    <view v-if="loading" class="loading-wrap">
      <view class="skeleton" style="height: 280px"></view>
      <view class="skeleton mt-16" style="height: 160px"></view>
    </view>

    <view v-else-if="error" class="notice notice--red mt-12">
      {{ error }}
      <view class="retry" @click="load">重新加载</view>
    </view>

    <template v-else-if="data && analysis">
      <view class="platform-tabs">
        <view
          v-for="item in data.series"
          :key="item.platform"
          class="chip"
          :class="{ 'chip-active': activePlatform === item.platform }"
          @click="selectPlatform(item.platform)"
        >
          {{ item.platform_name }}
        </view>
      </view>

      <view class="history-hero card fade-in">
        <view class="hero-top">
          <view>
            <view class="hero-label">当前价格</view>
            <view class="hero-price money">{{ formatMoney(analysis.current_price) }}</view>
          </view>
          <view class="chip" :class="badgeClass">{{ badge }}</view>
        </view>
        <view class="verdict">{{ analysis.verdict }}</view>

        <view class="chart-wrap">
          <PriceSparkline :points="analysis.points" :height="132" :max-bars="48" />
        </view>

        <view class="stats">
          <view class="stat">
            <text class="stat-label">90 天中位价</text>
            <text class="stat-value money">{{ formatMoney(analysis.median_price) }}</text>
          </view>
          <view class="stat">
            <text class="stat-label">90 天最低</text>
            <text class="stat-value money">{{ formatMoney(analysis.lowest_90d) }}</text>
          </view>
          <view class="stat">
            <text class="stat-label">30 天最低</text>
            <text class="stat-value money">{{ formatMoney(analysis.lowest_30d) }}</text>
          </view>
          <view class="stat">
            <text class="stat-label">历史最高</text>
            <text class="stat-value money">{{ formatMoney(analysis.max_price) }}</text>
          </view>
          <view class="stat">
            <text class="stat-label">当前分位</text>
            <text class="stat-value">{{ formatPercent(analysis.percentile) }}</text>
          </view>
          <view class="stat">
            <text class="stat-label">7 天变化</text>
            <text class="stat-value" :class="trendClass(analysis.trend_7d)">
              {{ trendText(analysis.trend_7d) }}
            </text>
          </view>
        </view>
      </view>

      <view v-if="analysis.fake_drop" class="notice notice--red mt-12">
        价格侦探提示：近两周出现过明显抬价，随后又降到当前水平。建议对照历史价格，不要只看“直降”标签。
      </view>
      <view v-else-if="analysis.is_low" class="notice notice--amber mt-12">
        当前价格处于近 90 天低位。若刚需，可以考虑入手；不着急也可以设置降价提醒。
      </view>

      <view class="notice mt-12">
        {{ data.data_note }} 当前分位越低，说明当前价格越接近历史低位。
      </view>

      <button class="btn btn-primary btn-block mt-16" @click="goCompare">
        返回比价详情
      </button>
    </template>

    <EmptyState
      v-else
      class="mt-16"
      icon="↘"
      title="暂无价格历史"
      description="该商品还没有足够的演示价格数据。"
      action-text="返回比价"
      @action="goCompare"
    />
  </view>
</template>

<style scoped>
.loading-wrap {
  margin-top: 10px;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}

.platform-tabs {
  display: flex;
  flex-wrap: wrap;
  margin: 8px 0 12px;
}

.platform-tabs .chip {
  margin: 0 7px 7px 0;
  font-size: 11px;
}

.history-hero {
  padding: 18px;
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-label {
  font-size: 10px;
  color: var(--muted);
}

.hero-price {
  margin-top: 2px;
  font-size: 34px;
  line-height: 1;
}

.verdict {
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.6;
  color: var(--ink-soft);
}

.chart-wrap {
  margin-top: 18px;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  margin-top: 17px;
  padding-top: 13px;
  border-top: 1px dashed var(--line);
}

.stat {
  width: 33.33%;
  padding: 6px 4px 6px 0;
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 9px;
  color: var(--muted);
}

.stat-value {
  margin-top: 2px;
  font-size: 13px;
  font-weight: 800;
}

.stat-value.down {
  color: var(--green);
}

.stat-value.up {
  color: var(--red);
}

@media (max-width: 520px) {
  .stat {
    width: 50%;
  }

  .hero-price {
    font-size: 30px;
  }
}
</style>
