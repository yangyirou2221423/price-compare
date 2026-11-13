<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { CartResponse, FillerCandidate } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import EmptyState from "../../components/EmptyState.vue";
import { formatMoney, platformTone, PLATFORM_META } from "../../utils/format";
import { useAppStore } from "../../stores/app";

const store = useAppStore();
const result = ref<CartResponse | null>(null);
const loading = ref(false);
const error = ref("");
const lastOptimized = ref("");
let timer: ReturnType<typeof setTimeout> | null = null;
let requestId = 0;

const hasItems = computed(() => store.cartItems.length > 0);
const itemsPayload = computed(() =>
  store.cartItems.map((item) => ({
    product_id: item.productId,
    quantity: item.quantity,
  })),
);
const signature = computed(() =>
  JSON.stringify(
    store.cartItems.map((item) => [item.productId, item.quantity] as const),
  ),
);
const baselineLabel = computed(() => {
  const cart = result.value?.cart;
  if (!cart) return "";
  if (cart.baseline_platform === "mixed") return "单平台方案";
  return PLATFORM_META[cart.baseline_platform]?.label || cart.baseline_platform;
});

onShow(() => {
  if (!hasItems.value) {
    result.value = null;
    return;
  }
  if (!result.value || signature.value !== lastOptimized.value) {
    optimize();
  }
});

watch(signature, () => {
  if (!hasItems.value) {
    result.value = null;
    lastOptimized.value = "";
    return;
  }
  if (signature.value === lastOptimized.value) return;
  result.value = null;
  scheduleOptimize();
});

async function optimize() {
  if (!hasItems.value) return;
  const currentRequest = ++requestId;
  const requestedSignature = signature.value;
  loading.value = true;
  error.value = "";
  try {
    const response = await api.cart({
      items: itemsPayload.value,
      ...store.contextPayload,
      include_fillers: true,
    });
    if (currentRequest !== requestId) return;
    result.value = response;
    lastOptimized.value = requestedSignature;
  } catch (err: any) {
    if (currentRequest !== requestId) return;
    error.value = err?.message || "计算失败，请稍后重试";
    result.value = null;
  } finally {
    if (currentRequest === requestId) loading.value = false;
  }
}

function onContextChange() {
  result.value = null;
  lastOptimized.value = "";
  if (hasItems.value) optimize();
}

function scheduleOptimize() {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    timer = null;
    optimize();
  }, 350);
}

function changeQuantity(productId: string, delta: number) {
  const item = store.cartItems.find((entry) => entry.productId === productId);
  if (!item) return;
  store.updateQuantity(productId, item.quantity + delta);
  result.value = null;
  scheduleOptimize();
}

function removeItem(productId: string) {
  store.removeFromCart(productId);
  result.value = null;
  lastOptimized.value = "";
  if (hasItems.value) {
    scheduleOptimize();
  }
}

function clearAll() {
  uni.showModal({
    title: "清空购物车",
    content: "只会清空本地演示购物车，不会影响任何平台账号。",
    success: (res) => {
      if (!res.confirm) return;
      store.clearCart();
      result.value = null;
      lastOptimized.value = "";
    },
  });
}

function addFiller(candidate: FillerCandidate) {
  store.addFiller(candidate);
  uni.showToast({ title: "已加购，重新计算中", icon: "none" });
  optimize();
}

function goDiscover() {
  uni.switchTab({ url: "/pages/discover/discover" });
}

function loadDemoCart() {
  store.addToCart({
    productId: "P005",
    title: "云鲸 扫地机器人 J6",
    image: "/static/products/p005.png",
    category: "清洁电器",
    unitPrice: 2920,
  });
  store.addToCart({
    productId: "P003",
    title: "声阔 Pods Pro 主动降噪耳机",
    image: "/static/products/p003.png",
    category: "耳机",
    unitPrice: 1199,
  });
  store.addToCart({
    productId: "P006",
    title: "极光 智能投影仪 P3",
    image: "/static/products/p006.png",
    category: "影音",
    unitPrice: 2899,
  });
  uni.showToast({ title: "已载入示例购物车", icon: "none" });
  optimize();
}

function openProduct(productId: string) {
  uni.navigateTo({
    url: `/pages/compare/compare?id=${encodeURIComponent(productId)}`,
  });
}

function platformMark(platform: string) {
  return PLATFORM_META[platform]?.mark || platform.slice(0, 1);
}

function thresholdHint(order: any): string {
  const rejection = order.order_rejected?.find(
    (item: any) => item.reason_code === "threshold",
  );
  return rejection?.reason || "";
}

function fillerTone(value: number): string {
  return value <= 0 ? "chip-green" : "chip-amber";
}

