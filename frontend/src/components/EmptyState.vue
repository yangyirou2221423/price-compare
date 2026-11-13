<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    description?: string;
    actionText?: string;
    icon?: string;
  }>(),
  { description: "", actionText: "", icon: "¥" },
);

const emit = defineEmits<{ (event: "action"): void }>();
</script>

<template>
  <view class="empty card">
    <view class="icon">{{ icon }}</view>
    <view class="title">{{ title }}</view>
    <view v-if="description" class="desc">{{ description }}</view>
    <button v-if="actionText" class="btn btn-primary mt-16" @click="emit('action')">
      {{ actionText }}
    </button>
  </view>
</template>

<style scoped>
.empty {
  padding: 44px 20px;
  text-align: center;
}

.icon {
  width: 58px;
  height: 58px;
  border-radius: 18px;
  background: var(--amber-soft);
  color: var(--amber-deep);
  font-size: 26px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}

.title {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.3px;
}

.desc {
  margin-top: 5px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--muted);
}
</style>
