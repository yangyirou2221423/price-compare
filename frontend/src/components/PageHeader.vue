<script setup lang="ts">
import { ref } from "vue";
import { useAppStore } from "../stores/app";
import ContextSheet from "./ContextSheet.vue";

withDefaults(
  defineProps<{
    title: string;
    subtitle?: string;
    back?: boolean;
  }>(),
  { subtitle: "", back: false },
);

const emit = defineEmits<{ (event: "change"): void }>();
const store = useAppStore();
const showContext = ref(false);

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.switchTab({ url: "/pages/index/index" });
  }
}
</script>

<template>
  <view class="top-safe">
    <view class="app-header">
      <view class="left">
        <view v-if="back" class="back-btn" @click="goBack">←</view>
        <view v-else class="brand-mark">价</view>
        <view class="titles">
          <view class="title">{{ title }}</view>
          <view v-if="subtitle" class="subtitle">{{ subtitle }}</view>
        </view>
      </view>
      <view class="context-chip" @click="showContext = true">
        <text class="dot"></text>
        <text class="context-text">{{ store.contextLabel }}</text>
        <text class="chevron">⌄</text>
      </view>
    </view>
    <ContextSheet v-model:visible="showContext" @change="emit('change')" />
  </view>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 8px;
}

.left {
  display: flex;
  align-items: center;
  min-width: 0;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: var(--ink);
  color: var(--amber);
  font-weight: 800;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  box-shadow: 0 8px 16px rgba(14, 27, 44, 0.18);
  flex-shrink: 0;
}

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: var(--card);
  border: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 10px;
  flex-shrink: 0;
}

.titles {
  min-width: 0;
}

.title {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.subtitle {
  font-size: 10px;
  color: var(--muted);
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.context-chip {
  display: flex;
  align-items: center;
  max-width: 210px;
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--card);
  border: 1px solid var(--line);
  font-size: 11px;
  color: var(--ink-soft);
  flex-shrink: 0;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  margin-right: 6px;
  flex-shrink: 0;
}

.context-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  margin-left: 4px;
  color: var(--muted);
}

@media (max-width: 520px) {
  .subtitle {
    display: none;
  }

  .context-chip {
    max-width: 132px;
  }

  .title {
    max-width: 170px;
  }
}
</style>