function netIncreaseLabel(value: number): string {
  if (value > 0.005) return `+${formatMoney(value)}`;
  if (value < -0.005) return `-${formatMoney(Math.abs(value))}`;
  return formatMoney(0);
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      title="购物车"
      subtitle="多件商品，拆成最省的订单"
      @change="onContextChange"
    />

    <EmptyState
      v-if="!hasItems"
      class="mt-16"
      icon="≡"
      title="购物车还是空的"
      description="从比价详情页加入商品，或一键载入三件商品的跨平台拆单示例。"
      action-text="去挑商品"
      @action="goDiscover"
    />

    <button
      v-if="!hasItems"
      class="btn btn-ghost btn-block mt-12"
      @click="loadDemoCart"
    >
      载入示例购物车（3 件）
    </button>

    <template v-else>
      <view class="cart-card card">
        <view class="cart-head">
          <view>
            <view class="cart-title">待算商品</view>
            <view class="cart-sub">{{ store.cartCount }} 件 · 页面价 {{ formatMoney(store.cartSubtotal) }}</view>
          </view>
          <view class="clear" @click="clearAll">清空</view>
        </view>

        <view v-for="item in store.cartItems" :key="item.productId" class="cart-row">
          <image
            class="cart-img"
            :src="item.image"
            mode="aspectFill"
            @click="openProduct(item.productId)"
          />
          <view class="cart-info" @click="openProduct(item.productId)">
            <view class="cart-name">{{ item.title }}</view>
            <view class="cart-unit">
              页面价 <text class="money">{{ formatMoney(item.unitPrice) }}</text>
            </view>
          </view>
          <view class="cart-actions">
            <view class="stepper">
              <text class="step-btn" @click="changeQuantity(item.productId, -1)">−</text>
              <text class="step-value">{{ item.quantity }}</text>
              <text class="step-btn" @click="changeQuantity(item.productId, 1)">＋</text>
            </view>
            <view class="remove" @click="removeItem(item.productId)">移除</view>
          </view>
        </view>

        <button class="btn btn-primary btn-block mt-12" :disabled="loading" @click="optimize">
          {{ loading ? "正在计算…" : "计算最优拆单" }}
        </button>
        <view class="cart-tip">同一平台商品合并为一单，平台券/满减按订单小计计算。</view>
      </view>

      <view v-if="error" class="notice notice--red mt-12">
        {{ error }}
        <view class="retry" @click="optimize">重新计算</view>
      </view>

      <view v-if="loading && !result" class="loading-wrap">
        <view class="skeleton" style="height: 150px"></view>
        <view class="skeleton mt-16" style="height: 220px"></view>
      </view>

      <template v-if="result && !loading">
        <view class="summary-hero fade-in">
          <view class="summary-head">
            <view>
              <text class="summary-eyebrow">SPLIT OPTIMIZER</text>
              <view class="summary-title">最优拆单</view>
            </view>
            <view class="chip chip-amber">
              {{ result.cart.optimal ? "精确最优" : "启发式" }}
            </view>
          </view>
          <view class="summary-price money">
            {{ formatMoney(result.cart.total_payment) }}
          </view>
          <view class="summary-save" v-if="result.cart.savings_vs_baseline > 0.005">
            比全部在{{ baselineLabel }}下单省
            {{ formatMoney(result.cart.savings_vs_baseline) }}
          </view>
          <view class="summary-save" v-else>
            当前拆单没有比单平台方案更省
          </view>

          <view class="summary-stats">
            <view class="summary-stat">
              <text class="summary-label">单平台基线</text>
              <text class="summary-value money">{{ formatMoney(result.cart.baseline_payment) }}</text>
            </view>
            <view class="summary-stat">
              <text class="summary-label">拆成</text>
              <text class="summary-value">{{ result.cart.orders.length }} 单</text>
            </view>
            <view class="summary-stat">
              <text class="summary-label">计入返利净价</text>
              <text class="summary-value money">{{ formatMoney(result.cart.total_net) }}</text>
            </view>
          </view>
          <view class="summary-summary">
            {{ result.cart.notes[0] }}
          </view>
        </view>

        <view class="section">
          <view class="section-head">
            <view>
              <view class="section-title">拆单方案</view>
              <view class="section-sub">每单的平台券和满减独立计算</view>
            </view>
            <view class="recalc" @click="optimize">重新计算</view>
          </view>

          <view v-for="order in result.cart.orders" :key="order.platform" class="order-card card">
            <view class="order-head">
              <view class="order-platform">
                <view class="order-mark" :class="`mark-${platformTone(order.platform)}`">
                  {{ platformMark(order.platform) }}
                </view>
                <view>
                  <view class="order-name">{{ order.platform_name }}</view>
                  <view class="order-meta">
                    商品 {{ order.lines.length }} 件 · 标价 {{ formatMoney(order.list_subtotal) }}
                  </view>
                </view>
              </view>
              <view class="order-price money">{{ formatMoney(order.final_price) }}</view>
            </view>

            <view class="order-lines">
              <view v-for="line in order.lines" :key="line.product_id" class="order-line">
                <view class="line-info">
                  <text class="line-title">{{ line.title }}</text>
                  <text class="line-qty">× {{ line.quantity }}</text>
                </view>
                <text class="line-price money">{{ formatMoney(line.line_final) }}</text>
              </view>
            </view>

            <view v-if="order.order_applied.length" class="order-benefits">
              <view
                v-for="benefit in order.order_applied"
                :key="benefit.benefit_id"
                class="order-benefit"
              >
                <text>{{ benefit.name }}</text>
                <text class="order-benefit-amount" :class="{ net: benefit.is_net_benefit }">
                  {{ benefit.is_net_benefit ? "+" : "-" }}{{ formatMoney(benefit.amount) }}
                </text>
              </view>
            </view>

            <view v-if="thresholdHint(order)" class="order-hint">
              {{ thresholdHint(order) }}
            </view>

            <view class="order-foot">
              <text class="order-discount" v-if="order.order_discount_total > 0.005">
                本单优惠 {{ formatMoney(order.order_discount_total) }}
              </text>
              <text class="order-discount" v-else>本单无额外优惠</text>
              <text class="order-final">实付 <text class="money">{{ formatMoney(order.final_price) }}</text></text>
            </view>
          </view>
        </view>

        <view v-if="result.fillers.length" class="section">
          <view class="section-head">
            <view>
              <view class="section-title">凑单机会</view>
              <view class="section-sub">加购后可能反而更省</view>
            </view>
          </view>

          <view v-for="filler in result.fillers" :key="filler.benefit_id + filler.platform" class="filler-card card">
            <view class="filler-head">
              <view>
                <view class="filler-title">
                  {{ filler.platform_name }} · 还差 {{ formatMoney(filler.gap) }}
                </view>
                <view class="filler-sub">达到「{{ filler.benefit_name }}」门槛</view>
              </view>
              <view class="chip chip-amber">凑单</view>
            </view>

            <view v-for="candidate in filler.candidates" :key="candidate.product_id" class="filler-row">
              <image class="filler-img" :src="candidate.image" mode="aspectFill" />
              <view class="filler-info">
                <view class="filler-name">{{ candidate.title }}</view>
                <view class="filler-reason">{{ candidate.reason }}</view>
              </view>
              <view class="filler-right">
                <view class="chip" :class="fillerTone(candidate.net_increase)">
                  净增 {{ netIncreaseLabel(candidate.net_increase) }}
                </view>
                <button class="btn btn-amber btn-sm mt-8" @click="addFiller(candidate)">
                  加购
                </button>
              </view>
            </view>

            <view class="filler-warning">{{ filler.warning }}</view>
          </view>
        </view>

        <view class="notes-card card">
          <view class="notes-title">计算说明</view>
          <view v-for="(note, index) in result.cart.notes" :key="index" class="note-row">
            <text class="note-dot">·</text>
            <text class="note-text">{{ note }}</text>
          </view>
        </view>
      </template>
    </template>
  </view>
</template>

<style scoped>
.cart-card {
  margin-top: 8px;
  padding: 16px;
}

.cart-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10px;
}

