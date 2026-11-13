<script setup lang="ts">
import { ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { api } from "../../api/client";
import type { ProductCard as ProductCardType } from "../../api/types";
import PageHeader from "../../components/PageHeader.vue";
import ProductCard from "../../components/ProductCard.vue";
import EmptyState from "../../components/EmptyState.vue";

const FALLBACK_CATEGORIES = [
  "全部",
  "手机",
  "笔记本",
  "平板",
  "耳机",
  "家电",
  "影音",
  "个护",
  "穿戴",
  "清洁电器",
  "家居",
];

const keyword = ref("");
const category = ref("全部");
const categories = ref<string[]>(FALLBACK_CATEGORIES);
const products = ref<ProductCardType[]>([]);
const loading = ref(true);
const error = ref("");
let configLoaded = false;

onLoad((options) => {
  if (options?.q) {
    try {
      keyword.value = decodeURIComponent(String(options.q));
    } catch {
      keyword.value = String(options.q);
    }
  }
});

onShow(() => {
  load();
});

async function loadConfig() {
  if (configLoaded) return;
  configLoaded = true;
  try {
    const config = await api.config();
    if (config.categories?.length) {
      categories.value = ["全部", ...config.categories];
    }
  } catch {
    // Keep the local fallback list when the API is temporarily unavailable.
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  await loadConfig();
  try {
    const response = await api.products({
      q: keyword.value.trim(),
      category: category.value === "全部" ? "" : category.value,
    });
    products.value = response.products;
  } catch (err: any) {
    error.value = err?.message || "加载失败，请稍后重试";
    products.value = [];
  } finally {
    loading.value = false;
  }
}

function selectCategory(name: string) {
  category.value = name;
  load();
}

function search() {
  load();
}

function clearFilters() {
  keyword.value = "";
  category.value = "全部";
  load();
}
</script>

<template>
  <view class="page-shell">
    <PageHeader
      title="比价"
      subtitle="搜一件商品，看各平台最终到手价"
      @change="load"
    />

    <view class="search-panel card">
      <view class="search-line">
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜品牌、型号或品类"
          placeholder-class="input-placeholder"
          confirm-type="search"
          @confirm="search"
        />
        <button class="btn btn-primary btn-sm search-btn" @click="search">
          搜索
        </button>
      </view>
      <view class="cat-row">
        <view
          v-for="name in categories"
          :key="name"
          class="chip cat-chip"
          :class="{ 'chip-active': category === name }"
          @click="selectCategory(name)"
        >
          {{ name }}
        </view>
      </view>
    </view>

    <view class="result-line">
      <text class="muted">共 {{ products.length }} 件商品</text>
      <text class="muted tiny">价格为演示数据</text>
    </view>

    <view v-if="error" class="notice notice--red mt-12">
      {{ error }}
      <view class="retry" @click="load">重新连接</view>
    </view>

    <view v-if="loading" class="grid-products mt-12">
      <view v-for="index in 6" :key="index" class="grid-item">
        <view class="card">
          <view class="skeleton" style="height: 168px; border-radius: 20px 20px 0 0"></view>
          <view style="padding: 14px">
            <view class="skeleton" style="height: 14px; width: 55%"></view>
            <view class="skeleton mt-12" style="height: 22px; width: 90%"></view>
            <view class="skeleton mt-12" style="height: 30px; width: 42%"></view>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="products.length" class="grid-products mt-12">
      <view v-for="item in products" :key="item.id" class="grid-item">
        <ProductCard :product="item" />
      </view>
    </view>

    <EmptyState
      v-else
      class="mt-16"
      icon="⌕"
      title="没有找到匹配的商品"
      description="换个关键词，或清空品类筛选再试一次。"
      action-text="清空筛选"
      @action="clearFilters"
    />
  </view>
</template>

<style scoped>
.search-panel {
  margin-top: 8px;
  padding: 12px;
  border-radius: 18px;
}

.search-line {
  display: flex;
  align-items: center;
}

.search-input {
  flex: 1;
  height: 42px;
  padding: 0 11px;
  border-radius: 12px;
  background: var(--paper);
  font-size: 13px;
}

.search-btn {
  margin-left: 8px;
  min-width: 74px;
}

.cat-row {
  display: flex;
  flex-wrap: wrap;
  margin-top: 10px;
}

.cat-chip {
  margin: 0 7px 7px 0;
  padding: 5px 11px;
  font-size: 11px;
}

.result-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 17px;
  font-size: 12px;
}

.retry {
  display: inline-block;
  margin-top: 8px;
  font-weight: 800;
  color: var(--red);
  text-decoration: underline;
}
</style>
