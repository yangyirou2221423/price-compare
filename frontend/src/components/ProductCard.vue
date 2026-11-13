<script setup lang="ts">
import type { ProductCard as ProductCardType } from "../api/types";
import { formatMoney, platformTone } from "../utils/format";
import DataSourceBadge from "./DataSourceBadge.vue";

const props = defineProps<{ product: ProductCardType }>();

function open() {
  uni.navigateTo({
    url: `/pages/compare/compare?id=${encodeURIComponent(props.product.id)}`,
  });
}
</script>

<template>
  <view class="product-card card fade-in" @click="open">
    <view class="media">
      <image class="product-img" :src="product.image" mode="aspectFill" />
      <view class="platform-badge" :class="`tone-${platformTone(product.best_platform)}`">
        {{ product.best_platform_name }}
      </view>
      <view v-if="product.savings > 0.005" class="save-badge">
        省 {{ formatMoney(product.savings) }}
      </view>
    </view>
    <view class="body">
      <view class="brand-line">
        <text class="brand">{{ product.brand }}</text>
        <text class="category">{{ product.category }}</text>
      </view>
      <view class="title">{{ product.title }}</view>
      <view class="specs">{{ product.specs }}</view>
      <view class="price-row">
        <view class="price-left">
          <text class="price money">{{ formatMoney(product.best_price) }}</text>
          <text class="price-suffix">到手</text>
        </view>
        <text class="list-price">标价 {{ formatMoney(product.list_price) }}</text>
      </view>
      <view class="summary">{{ product.summary }}</view>
      <view class="footer">
        <DataSourceBadge :source="product.data_source" />
        <view class="cta">看怎么买 <text class="arrow">→</text></view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.product-card {
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.product-card:active {
  transform: scale(0.992);
  box-shadow: 0 6px 18px rgba(14, 27, 44, 0.06);
}

.media {
  position: relative;
  height: 168px;
  background: var(--paper-deep);
}

.product-img {
  width: 100%;
  height: 100%;
  display: block;
}

.platform-badge {
  position: absolute;
  left: 12px;
  top: 12px;
  padding: 4px 9px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.4px;
  color: #fff;
}

.tone-jd {
  background: #d92b22;
}

.tone-taobao {
  background: #e85712;
}

.tone-pdd {
  background: #d63027;
}

.tone-douyin {
  background: #15171c;
}

.tone-default {
  background: var(--ink);
}

.save-badge {
  position: absolute;
  right: 12px;
  top: 12px;
  padding: 4px 9px;
  border-radius: 8px;
  background: var(--amber);
  color: #2b1a00;
  font-size: 10px;
  font-weight: 800;
}

.body {
  padding: 13px 14px 14px;
}

.brand-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 3px;
}

.brand {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--muted);
}

.category {
  font-size: 9px;
  color: var(--muted-light);
}

.title {
  font-size: 15px;
  font-weight: 800;
  line-height: 1.35;
  letter-spacing: -0.2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 40px;
}

.specs {
  margin-top: 3px;
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 9px;
}

.price-left {
  display: flex;
  align-items: baseline;
}

.price {
  font-size: 24px;
  line-height: 1;
  color: var(--ink);
}

.price-suffix {
  margin-left: 4px;
  font-size: 10px;
  color: var(--muted);
}

.list-price {
  font-size: 10px;
  color: var(--muted-light);
  text-decoration: line-through;
}

.summary {
  margin-top: 7px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 33px;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.cta {
  font-size: 12px;
  font-weight: 800;
  color: var(--amber-deep);
}

.arrow {
  margin-left: 2px;
}
</style>
