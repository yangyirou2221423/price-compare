<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { ProductCard, SubmissionResponse } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import ContextSheet from "../../components/ContextSheet.vue";
import {
  formatMoney,
  platformLabel,
} from "../../utils/format";
import { useAppStore } from "../../stores/app";

const PLATFORMS = [
  { id: "jd", name: "京东" },
  { id: "taobao", name: "淘宝" },
  { id: "pdd", name: "拼多多" },
  { id: "douyin", name: "抖音" },
];

const store = useAppStore();
const showContext = ref(false);
const submissions = ref<SubmissionResponse[]>([]);
const products = ref<ProductCard[]>([]);
const loadingSubmissions = ref(false);
const loadingProducts = ref(false);

const productIndex = ref(0);
const platformIndex = ref(0);
const priceInput = ref("");
const note = ref("");
const submitting = ref(false);

const preferenceLabel = computed(() =>
  store.preference === "net" ? "净价最低（含返利）" : "实付最低",
);
const selectedProduct = computed(() => products.value[productIndex.value] || null);
const selectedPlatform = computed(
  () => PLATFORMS[platformIndex.value] || PLATFORMS[0],
);

onShow(() => {
  loadSubmissions();
  loadProducts();
});

async function loadSubmissions() {
  loadingSubmissions.value = true;
  try {
    const response = await api.submissions();
    submissions.value = response.submissions;
  } catch {
    submissions.value = [];
  } finally {
    loadingSubmissions.value = false;
  }
}

async function loadProducts() {
  if (products.value.length) return;
  loadingProducts.value = true;
  try {
    const response = await api.products({ limit: 100 });
    products.value = response.products;
  } catch {
    products.value = [];
  } finally {
    loadingProducts.value = false;
  }
}

function onProductChange(event: any) {
  productIndex.value = Number(event?.detail?.value ?? 0);
}

function onPlatformChange(event: any) {
  platformIndex.value = Number(event?.detail?.value ?? 0);
}

async function submitPrice() {
  const product = selectedProduct.value;
  const price = Number(priceInput.value);
  if (!product) {
    uni.showToast({ title: "请选择商品", icon: "none" });
    return;
  }
  if (!Number.isFinite(price) || price <= 0) {
    uni.showToast({ title: "请输入有效价格", icon: "none" });
    return;
  }
  submitting.value = true;
  try {
    await api.submitPrice({
      product_id: product.id,
      platform: selectedPlatform.value.id,
      price,
      note: note.value.trim(),
    });
    priceInput.value = "";
    note.value = "";
    uni.showToast({ title: "提交成功", icon: "none" });
    await loadSubmissions();
  } catch (err: any) {
    uni.showToast({ title: err?.message || "提交失败", icon: "none" });
  } finally {
    submitting.value = false;
  }
}

function openProduct(productId: string) {
  uni.navigateTo({
    url: `/pages/compare/compare?id=${encodeURIComponent(productId)}`,
  });
}

function removeFavorite(productId: string) {
  const item = store.favorites.find((favorite) => favorite.id === productId);
  if (item) store.toggleFavorite(item);
}

function goDiscover() {
  uni.switchTab({ url: "/pages/discover/discover" });
}

function resetDemo() {
  uni.showModal({
    title: "重置演示数据",
    content: "会清空本地购物车、收藏和购买条件，但不会删除已提交的价格。",
    success: (res) => {
      if (!res.confirm) return;
      store.resetAll();
      uni.showToast({ title: "已重置", icon: "none" });
    },
  });
}

function submissionLabel(item: SubmissionResponse) {
  const parts = item.message.split(" · ");
  if (parts.length === 2) {
    return `${platformLabel(parts[0])} · ${parts[1]}`;
  }
  return item.message;
}

async function deleteSubmission(item: SubmissionResponse) {
  try {
    await api.deleteSubmission(item.id);
    submissions.value = submissions.value.filter((entry) => entry.id !== item.id);
    uni.showToast({ title: "已删除", icon: "none" });
  } catch (err: any) {
    uni.showToast({ title: err?.message || "删除失败", icon: "none" });
  }
}