.cart-title {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.4px;
}

.cart-sub {
  font-size: 10px;
  color: var(--muted);
  margin-top: 2px;
}

.clear {
  font-size: 11px;
  color: var(--muted);
  padding: 3px 0;
}

.cart-row {
  display: flex;
  align-items: center;
  padding: 11px 0;
  border-top: 1px solid var(--line);
}

.cart-img {
  width: 66px;
  height: 66px;
  border-radius: 12px;
  flex-shrink: 0;
  background: var(--paper-deep);
}

.cart-info {
  flex: 1;
  min-width: 0;
  padding: 0 10px;
}

.cart-name {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cart-unit {
  margin-top: 3px;
  font-size: 10px;
  color: var(--muted);
}

.cart-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.stepper {
  display: flex;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 9px;
  overflow: hidden;
}

.step-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper);
  font-size: 15px;
  color: var(--ink-soft);
}

.step-value {
  width: 26px;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
}

.remove {
  margin-top: 5px;
  font-size: 9px;
  color: var(--muted-light);
}

.cart-tip {
  margin-top: 9px;
  font-size: 9px;
  color: var(--muted-light);
  text-align: center;
  line-height: 1.5;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}

.loading-wrap {
  margin-top: 16px;
}

.summary-hero {
  margin-top: 18px;
  padding: 19px;
  border-radius: 22px;
  background: radial-gradient(circle at 88% 0%, #2b4564 0, #14263b 42%, #0b1728 100%);
  color: #fff8ea;
  box-shadow: 0 18px 36px rgba(14, 27, 44, 0.2);
}

.summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.summary-eyebrow {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 2px;
  color: rgba(255, 248, 234, 0.48);
}

.summary-title {
  font-size: 18px;
  font-weight: 800;
  margin-top: 1px;
}

.summary-price {
  margin-top: 12px;
  font-size: 40px;
  line-height: 1;
  color: var(--amber);
}

.summary-save {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(255, 248, 234, 0.68);
}

.summary-stats {
  display: flex;
  margin-top: 14px;
  padding: 10px 0;
  border-top: 1px solid rgba(255, 248, 234, 0.1);
  border-bottom: 1px solid rgba(255, 248, 234, 0.1);
}

.summary-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.summary-label {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.45);
}

