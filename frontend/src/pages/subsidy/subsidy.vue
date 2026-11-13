<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type {
  PlatformInfo,
  SubsidyCheckResponse,
} from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import { formatMoney } from "../../utils/format";
import {
  MEMBERSHIP_OPTIONS,
  REGION_OPTIONS,
  useAppStore,
} from "../../stores/app";

const FALLBACK_CATEGORIES = [
  "手机",
  "笔记本",
  "平板",
  "家电",
  "耳机",
  "影音",
  "个护",
  "穿戴",
  "清洁电器",
  "家居",
];
const FALLBACK_PLATFORMS: PlatformInfo[] = [
  { id: "jd", name: "京东", short: "京东" },
  { id: "taobao", name: "淘宝", short: "淘宝" },
  { id: "pdd", name: "拼多多", short: "拼多多" },
  { id: "douyin", name: "抖音", short: "抖音" },
];

const store = useAppStore();
const categories = ref<string[]>(FALLBACK_CATEGORIES);
const platforms = ref<PlatformInfo[]>(FALLBACK_PLATFORMS);
const regions = ref<string[]>(REGION_OPTIONS);

const category = ref("手机");
const priceInput = ref("5999");
const platform = ref("taobao");
const region = ref(store.region || "浙江");
const memberships = ref<string[]>([...store.memberships]);
const tradeInEnabled = ref(store.tradeInEnabled);
const tradeInDevice = ref(store.tradeInDevice);
const tradeInEstimate = ref(store.tradeInEstimate);

const result = ref<SubsidyCheckResponse | null>(null);
const loading = ref(false);
const error = ref("");
let booted = false;

const categoryIndex = computed(() =>
  Math.max(0, categories.value.indexOf(category.value)),
);
const platformIndex = computed(() =>
  Math.max(
    0,
    platforms.value.findIndex((item) => item.id === platform.value),
  ),
);
const regionIndex = computed(() =>
  Math.max(0, regions.value.indexOf(region.value)),
);
const platformName = computed(
  () =>
    platforms.value.find((item) => item.id === platform.value)?.name ||
    platform.value,
);

onShow(() => {
  if (booted) return;
  booted = true;
  loadConfig();
});

async function loadConfig() {
  try {
    const config = await api.config();
    if (config.categories?.length) {
      categories.value = config.categories;
      if (!categories.value.includes(category.value)) {
        category.value = categories.value[0];
      }
    }
    if (config.platforms?.length) platforms.value = config.platforms;
    if (config.regions?.length) regions.value = config.regions;
  } catch {
    // Keep local fallbacks; the form still demonstrates the rule engine offline.
  }
  check();
}

function onCategoryChange(event: any) {
  const index = Number(event?.detail?.value ?? 0);
  category.value = categories.value[index] || categories.value[0];
}

function onPlatformChange(event: any) {
  const index = Number(event?.detail?.value ?? 0);
  platform.value = platforms.value[index]?.id || "taobao";
}

function onRegionChange(event: any) {
  const index = Number(event?.detail?.value ?? 0);
  region.value = regions.value[index] || "全国";
}

function toggleMembership(name: string) {
  if (memberships.value.includes(name)) {
    memberships.value = memberships.value.filter((item) => item !== name);
  } else {
    memberships.value = [...memberships.value, name];
  }
}

function onTradeInChange(event: any) {
  tradeInEnabled.value = Boolean(event?.detail?.value);
}

