<script setup lang="ts">
import { computed } from "vue";
import { sourceLabel } from "../utils/format";

const props = withDefaults(
  defineProps<{ source: string; prefix?: string }>(),
  { prefix: "" },
);

const label = computed(() => `${props.prefix}${sourceLabel(props.source)}`);
</script>

<template>
  <view class="source-badge">
    <text class="source-dot"></text>
    <text>{{ label }}</text>
  </view>
</template>

<style scoped>
.source-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--paper-deep);
  color: var(--muted);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.source-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--amber);
  margin-right: 5px;
}
</style>