.summary-value {
  font-size: 13px;
  font-weight: 700;
  margin-top: 2px;
}

.summary-summary {
  margin-top: 10px;
  font-size: 10px;
  line-height: 1.6;
  color: rgba(255, 248, 234, 0.62);
}

.recalc {
  font-size: 11px;
  font-weight: 800;
  color: var(--amber-deep);
}

.order-card {
  padding: 15px;
  margin-bottom: 12px;
}

.order-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.order-platform {
  display: flex;
  align-items: center;
}

.order-mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 14px;
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

.order-name {
  font-size: 14px;
  font-weight: 800;
}

.order-meta {
  font-size: 9px;
  color: var(--muted);
  margin-top: 1px;
}

.order-price {
  font-size: 21px;
  line-height: 1;
  flex-shrink: 0;
  margin-left: 10px;
}

.order-lines {
  margin-top: 10px;
  padding: 9px 11px;
  border-radius: 11px;
  background: var(--paper);
}

.order-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 0;
}

.line-info {
  min-width: 0;
  display: flex;
  align-items: center;
}

.line-title {
  font-size: 10px;
  color: var(--ink-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.line-qty {
  margin-left: 5px;
  font-size: 9px;
  color: var(--muted);
}

.line-price {
  font-size: 11px;
  flex-shrink: 0;
}

.order-benefits {
  display: flex;
  flex-wrap: wrap;
  margin-top: 8px;
}

.order-benefit {
  display: flex;
  align-items: center;
  padding: 4px 7px;
  border-radius: 7px;
  background: #fbf3e4;
  font-size: 9px;
  color: #6f5a33;
  margin: 0 6px 5px 0;
}

.order-benefit-amount {
  margin-left: 4px;
  font-weight: 800;
  color: var(--green);
}

.order-benefit-amount.net {
  color: var(--amber-deep);
}

.order-hint {
  margin-top: 4px;
  font-size: 9px;
  color: var(--amber-deep);
  background: #fdf3df;
  border-radius: 8px;
  padding: 6px 8px;
  line-height: 1.45;
}

.order-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 9px;
  padding-top: 9px;
  border-top: 1px dashed var(--line);
}

.order-discount {
  font-size: 10px;
  color: var(--muted);
}

.order-final {
  font-size: 11px;
  color: var(--ink-soft);
}

.filler-card {
  padding: 15px;
  margin-bottom: 12px;
}

.filler-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 9px;
}

.filler-title {
  font-size: 14px;
  font-weight: 800;
}

.filler-sub {
  font-size: 9px;
  color: var(--muted);
  margin-top: 1px;
}

.filler-row {
  display: flex;
  align-items: center;
  padding: 9px 0;
  border-top: 1px solid var(--line);
}

.filler-img {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  flex-shrink: 0;
  background: var(--paper-deep);
}

.filler-info {
  flex: 1;
  min-width: 0;
  padding: 0 9px;
}

.filler-name {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
}

.filler-reason {
  font-size: 9px;
  color: var(--muted);
  margin-top: 2px;
  line-height: 1.4;
}

.filler-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.filler-warning {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 9px;
  background: var(--paper);
  color: var(--muted);
  font-size: 9px;
  line-height: 1.5;
}

.notes-card {
  margin-top: 18px;
  padding: 15px;
}

.notes-title {
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 6px;
}

.note-row {
  display: flex;
  align-items: flex-start;
  padding: 2px 0;
}

.note-dot {
  color: var(--amber-deep);
  margin-right: 5px;
}

.note-text {
  flex: 1;
  font-size: 10px;
  line-height: 1.55;
  color: var(--muted);
}

@media (max-width: 520px) {
  .summary-price {
    font-size: 34px;
  }

  .line-title {
    max-width: 160px;
  }
}
</style>
