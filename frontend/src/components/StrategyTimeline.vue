<script setup lang="ts">
import { computed } from "vue";
import type { PlatformResult } from "../api/types";
import { formatMoney, kindLabel } from "../utils/format";

const props = defineProps<{ result: PlatformResult }>();

interface Step {
  id: string;
  index: number;
  name: string;
  kind: string;
  description: string;
  amount: number;
  priceAfter: number;
  isNet: boolean;
}

const FALLBACK: Record<string, string> = {
  store_coupon: "先在店铺首页领取，再提交订单。",
  platform_coupon: "在平台会场领取后下单，注意使用门槛。",
  category_coupon: "在品类会场领取，确认商品在适用范围内。",
  full_reduction: "把商品合并到同一订单，达到门槛后自动抵扣。",
  member: "使用对应会员身份下单，价格会自动生效。",
  platform_subsidy: "使用平台活动价或补贴入口下单。",
  national_subsidy: "下单后在平台补贴入口完成资格校验。",
  trade_in: "提交旧机回收订单，按检测结果抵扣。",
  payment_discount: "选择指定支付方式，结算时自动立减。",
  rebate: "确认收货后按平台规则结算返利。",
  gift: "赠品价值按估值计入净价，不影响实付。",
};

const steps = computed<Step[]>(() =>
  props.result.applied.map((step, index) => ({
    id: step.benefit_id,
    index: index + 1,
    name: step.name,
    kind: step.kind,
    description: step.description || FALLBACK[step.kind] || "按平台页面提示操作。",
    amount: step.amount,
    priceAfter: step.price_after,
    isNet: step.is_net_benefit,
  })),
);
</script>

<template>
  <view class="timeline card card-pad">
    <view class="head">
      <text class="eyebrow">PLAYBOOK</text>
      <view class="title">按顺序执行</view>
      <view class="sub">每一步都来自当前条件下的最优解</view>
    </view>

    <view v-if="steps.length" class="steps">
      <view v-for="(step, index) in steps" :key="step.id" class="step">
        <view class="rail">
          <view class="dot" :class="step.kind">{{ step.index }}</view>
          <view v-if="index < steps.length - 1" class="line"></view>
        </view>
        <view class="step-body">
          <view class="step-top">
            <view class="step-title-wrap">
              <text class="step-name">{{ step.name }}</text>
              <text class="kind">{{ kindLabel(step.kind) }}</text>
            </view>
            <text class="step-amount" :class="{ net: step.isNet }">
              {{ step.isNet ? "+" : "-" }}{{ formatMoney(step.amount) }}
            </text>
          </view>
          <view class="step-desc">{{ step.description }}</view>
          <view v-if="!step.isNet" class="step-after">
            执行后价格 <text class="money">{{ formatMoney(step.priceAfter) }}</text>
          </view>
          <view v-else class="step-after">返利不影响支付金额，确认收货后到账</view>
        </view>
      </view>
    </view>

    <view v-else class="empty-steps">
      当前平台没有额外优惠，直接按页面价下单即可。
    </view>

    <view class="final">
      <view class="final-dot">✓</view>
      <view class="final-info">
        <text class="final-label">预计实付</text>
        <text class="final-hint">以平台结算页为准</text>
      </view>
      <text class="final-price money">{{ formatMoney(result.final_price) }}</text>
    </view>

    <view
      v-if="result.net_price < result.final_price - 0.005"
      class="net-note"
    >
      计入返利/赠品后，净价约
      <text class="money">{{ formatMoney(result.net_price) }}</text>
    </view>
  </view>
</template>

<style scoped>
.head {
  margin-bottom: 16px;
}

.title {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.4px;
  margin-top: 1px;
}

.sub {
  font-size: 10px;
  color: var(--muted);
  margin-top: 2px;
}

.step {
  display: flex;
  align-items: stretch;
}

.rail {
  width: 34px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.dot {
  width: 26px;
  height: 26px;
  border-radius: 9px;
  background: var(--paper-deep);
  color: var(--ink-soft);
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dot.national_subsidy {
  background: var(--amber-soft);
  color: var(--amber-deep);
}

.dot.trade_in {
  background: var(--green-soft);
  color: var(--green);
}

.dot.platform_subsidy {
  background: var(--ink);
  color: var(--amber);
}

.line {
  width: 2px;
  flex: 1;
  min-height: 26px;
  background: var(--line);
  margin: 4px 0;
  border-radius: 2px;
}

.step-body {
  flex: 1;
  padding: 0 0 18px 10px;
  min-width: 0;
}

.step-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.step-title-wrap {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.step-name {
  font-size: 13px;
  font-weight: 800;
  line-height: 1.35;
}

.kind {
  font-size: 9px;
  color: var(--muted);
  margin-top: 1px;
}

.step-amount {
  font-size: 13px;
  font-weight: 800;
  color: var(--green);
  flex-shrink: 0;
  margin-left: 8px;
}

.step-amount.net {
  color: var(--amber-deep);
}

.step-desc {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.5;
  margin-top: 4px;
}

.step-after {
  font-size: 10px;
  color: var(--muted-light);
  margin-top: 4px;
}

.empty-steps {
  padding: 14px;
  border-radius: 12px;
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.final {
  display: flex;
  align-items: center;
  margin-top: 2px;
  padding: 14px;
  border-radius: 14px;
  background: var(--ink);
  color: #fff8ea;
}

.final-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--amber);
  color: #2b1a00;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  margin-right: 10px;
  flex-shrink: 0;
}

.final-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.final-label {
  font-size: 12px;
  font-weight: 700;
}

.final-hint {
  font-size: 9px;
  color: rgba(255, 248, 234, 0.52);
}

.final-price {
  font-size: 26px;
  color: var(--amber);
  line-height: 1;
}

.net-note {
  margin-top: 9px;
  font-size: 10px;
  color: var(--green);
  text-align: right;
}
</style>
