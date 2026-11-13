<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  MEMBERSHIP_OPTIONS,
  REGION_OPTIONS,
  useAppStore,
} from "../stores/app";
import type { Preference } from "../api/types";

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits<{
  (event: "update:visible", value: boolean): void;
  (event: "change"): void;
}>();

const store = useAppStore();
const draftRegion = ref(store.region);
const draftMemberships = ref<string[]>([...store.memberships]);
const draftTradeIn = ref(store.tradeInEnabled);
const draftDevice = ref(store.tradeInDevice);
const draftEstimate = ref<number>(store.tradeInEstimate);
const draftPreference = ref<Preference>(store.preference);

watch(
  () => props.visible,
  (visible) => {
    if (!visible) return;
    draftRegion.value = store.region;
    draftMemberships.value = [...store.memberships];
    draftTradeIn.value = store.tradeInEnabled;
    draftDevice.value = store.tradeInDevice;
    draftEstimate.value = store.tradeInEstimate;
    draftPreference.value = store.preference;
  },
);

const regionIndex = computed(() =>
  Math.max(0, REGION_OPTIONS.indexOf(draftRegion.value)),
);

function onRegionChange(event: any) {
  const index = Number(event?.detail?.value ?? 0);
  draftRegion.value = REGION_OPTIONS[index] || "全国";
}

function toggleMembership(name: string) {
  if (draftMemberships.value.includes(name)) {
    draftMemberships.value = draftMemberships.value.filter(
      (item) => item !== name,
    );
  } else {
    draftMemberships.value = [...draftMemberships.value, name];
  }
}

function onTradeInChange(event: any) {
  draftTradeIn.value = Boolean(event?.detail?.value);
}

function apply() {
  store.region = draftRegion.value;
  store.memberships = [...draftMemberships.value];
  store.tradeInEnabled = draftTradeIn.value;
  store.tradeInDevice = draftDevice.value || "旧设备";
  store.tradeInEstimate = Math.max(0, Number(draftEstimate.value) || 0);
  store.preference = draftPreference.value;
  store.persist();
  emit("change");
  close();
}

function close() {
  emit("update:visible", false);
}
</script>

<template>
  <view v-if="visible" class="sheet-root">
    <view class="mask" @click="close"></view>
    <view class="sheet" @click.stop>
      <view class="handle"></view>
      <view class="sheet-head">
        <view>
          <view class="sheet-title">购买条件</view>
          <view class="sheet-sub">地区、会员和旧机估值会改变最优平台</view>
        </view>
        <view class="close" @click="close">×</view>
      </view>

      <view class="field">
        <text class="form-label">所在地区</text>
        <picker
          mode="selector"
          :range="REGION_OPTIONS"
          :value="regionIndex"
          @change="onRegionChange"
        >
          <view class="picker-field flex between">
            <text>{{ draftRegion }}</text>
            <text class="muted">⌄</text>
          </view>
        </picker>
      </view>

      <view class="field">
        <text class="form-label">会员身份</text>
        <view class="chip-row">
          <view
            v-for="name in MEMBERSHIP_OPTIONS"
            :key="name"
            class="chip"
            :class="{ 'chip-active': draftMemberships.includes(name) }"
            @click="toggleMembership(name)"
          >
            {{ name }}
          </view>
        </view>
        <view class="hint">演示规则中，88VIP 会改变淘宝会员价与返利结果。</view>
      </view>

      <view class="field">
        <view class="switch-row">
          <view>
            <text class="form-label">以旧换新</text>
            <view class="hint">仅部分平台/品类参与，旧机估值按你填写计算</view>
          </view>
          <switch
            :checked="draftTradeIn"
            color="#E9A23B"
            @change="onTradeInChange"
          />
        </view>
        <view v-if="draftTradeIn" class="trade-grid">
          <view>
            <text class="form-label">旧设备</text>
            <input
              v-model="draftDevice"
              class="input"
              placeholder="如：旧手机"
              placeholder-class="input-placeholder"
            />
          </view>
          <view>
            <text class="form-label">估值（元）</text>
            <input
              v-model="draftEstimate"
              class="input"
              type="digit"
              placeholder="300"
              placeholder-class="input-placeholder"
            />
          </view>
        </view>
      </view>

      <view class="field">
        <text class="form-label">排序偏好</text>
        <view class="chip-row">
          <view
            class="chip"
            :class="{ 'chip-active': draftPreference === 'payment' }"
            @click="draftPreference = 'payment'"
          >
            实付最低
          </view>
          <view
            class="chip"
            :class="{ 'chip-active': draftPreference === 'net' }"
            @click="draftPreference = 'net'"
          >
            净价最低（含返利）
          </view>
        </view>
      </view>

      <view class="notice">
        以上条件只影响本次演示计算，不会上传个人身份信息。
      </view>

      <view class="sheet-actions">
        <button class="btn btn-soft" @click="close">取消</button>
        <button class="btn btn-amber" @click="apply">应用条件</button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.sheet-root {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 90;
}

.mask {
  position: absolute;
  inset: 0;
  background: rgba(8, 16, 28, 0.48);
}

.sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  max-width: 720px;
  margin: 0 auto;
  max-height: 88vh;
  overflow-y: auto;
  padding: 10px 20px calc(20px + env(safe-area-inset-bottom));
  border-radius: 24px 24px 0 0;
  background: #fbf8f1;
  box-shadow: 0 -18px 60px rgba(8, 16, 28, 0.24);
}

.handle {
  width: 42px;
  height: 4px;
  border-radius: 999px;
  background: var(--line-strong);
  margin: 2px auto 16px;
}

.sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
}

.sheet-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.6px;
}

.sheet-sub {
  margin-top: 3px;
  font-size: 12px;
  color: var(--muted);
}

.close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--paper-deep);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  line-height: 1;
}

.field {
  margin-bottom: 18px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
}

.chip-row .chip {
  margin: 0 8px 8px 0;
}

.hint {
  margin-top: 5px;
  font-size: 11px;
  color: var(--muted);
  line-height: 1.5;
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

.sheet-actions {
  display: flex;
  margin-top: 16px;
}

.sheet-actions .btn {
  flex: 1;
}

.sheet-actions .btn:first-child {
  margin-right: 10px;
}
</style>
