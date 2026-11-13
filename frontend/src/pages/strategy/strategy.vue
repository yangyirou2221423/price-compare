<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { StrategyResult } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import StrategyTimeline from "../../components/StrategyTimeline.vue";
import DataSourceBadge from "../../components/DataSourceBadge.vue";
import { formatMoney, platformTone, PLATFORM_META } from "../../utils/format";
import { useAppStore } from "../../stores/app";

const store = useAppStore();
const productId = ref("");
const strategy = ref<StrategyResult | null>(null);
const loading = ref(true);
const error = ref("");
const showAllRejections = ref(false);

const best = computed(() => (strategy.value ? strategy.value.best : null));
const alternatives = computed(() =>
  strategy.value ? strategy.value.results.filter((item) => item.platform !== strategy.value?.best_platform) : [],
);
const rejections = computed(() => (best.value ? best.value.rejected : []));
const visibleRejections = computed(() =>
  showAllRejections.value ? rejections.value : rejections.value.slice(0, 8),
);
const preferenceLabel = computed(() =>
  strategy.value?.preference === "net" ? "净价优先" : "实付优先",
);

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
    strategy.value = await api.strategy({
      product_id: productId.value,
      ...store.contextPayload,
    });
  } catch (err: any) {
    error.value = err?.message || "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

const playbookText = computed(() => {
  const current = strategy.value;
  if (!current) return "";
  const lines = [
    `价策 · ${current.product_title}`,
    `推荐平台：${current.best.platform_name}`,
    `预计实付：${formatMoney(current.best.final_price)}`,
    `购买条件：${store.contextLabel}`,
    "执行步骤：",
    ...current.best.applied.map(
      (step, index) =>
        `${index + 1}. ${step.name}（${step.is_net_benefit ? "+" : "-"}${formatMoney(step.amount)}）`,
    ),
    current.best.net_price < current.best.final_price
      ? `计入返利/赠品后净价：${formatMoney(current.best.net_price)}`
      : "",
    "数据为演示数据，最终以平台结算页为准。",
  ].filter(Boolean);
  return lines.join("\n");
});

function copyPlaybook() {
  uni.setClipboardData({
    data: playbookText.value,
    success: () => {
      uni.showToast({ title: "购买步骤已复制", icon: "none" });
    },
  });
}

function addToCart() {
  if (!strategy.value) return;
  store.addToCart({
    productId: strategy.value.product_id,
    title: strategy.value.product_title,
    image: strategy.value.product_image,
    category: strategy.value.product_category,
    unitPrice: strategy.value.best.final_price,
  });
  uni.showToast({ title: "已加入购物车", icon: "none" });
}

function platformMark(platform: string) {
  return PLATFORM_META[platform]?.mark || platform.slice(0, 1);
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      back
      title="购买策略"
      :subtitle="strategy?.product_title || '正在计算最优组合'"
      @change="load"
    />

    <view v-if="loading" class="loading-wrap">
      <view class="skeleton" style="height: 200px"></view>
      <view class="skeleton mt-16" style="height: 320px"></view>
    </view>

    <view v-else-if="error" class="notice notice--red mt-12">
      {{ error }}
      <view class="retry" @click="load">重新计算</view>
    </view>

    <template v-else-if="strategy && best">
      <view class="strategy-hero fade-in">
        <view class="hero-head">
          <view>
            <text class="hero-eyebrow">OPTIMAL PLAYBOOK</text>
            <view class="hero-platform">
              {{ best.platform_name }} · {{ best.shop_name }}
            </view>
          </view>
          <view class="chip chip-amber">
            {{ strategy.optimal ? "精确最优" : "启发式结果" }}
          </view>
        </view>

        <view class="hero-price-row">
          <view class="hero-price money">{{ formatMoney(best.final_price) }}</view>
          <view class="hero-save" v-if="best.promo_savings > 0.005">
            比标价省 {{ formatMoney(best.promo_savings) }}
          </view>
        </view>
        <view v-if="best.trade_in_value > 0.005" class="trade-line">
          其中旧机抵扣 {{ formatMoney(best.trade_in_value) }}，实际支付金额已扣除
        </view>

        <view class="hero-summary">{{ strategy.summary }}</view>

        <view class="hero-meta">
          <view class="meta-item">
            <text class="meta-label">偏好</text>
            <text class="meta-value">{{ preferenceLabel }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">步骤</text>
            <text class="meta-value">{{ best.applied.length }} 步</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">引擎</text>
            <text class="meta-value">{{ strategy.engine_version }}</text>
          </view>
        </view>

        <view class="hero-foot">
          <DataSourceBadge :source="strategy.data_source" />
          <text class="hero-region">{{ store.contextLabel }}</text>
        </view>
      </view>

      <view class="section">
        <StrategyTimeline :result="best" />
      </view>

      <view class="section">
        <view class="section-head">
          <view>
            <view class="section-title">备选平台</view>
            <view class="section-sub">为什么不是它们</view>
          </view>
        </view>
        <view v-if="alternatives.length" class="alt-list card">
          <view
            v-for="item in alternatives"
            :key="item.offer_id"
            class="alt-row"
          >
            <view class="alt-left">
              <view class="alt-mark" :class="`mark-${platformTone(item.platform)}`">
                {{ platformMark(item.platform) }}
              </view>
              <view class="alt-info">
                <view class="alt-name">{{ item.platform_name }}</view>
                <view class="alt-note">{{ item.note || "当前条件下不是最优" }}</view>
              </view>
            </view>
            <view class="alt-price money">{{ formatMoney(item.final_price) }}</view>
          </view>
        </view>
        <view v-else class="notice">只有一个平台可选。</view>
      </view>

      <view class="section">
        <view class="section-head">
          <view>
            <view class="section-title">没采用的优惠</view>
            <view class="section-sub">不是漏算，而是不划算或不符合资格</view>
          </view>
        </view>
        <view v-if="rejections.length" class="reject-list card">
          <view
            v-for="item in visibleRejections"
            :key="item.benefit_id"
            class="reject-row"
          >
            <view class="reject-dot"></view>
            <view class="reject-info">
              <text class="reject-name">{{ item.name }}</text>
              <text class="reject-reason">{{ item.reason }}</text>
            </view>
          </view>
          <view
            v-if="rejections.length > 8"
            class="show-more"
            @click="showAllRejections = !showAllRejections"
          >
            {{ showAllRejections ? "收起" : `展开全部 ${rejections.length} 项` }}
          </view>
        </view>
        <view v-else class="notice">所有匹配到的优惠都已经纳入最优组合。</view>
      </view>

      <view class="section">
        <view class="assumption-card card">
          <view class="assumption-title">计算假设</view>
          <view
            v-for="(item, index) in strategy.assumptions"
            :key="index"
            class="assumption-row"
          >
            <text class="assumption-index">{{ index + 1 }}</text>
            <text class="assumption-text">{{ item }}</text>
          </view>
        </view>
      </view>

      <view class="action-card card">
        <view class="action-copy">
          <view class="action-title">把这套方案带走</view>
          <view class="action-desc">复制步骤，按顺序领券、凑单、申请补贴。</view>
        </view>
        <button class="btn btn-primary" @click="copyPlaybook">复制购买步骤</button>
        <button class="btn btn-ghost mt-8" @click="addToCart">加入购物车</button>
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

.strategy-hero {
  padding: 20px;
  border-radius: 22px;
  background: radial-gradient(circle at 88% 0%, #2b4564 0, #14263b 42%, #0b1728 100%);
  color: #fff8ea;
  box-shadow: 0 18px 36px rgba(14, 27, 44, 0.2);
}

.hero-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-eyebrow {
  display: block;
  font-size: 8px;
  letter-spacing: 2.2px;
  font-weight: 800;
  color: rgba(255, 248, 234, 0.48);
}

.hero-platform {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 248, 234, 0.9);
  margin-top: 2px;
}

.hero-price-row {
  display: flex;
  align-items: center;
  margin-top: 15px;
}

.hero-price {
  font-size: 42px;
  line-height: 1;
  color: var(--amber);
}

.hero-save {
  margin-left: 10px;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(233, 162, 59, 0.16);
  color: var(--amber);
  font-size: 10px;
  font-weight: 800;
}

.trade-line {
  margin-top: 6px;
  font-size: 10px;
  color: rgba(255, 248, 234, 0.55);
}

.hero-summary {
  margin-top: 12px;
  font-size: 11px;
  line-height: 1.65;
  color: rgba(255, 248, 234, 0.7);
}

.hero-meta {
  display: flex;
  margin-top: 14px;
  padding: 10px 0;
  border-top: 1px solid rgba(255, 248, 234, 0.1);
  border-bottom: 1px solid rgba(255, 248, 234, 0.1);
}

.meta-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.45);
}

.meta-value {
  font-size: 12px;
  font-weight: 700;
  margin-top: 2px;
}

.hero-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 11px;
}