function dateLabel(value: string) {
  return value ? value.slice(0, 16).replace("T", " ") : "";
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      title="我的"
      subtitle="购买条件、收藏与演示数据"
    />

    <view class="condition-card card fade-in">
      <view class="card-head">
        <view>
          <view class="card-title">购买条件</view>
          <view class="card-sub">会直接影响最优平台与拆单结果</view>
        </view>
        <view class="edit" @click="showContext = true">修改</view>
      </view>
      <view class="condition-grid">
        <view class="condition-item">
          <text class="condition-label">地区</text>
          <text class="condition-value">{{ store.region }}</text>
        </view>
        <view class="condition-item">
          <text class="condition-label">会员</text>
          <text class="condition-value">
            {{ store.memberships.length ? store.memberships.join(" / ") : "未开通" }}
          </text>
        </view>
        <view class="condition-item">
          <text class="condition-label">以旧换新</text>
          <text class="condition-value">
            {{ store.tradeInEnabled ? `旧机估值 ${formatMoney(store.tradeInEstimate)}` : "未启用" }}
          </text>
        </view>
        <view class="condition-item">
          <text class="condition-label">排序偏好</text>
          <text class="condition-value">{{ preferenceLabel }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">我的收藏</view>
          <view class="section-sub">{{ store.favorites.length }} 件商品</view>
        </view>
        <view class="section-link" @click="goDiscover">去比价 →</view>
      </view>

      <view v-if="store.favorites.length" class="favorite-list card">
        <view v-for="item in store.favorites" :key="item.id" class="favorite-row">
          <image class="favorite-img" :src="item.image" mode="aspectFill" @click="openProduct(item.id)" />
          <view class="favorite-info" @click="openProduct(item.id)">
            <view class="favorite-name">{{ item.title }}</view>
            <view class="favorite-meta">{{ item.category }} · 收藏价 {{ formatMoney(item.price) }}</view>
          </view>
          <view class="favorite-remove" @click="removeFavorite(item.id)">×</view>
        </view>
      </view>
      <view v-else class="notice">
        还没有收藏。打开任意商品详情，点击右上角的心形即可收藏。
      </view>
    </view>

    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">提交价格</view>
          <view class="section-sub">演示众包数据入口，不抓取平台页面</view>
        </view>
      </view>

      <view class="submit-card card">
        <picker
          mode="selector"
          :range="products"
          range-key="title"
          :value="productIndex"
          @change="onProductChange"
        >
          <view class="picker-field flex between">
            <text>{{ selectedProduct ? selectedProduct.title : "选择商品" }}</text>
            <text class="muted">⌄</text>
          </view>
        </picker>

        <view class="submit-row">
          <picker
            mode="selector"
            :range="PLATFORMS"
            range-key="name"
            :value="platformIndex"
            @change="onPlatformChange"
          >
            <view class="picker-field flex between">
              <text>{{ selectedPlatform.name }}</text>
              <text class="muted">⌄</text>
            </view>
          </picker>
          <input
            v-model="priceInput"
            class="input price-input"
            type="digit"
            placeholder="你看到的价格"
            placeholder-class="input-placeholder"
          />
        </view>

        <input
          v-model="note"
          class="input mt-8"
          placeholder="备注（可选，如：店铺券后价）"
          placeholder-class="input-placeholder"
        />

        <button
          class="btn btn-soft btn-block mt-12"
          :disabled="submitting || !products.length"
          @click="submitPrice"
        >
          {{ submitting ? "提交中…" : "记录这个价格" }}
        </button>
        <view class="submit-tip">仅保存商品、平台、价格和备注，可在提交记录中查看。</view>
      </view>

      <view class="submission-list card">
        <view class="list-title">最近提交</view>
        <view v-if="loadingSubmissions" class="loading">加载中…</view>
        <view v-else-if="submissions.length">
          <view v-for="item in submissions" :key="item.id" class="submission-row">
            <view>
              <view class="submission-label">{{ submissionLabel(item) }}</view>
              <view class="submission-date">{{ dateLabel(item.created_at) }}</view>
            </view>
            <view class="submission-right">
              <text class="chip chip-green">已记录</text>
              <text class="submission-delete" @click="deleteSubmission(item)">删除</text>
            </view>
          </view>
        </view>
        <view v-else class="notice">还没有提交记录。</view>
      </view>
    </view>

    <view class="section">
      <view class="policy-card card">
        <view class="card-title">数据与合规</view>
        <view class="policy-row">
          <text class="policy-index">01</text>
          <text class="policy-text">所有价格、优惠与规则均为演示数据，不代表实时售价。</text>
        </view>
        <view class="policy-row">
          <text class="policy-index">02</text>
          <text class="policy-text">不抓取平台页面；已预留京东联盟、淘宝客、多多进宝等适配层。</text>
        </view>
        <view class="policy-row">
          <text class="policy-index">03</text>
          <text class="policy-text">国补规则 JSON 化、带版本与生效期，可按地区与品类更新。</text>
        </view>
        <view class="policy-row">
          <text class="policy-index">04</text>
          <text class="policy-text">用户提交只保存商品、平台、价格和备注；收藏与购物车仅存本地。</text>
        </view>
      </view>
    </view>

    <view class="about-card card">
      <view class="between">
        <view>
          <view class="about-title">价策 v0.1.0</view>
          <view class="about-sub">uni-app + Vue 3 + FastAPI · 求解决策引擎</view>
        </view>
        <view class="about-mark">价</view>
      </view>
      <view class="divider"></view>
      <view class="about-note">
        12 件演示商品 · 4 个平台 · 6 条补贴规则 · 可解释策略输出
      </view>
      <button class="btn btn-ghost btn-block mt-12" @click="resetDemo">
        重置本地演示数据
      </button>
    </view>

    <ContextSheet v-model:visible="showContext" />
  </view>
</template>

<style scoped>
.condition-card {
  margin-top: 8px;
  padding: 17px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.card-title {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.3px;
}

.card-sub {
  margin-top: 2px;
  font-size: 10px;
  color: var(--muted);
}

.edit {
  font-size: 11px;
  font-weight: 800;
  color: var(--amber-deep);
}

.condition-grid {
  display: flex;
  flex-wrap: wrap;
  margin-top: 13px;
  padding-top: 11px;
  border-top: 1px dashed var(--line);
}

.condition-item {
  width: 50%;
  display: flex;
  flex-direction: column;
  padding: 5px 6px 5px 0;
}

.condition-label {
  font-size: 9px;
  color: var(--muted);
}

.condition-value {
  margin-top: 2px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
}

.section-link {
  font-size: 11px;
  font-weight: 800;
  color: var(--amber-deep);
}

.favorite-list {
  padding: 4px 15px;
}

.favorite-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}

.favorite-row:last-child {
  border-bottom: 0;
}

.favorite-img {
  width: 54px;
  height: 54px;
  border-radius: 11px;
  flex-shrink: 0;
  background: var(--paper-deep);
}

.favorite-info {
  flex: 1;
  min-width: 0;
  padding: 0 10px;
}

.favorite-name {
  font-size: 12px;
  font-weight: 700;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.favorite-meta {
  font-size: 9px;
  color: var(--muted);
  margin-top: 2px;
}

.favorite-remove {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--paper);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.submit-card {
  padding: 15px;
}

.submit-row {
  display: flex;
  margin-top: 8px;
}

.submit-row picker {
  width: 45%;
  margin-right: 8px;
}

.price-input {
  flex: 1;
}

.submit-tip {
  margin-top: 8px;
  font-size: 9px;
  color: var(--muted-light);
  text-align: center;
}

.submission-list {
  margin-top: 12px;
  padding: 15px;
}

.list-title {
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 7px;
}

.submission-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-top: 1px solid var(--line);
}

.submission-label {
  font-size: 11px;
  font-weight: 700;
}

.submission-date {
  font-size: 9px;
  color: var(--muted-light);
  margin-top: 1px;
}

.submission-right {
  display: flex;
  align-items: center;
}

.submission-delete {
  margin-left: 8px;
  font-size: 9px;
  color: var(--muted-light);
  text-decoration: underline;
}

.policy-card {
  padding: 17px;
}

.policy-row {
  display: flex;
  align-items: flex-start;
  margin-top: 10px;
}

.policy-index {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: var(--paper-deep);
  color: var(--muted);
  font-size: 9px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  flex-shrink: 0;
}

.policy-text {
  flex: 1;
  font-size: 10px;
  line-height: 1.6;
  color: var(--muted);
}

.about-card {
  margin-top: 18px;
  margin-bottom: 20px;
  padding: 17px;
}

.about-title {
  font-size: 15px;
  font-weight: 800;
}

.about-sub {
  font-size: 9px;
  color: var(--muted);
  margin-top: 2px;
}

.about-mark {
  width: 40px;
  height: 40px;
  border-radius: 13px;
  background: var(--ink);
  color: var(--amber);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
}

.about-note {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.6;
}
</style>
