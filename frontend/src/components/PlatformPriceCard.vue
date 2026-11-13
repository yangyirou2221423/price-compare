<script setup lang="ts">
import { computed, ref } from "vue";
import type { PlatformResult } from "../api/types";
import {
  formatDiscount,
  formatMoney,
  kindLabel,
  platformTone,
  PLATFORM_META,
} from "../utils/format";

const props = withDefaults(
  defineProps<{ result: PlatformResult; best?: boolean }>(),
  { best: false },
);

const expanded = ref(false);
const mark = computed(
  () => PLATFORM_META[props.result.platform]?.mark || props.result.platform.slice(0, 1),
);

function benefitAmount(isNet: boolean, amount: number): string {
  return isNet ? `+${formatMoney(amount)}` : formatDiscount(amount);
}
</script>

<template>
  <view class="platform-card card" :class="{ 'is-best': best }">
    <view class="top">
      <view class="platform">
        <view class="mark" :class="`mark-${platformTone(result.platform)}`">
          {{ mark }}
        </view>
        <view class="platform-meta">
          <view class="platform-name">
            {{ result.platform_name }}
            <text v-if="best" class="best-tag">最优</text>
          </view>
          <view class="shop">{{ result.shop_name }}</view>
        </view>
      </view>
      <view class="price-block">
        <view class="price money">{{ formatMoney(result.final_price) }}</view>
        <view class="price-label">预计到手</view>
      </view>
    </view>

    <view class="meta-row">
      <text class="meta">标价 {{ formatMoney(result.list_price) }}</text>
      <text v-if="result.promo_savings > 0.005" class="meta meta-green">
        优惠 {{ formatMoney(result.promo_savings) }}
      </text>
      <text v-if="result.trade_in_value > 0.005" class="meta meta-amber">
        旧机抵扣 {{ formatMoney(result.trade_in_value) }}
      </text>
      <text
        v-if="result.net_price < result.final_price - 0.005"
        class="meta meta-green"
      >
        净价 {{ formatMoney(result.net_price) }}
      </text>
    </view>

    <view v-if="result.note" class="note">{{ result.note }}</view>

    <view v-if="result.applied.length" class="benefits">
      <view
        v-for="item in result.applied.slice(0, 3)"
        :key="item.benefit_id"
        class="benefit-chip"
      >
        <text class="benefit-name">{{ item.name }}</text>
        <text class="benefit-amount" :class="{ net: item.is_net_benefit }">
          {{ benefitAmount(item.is_net_benefit, item.amount) }}
        </text>
      </view>
      <text v-if="result.applied.length > 3" class="more">
        +{{ result.applied.length - 3 }} 项
      </text>
    </view>
    <view v-else class="no-benefit">当前条件下暂无额外优惠</view>

    <view class="expand" @click="expanded = !expanded">
      <text>{{ expanded ? "收起优惠明细" : "查看优惠明细" }}</text>
      <text class="chev">{{ expanded ? "⌃" : "⌄" }}</text>
    </view>

    <view v-if="expanded" class="details">
      <view v-if="result.applied.length">
        <view class="detail-title">优惠拆解</view>
        <view
          v-for="step in result.applied"
          :key="step.benefit_id"
          class="detail-row"
        >
          <view class="detail-info">
            <text class="detail-name">{{ step.name }}</text>
            <text class="detail-after">{{ kindLabel(step.kind) }}</text>
          </view>
          <text class="detail-amount" :class="{ net: step.is_net_benefit }">
            {{ benefitAmount(step.is_net_benefit, step.amount) }}
          </text>
        </view>
      </view>
      <view v-if="result.rejected.length" class="reject-box">
        <view class="detail-title">没有采用的优惠</view>
        <view
          v-for="item in result.rejected.slice(0, 6)"
          :key="item.benefit_id"
          class="reject-row"
        >
          <text class="reject-name">{{ item.name }}</text>
          <text class="reject-reason">{{ item.reason }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.platform-card {
  padding: 15px;
  margin-bottom: 12px;
  border-radius: 18px;
}

.is-best {
  border-color: var(--amber);
  box-shadow: 0 12px 28px rgba(233, 162, 59, 0.14);
}

.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.platform {
  display: flex;
  align-items: center;
  min-width: 0;
}

.mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  margin-right: 10px;
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

.platform-meta {
  min-width: 0;
}

.platform-name {
  font-size: 15px;
  font-weight: 800;
}

.best-tag {
  margin-left: 6px;
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--amber);
  color: #2b1a00;
  font-size: 9px;
  font-weight: 800;
}

.shop {
  font-size: 10px;
  color: var(--muted);
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}

.price-block {
  text-align: right;
  flex-shrink: 0;
  margin-left: 10px;
}

.price {
  font-size: 25px;
  line-height: 1;
}

.price-label {
  font-size: 9px;
  color: var(--muted);
  margin-top: 3px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  margin-top: 10px;
}

.meta {
  font-size: 10px;
  color: var(--muted);
  background: var(--paper);
  border-radius: 7px;
  padding: 3px 7px;
  margin: 0 6px 5px 0;
}

.meta-green {
  color: var(--green);
  background: var(--green-soft);
}

.meta-amber {
  color: var(--amber-deep);
  background: var(--amber-soft);
}

.note {
  margin-top: 6px;
  padding: 8px 10px;
  border-radius: 9px;
  background: var(--paper);
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
}

.benefits {
  display: flex;
  flex-wrap: wrap;
  margin-top: 9px;
}

.benefit-chip {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 8px;
  background: #fbf3e4;
  margin: 0 6px 6px 0;
  font-size: 9px;
}

.benefit-name {
  color: #6f5a33;
  max-width: 170px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.benefit-amount {
  margin-left: 5px;
  font-weight: 800;
  color: var(--green);
}

.benefit-amount.net {
  color: var(--amber-deep);
}

.more {
  font-size: 9px;
  color: var(--muted);
  align-self: center;
}

.no-benefit {
  margin-top: 9px;
  font-size: 10px;
  color: var(--muted-light);
}

.expand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding-top: 9px;
  border-top: 1px dashed var(--line);
  font-size: 11px;
  color: var(--muted);
}

.chev {
  font-size: 12px;
}

.details {
  margin-top: 10px;
  padding: 11px;
  border-radius: 12px;
  background: #fbf8f2;
}

.detail-title {
  font-size: 10px;
  font-weight: 800;
  color: var(--muted);
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.detail-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.detail-name {
  font-size: 11px;
  color: var(--ink-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.detail-after {
  font-size: 9px;
  color: var(--muted-light);
}

.detail-amount {
  font-size: 12px;
  font-weight: 800;
  color: var(--green);
  flex-shrink: 0;
}

.detail-amount.net {
  color: var(--amber-deep);
}

.reject-box {
  margin-top: 10px;
  padding-top: 9px;
  border-top: 1px dashed var(--line);
}

.reject-row {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}

.reject-name {
  font-size: 10px;
  color: var(--muted);
}

.reject-reason {
  font-size: 9px;
  color: var(--muted-light);
  line-height: 1.45;
}
</style>