async function check() {
  const price = Number(priceInput.value);
  if (!Number.isFinite(price) || price <= 0) {
    uni.showToast({ title: "请输入有效价格", icon: "none" });
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    result.value = await api.subsidy({
      category: category.value,
      price,
      platform: platform.value,
      region: region.value,
      memberships: memberships.value,
      trade_in: tradeInEnabled.value
        ? {
            device_name: tradeInDevice.value || "旧设备",
            estimate: Math.max(0, Number(tradeInEstimate.value) || 0),
          }
        : null,
    });
  } catch (err: any) {
    error.value = err?.message || "计算失败，请稍后重试";
    result.value = null;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <view class="page-shell page-shell--narrow">
    <PageHeader
      back
      title="国补计算器"
      subtitle="示例规则，按地区与品类判定"
    />

    <view class="intro-card fade-in">
      <text class="intro-eyebrow">POLICY CALCULATOR</text>
      <view class="intro-title">先别下单，</view>
      <view class="intro-title">看看能领<text class="accent">多少</text>。</view>
      <view class="intro-sub">
        国补、地区加码、以旧换新分开判定；金额按示例规则估算。
      </view>
    </view>

    <view class="form-card card">
      <view class="form-grid">
        <view class="field">
          <text class="form-label">商品品类</text>
          <picker
            mode="selector"
            :range="categories"
            :value="categoryIndex"
            @change="onCategoryChange"
          >
            <view class="picker-field flex between">
              <text>{{ category }}</text>
              <text class="muted">⌄</text>
            </view>
          </picker>
        </view>
        <view class="field">
          <text class="form-label">商品价格（元）</text>
          <input
            v-model="priceInput"
            class="input"
            type="digit"
            placeholder="5999"
            placeholder-class="input-placeholder"
          />
        </view>
      </view>

      <view class="form-grid">
        <view class="field">
          <text class="form-label">购买平台</text>
          <picker
            mode="selector"
            :range="platforms"
            range-key="name"
            :value="platformIndex"
            @change="onPlatformChange"
          >
            <view class="picker-field flex between">
              <text>{{ platformName }}</text>
              <text class="muted">⌄</text>
            </view>
          </picker>
        </view>
        <view class="field">
          <text class="form-label">所在地区</text>
          <picker
            mode="selector"
            :range="regions"
            :value="regionIndex"
            @change="onRegionChange"
          >
            <view class="picker-field flex between">
              <text>{{ region }}</text>
              <text class="muted">⌄</text>
            </view>
          </picker>
        </view>
      </view>

      <view class="field">
        <text class="form-label">会员身份</text>
        <view class="chip-row">
          <view
            v-for="name in MEMBERSHIP_OPTIONS"
            :key="name"
            class="chip"
            :class="{ 'chip-active': memberships.includes(name) }"
            @click="toggleMembership(name)"
          >
            {{ name }}
          </view>
        </view>
      </view>

      <view class="field">
        <view class="switch-row">
          <view>
            <text class="form-label">以旧换新</text>
            <view class="hint">仅部分品类/平台支持，按你填写的旧机估值计算</view>
          </view>
          <switch
            :checked="tradeInEnabled"
            color="#E9A23B"
            @change="onTradeInChange"
          />
        </view>
        <view v-if="tradeInEnabled" class="trade-grid">
          <view>
            <text class="form-label">旧设备</text>
            <input
              v-model="tradeInDevice"
              class="input"
              placeholder="旧手机 / 旧家电"
              placeholder-class="input-placeholder"
            />
          </view>
          <view>
            <text class="form-label">估值（元）</text>
            <input
              v-model="tradeInEstimate"
              class="input"
              type="digit"
              placeholder="300"
              placeholder-class="input-placeholder"
            />
          </view>
        </view>
      </view>

      <button class="btn btn-amber btn-block" :disabled="loading" @click="check">
        {{ loading ? "正在判定…" : "计算补贴" }}
      </button>
      <view class="form-note">
        示例规则，不构成政策承诺；实际以当地最新政策、平台页面和实名资格为准。
      </view>
    </view>

    <view v-if="error" class="notice notice--red mt-12">
      {{ error }}
      <view class="retry" @click="check">重新计算</view>
    </view>

    <template v-if="result">
      <view class="total-card fade-in">
        <view class="total-head">
          <view>
            <text class="total-eyebrow">ESTIMATED BENEFIT</text>
            <view class="total-title">预计可减</view>
          </view>
          <view class="chip chip-amber">{{ result.region }}</view>
        </view>
        <view class="total-price money">{{ formatMoney(result.total_estimated) }}</view>
        <view class="total-sub">
          {{ result.category }} · {{ formatMoney(result.price) }} · {{ result.platform_name }}
        </view>
        <view class="total-note">
          不含平台券与店铺券；同一笔订单的实际优惠以结算页为准。
        </view>
      </view>

      <view class="section">
        <view class="section-head">
          <view>
            <view class="section-title">规则判定</view>
            <view class="section-sub">每条规则独立判断资格与金额</view>
          </view>
        </view>

        <view
          v-for="item in result.items"
          :key="item.rule_id"
          class="rule-card card"
        >
          <view class="rule-head">
            <view class="rule-title-wrap">
              <view class="rule-name">{{ item.name }}</view>
              <view class="rule-meta">
                {{ item.source }} · v{{ item.version }} · {{ item.effective }}
              </view>
            </view>
            <view class="chip" :class="item.eligible ? 'chip-green' : 'chip-red'">
              {{ item.eligible ? "符合" : "不符合" }}
            </view>
          </view>

          <view class="rule-amount-row">
            <text class="rule-amount money">
              {{ item.eligible ? formatMoney(item.amount) : "¥0" }}
            </text>
            <text class="rule-reason">{{ item.reason }}</text>
          </view>

          <view v-if="item.description" class="rule-desc">
            {{ item.description }}
          </view>
        </view>

        <view v-if="!result.items.length" class="notice">
          该品类暂未配置示例补贴规则。
        </view>
      </view>

      <view class="notes-card card">
        <view class="notes-title">说明</view>
        <view v-for="(note, index) in result.notes" :key="index" class="note-row">
          <text class="note-dot">·</text>
          <text class="note-text">{{ note }}</text>
        </view>
      </view>
    </template>
  </view>
</template>

<style scoped>
.intro-card {
  margin-top: 8px;
  padding: 21px;
  border-radius: 22px;
  background: radial-gradient(circle at 88% 0%, #2b4564 0, #14263b 42%, #0b1728 100%);
  color: #fff8ea;
  box-shadow: 0 18px 36px rgba(14, 27, 44, 0.2);
}

.intro-eyebrow {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 2.2px;
  color: rgba(255, 248, 234, 0.48);
}

.intro-title {
  font-size: 27px;
  font-weight: 800;
  letter-spacing: -0.8px;
  line-height: 1.2;
}

.intro-title:first-of-type {
  margin-top: 12px;
}

.accent {
  color: var(--amber);
}

.intro-sub {
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.6;
  color: rgba(255, 248, 234, 0.62);
}

.form-card {
  margin-top: 14px;
  padding: 17px;
}

.form-grid {
  display: flex;
}

.field {
  flex: 1;
  margin-bottom: 14px;
  min-width: 0;
}

.form-grid .field:first-child {
  margin-right: 10px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
}

.chip-row .chip {
  margin: 0 7px 7px 0;
  font-size: 11px;
}

.hint {
  margin-top: 4px;
  font-size: 10px;
  color: var(--muted);
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.trade-grid {
  display: flex;
  margin-top: 8px;
}

.trade-grid > view {
  width: 50%;
}

.trade-grid > view:first-child {
  margin-right: 10px;
}

.form-note {
  margin-top: 9px;
  font-size: 9px;
  color: var(--muted-light);
  line-height: 1.5;
  text-align: center;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}

.total-card {
  margin-top: 18px;
  padding: 19px;
  border-radius: 22px;
  background: radial-gradient(circle at 88% 0%, #2b4564 0, #14263b 42%, #0b1728 100%);
  color: #fff8ea;
}

.total-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.total-eyebrow {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 2px;
  color: rgba(255, 248, 234, 0.48);
}

.total-title {
  font-size: 15px;
  font-weight: 800;
  margin-top: 1px;
}

.total-price {
  margin-top: 10px;
  font-size: 42px;
  line-height: 1;
  color: var(--amber);
}

.total-sub {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(255, 248, 234, 0.7);
}

.total-note {
  margin-top: 8px;
  font-size: 9px;
  color: rgba(255, 248, 234, 0.45);
}

.rule-card {
  padding: 15px;
  margin-bottom: 11px;
}

.rule-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.rule-title-wrap {
  min-width: 0;
}

.rule-name {
  font-size: 14px;
  font-weight: 800;
}

.rule-meta {
  font-size: 9px;
  color: var(--muted);
  margin-top: 2px;
}

.rule-amount-row {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.rule-amount {
  font-size: 20px;
  color: var(--ink);
  flex-shrink: 0;
}

.rule-reason {
  margin-left: 9px;
  font-size: 10px;
  line-height: 1.5;
  color: var(--muted);
}

.rule-desc {
  margin-top: 7px;
  padding-top: 7px;
  border-top: 1px dashed var(--line);
  font-size: 10px;
  line-height: 1.55;
  color: var(--muted-light);
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
  .total-price {
    font-size: 34px;
  }

  .intro-title {
    font-size: 24px;
  }
}
</style>