.hero-region {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.45);
  max-width: 60%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alt-list {
  padding: 4px 15px;
}

.alt-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 0;
  border-bottom: 1px solid var(--line);
}

.alt-row:last-child {
  border-bottom: 0;
}

.alt-left {
  display: flex;
  align-items: center;
  min-width: 0;
}

.alt-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  margin-right: 9px;
  flex-shrink: 0;
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
  background: var(--ink);
}

.alt-info {
  min-width: 0;
}

.alt-name {
  font-size: 13px;
  font-weight: 700;
}

.alt-note {
  font-size: 9px;
  color: var(--muted);
  line-height: 1.4;
  max-width: 360px;
}

.alt-price {
  font-size: 16px;
  margin-left: 10px;
  flex-shrink: 0;
}

.reject-list {
  padding: 4px 15px;
}

.reject-row {
  display: flex;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}

.reject-row:last-child {
  border-bottom: 0;
}

.reject-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--red);
  margin: 6px 9px 0 0;
  flex-shrink: 0;
}

.reject-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.reject-name {
  font-size: 12px;
  font-weight: 700;
}

.reject-reason {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.5;
  margin-top: 1px;
}

.show-more {
  padding: 10px 0;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--amber-deep);
}

.assumption-card {
  padding: 15px;
}

.assumption-title {
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 8px;
}

.assumption-row {
  display: flex;
  align-items: flex-start;
  padding: 3px 0;
}

.assumption-index {
  width: 17px;
  height: 17px;
  border-radius: 5px;
  background: var(--paper-deep);
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 2px 8px 0 0;
  flex-shrink: 0;
}

.assumption-text {
  flex: 1;
  font-size: 10px;
  line-height: 1.6;
  color: var(--muted);
}

.action-card {
  margin-top: 24px;
  padding: 16px;
}

.action-title {
  font-size: 15px;
  font-weight: 800;
}

.action-desc {
  font-size: 10px;
  color: var(--muted);
  margin: 3px 0 12px;
  line-height: 1.5;
}

@media (max-width: 520px) {
  .hero-price {
    font-size: 34px;
  }

  .strategy-hero {
    padding: 17px;
  }
}
</style>
