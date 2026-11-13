<script setup lang="ts">
import { computed } from "vue";
import type { PricePoint } from "../api/types";
import { formatMoney, formatDateRange } from "../utils/format";

const props = withDefaults(
  defineProps<{
    points: PricePoint[];
    height?: number;
    maxBars?: number;
  }>(),
  { height: 118, maxBars: 48 },
);

const buckets = computed(() => {
  const points = props.points || [];
  if (points.length <= props.maxBars) {
    return points.map((point) => ({ date: point.date, price: point.price }));
  }
  const size = Math.ceil(points.length / props.maxBars);
  const result: { date: string; price: number }[] = [];
  for (let index = 0; index < points.length; index += size) {
    const chunk = points.slice(index, index + size);
    const average =
      chunk.reduce((sum, point) => sum + point.price, 0) / chunk.length;
    result.push({ date: chunk[chunk.length - 1].date, price: average });
  }
  const last = points[points.length - 1];
  result[result.length - 1] = { date: last.date, price: last.price };
  return result;
});

const prices = computed(() => props.points.map((point) => point.price));
const min = computed(() => (prices.value.length ? Math.min(...prices.value) : 0));
const max = computed(() => (prices.value.length ? Math.max(...prices.value) : 0));
const range = computed(() => Math.max(1, max.value - min.value));

const median = computed(() => {
  if (!prices.value.length) return 0;
  const sorted = [...prices.value].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
});

const medianPercent = computed(() =>
  Math.max(0, Math.min(100, ((median.value - min.value) / range.value) * 100)),
);

const bars = computed(() =>
  buckets.value.map((bucket, index) => {
    const ratio = (bucket.price - min.value) / range.value;
    return {
      ...bucket,
      height: Math.max(8, Math.min(100, 12 + ratio * 88)),
      isLast: index === buckets.value.length - 1,
      isLow: bucket.price <= min.value + range.value * 0.12,
    };
  }),
);

const dateRange = computed(() => formatDateRange(props.points));
</script>

<template>
  <view v-if="points.length" class="spark-wrap">
    <view class="spark" :style="{ height: height + 'px' }">
      <view
        class="median-line"
        :style="{ bottom: medianPercent + '%' }"
      >
        <text class="median-tag">中位 {{ formatMoney(median) }}</text>
      </view>
      <view
        v-for="(bar, index) in bars"
        :key="index"
        class="bar-wrap"
      >
        <view
          class="bar"
          :class="{ last: bar.isLast, low: bar.isLow }"
          :style="{ height: bar.height + '%' }"
        ></view>
      </view>
    </view>
    <view class="axis">
      <text>{{ dateRange.split(" – ")[0] }}</text>
      <text class="axis-mid">90 天价格带</text>
      <text>{{ dateRange.split(" – ")[1] }}</text>
    </view>
  </view>
  <view v-else class="empty">暂无价格历史</view>
</template>

<style scoped>
.spark-wrap {
  width: 100%;
}

.spark {
  position: relative;
  display: flex;
  align-items: flex-end;
  padding-bottom: 2px;
  border-bottom: 1px solid var(--line);
}

.bar-wrap {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: flex-end;
  padding: 0 1px;
  min-width: 2px;
}

.bar {
  width: 100%;
  min-height: 4px;
  border-radius: 3px 3px 0 0;
  background: #ded5c4;
  z-index: 1;
}

.bar.low {
  background: rgba(31, 122, 92, 0.55);
}

.bar.last {
  background: var(--amber);
}

.median-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  border-top: 1px dashed rgba(14, 27, 44, 0.22);
  z-index: 2;
  pointer-events: none;
}

.median-tag {
  position: absolute;
  right: 0;
  top: -16px;
  padding: 1px 5px;
  border-radius: 5px;
  background: var(--paper);
  color: var(--muted);
  font-size: 8px;
}

.axis {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 7px;
  font-size: 9px;
  color: var(--muted-light);
}

.axis-mid {
  color: var(--muted);
}

.empty {
  padding: 30px 0;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
}
</style>
