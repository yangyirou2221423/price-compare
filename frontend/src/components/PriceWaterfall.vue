<script setup lang="ts">
import { computed } from "vue";
import type { PlatformResult } from "../api/types";
import { formatDiscount, formatMoney } from "../utils/format";

const props = defineProps<{ result: PlatformResult }>();

interface Row {
  id: string;
  label: string;
  amount: number;
  negative: boolean;
  width: number;
  tone: string;
}

const rows = computed<Row[]>(() => {
  const list: Row[] = [
    {
      id: "base",
      label: "页面标价",
      amount: props.result.list_price,
      negative: false,
      width: 100,
      tone: "base",
    },
  ];
  const gross = props.result.list_price || 1;
  props.result.applied
    .filter((step) => !step.is_net_benefit)
    .forEach((step) => {
      if (step.amount <= 0.005) return;
      list.push({
        id: step.benefit_id,
        label: step.name,
        amount: step.amount,
        negative: true,
        width: Math.max(5, Math.min(100, (step.amount / gross) * 100)),
        tone: step.kind === "trade_in" ? "trade" : "discount",
      });
    });
  return list;
});

const netRows = computed(() =>
  props.result.applied.filter((step) => step.is_net_benefit && step.amount > 0.005),
);

const paymentDiscountCount = computed(
  () => props.result.applied.filter((step) => !step.is_net_benefit).length,
);
</script>

<template>
  <view class="waterfall card card-pad">
    <view class="wf-head">
      <view>
        <text class="eyebrow">PRICE TRACE</text>
        <view class="wf-title">价格拆解</view>
      </view>
      <view class="wf-summary">
        <view class="wf-save">共优惠 {{ formatMoney(result.discount_total) }}</view>
        <view class="wf-platform">{{ result.platform_name }}</view>
      </view>
    </view>

    <view class="rows">
      <view v-for="row in rows" :key="row.id" class="wf-row">
        <view class="row-top">
          <text class="row-label">{{ row.label }}</text>
          <text class="row-amount" :class="{ negative: row.negative }">
            {{ row.negative ? formatDiscount(row.amount) : formatMoney(row.amount) }}
          </text>
        </view>
        <view class="track">
          <view class="bar" :class="row.tone" :style="{ width: row.width + '%' }"></view>
        </view>
      </view>
    </view>

    <view class="final-row">
      <view>
        <view class="final-label">预计到手价</view>
        <view class="final-hint">不含返利与赠品估值</view>
      </view>
      <view class="final-price money">{{ formatMoney(result.final_price) }}</view>
    </view>

    <view v-if="netRows.length" class="net-box">
      <view v-for="row in netRows" :key="row.benefit_id" class="net-row">
        <text>{{ row.name }}（不影响实付）</text>
        <text class="net-amount">+{{ formatMoney(row.amount) }}</text>
      </view>
      <view class="net-final">
        <text>计入返利/赠品后净价</text>
        <text class="money">{{ formatMoney(result.net_price) }}</text>
      </view>
    </view>

    <view v-if="!paymentDiscountCount" class="notice mt-12">
      当前平台没有额外支付优惠，标价即到手价。
    </view>
  </view>
</template>

<style scoped>
.wf-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.wf-title {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.4px;
  margin-top: 1px;
}

.wf-summary {
  text-align: right;
}

.wf-save {
  font-size: 11px;
  font-weight: 800;
  color: var(--green);
}

.wf-platform {
  font-size: 9px;
  color: var(--muted);
}

.wf-row {
  margin-bottom: 10px;
}

.row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.row-label {
  font-size: 11px;
  color: var(--ink-soft);
  max-width: 70%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-amount {
  font-size: 12px;
  font-weight: 800;
  color: var(--ink);
}

.row-amount.negative {
  color: var(--green);
}

.track {
  height: 6px;
  border-radius: 999px;
  background: #f1ece2;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 999px;
}

.bar.base {
  background: var(--ink-soft);
}

.bar.discount {
  background: var(--amber);
}

.bar.trade {
  background: var(--green);
}

.final-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 12px;
  padding: 13px 14px;
  border-radius: 14px;
  background: var(--ink);
  color: #fff8ea;
}

.final-label {
  font-size: 12px;
  font-weight: 700;
}

.final-hint {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.55);
  margin-top: 2px;
}

.final-price {
  font-size: 28px;
  line-height: 1;
  color: var(--amber);
}

.net-box {
  margin-top: 10px;
  padding: 11px;
  border-radius: 12px;
  background: var(--green-soft);
}

.net-row {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--green);
  padding: 2px 0;
}

.net-amount {
  font-weight: 800;
}

.net-final {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed rgba(31, 122, 92, 0.25);
  font-size: 11px;
  color: var(--green);
  font-weight: 700;
}
</style>
