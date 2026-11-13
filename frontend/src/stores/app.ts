import { computed, ref } from "vue";
import { defineStore } from "pinia";
import type {
  ContextPayload,
  FillerCandidate,
  Preference,
} from "../api/types";

const STORAGE_KEY = "pricecompare.app.v1";

export const REGION_OPTIONS = [
  "全国",
  "浙江",
  "江苏",
  "上海",
  "广东",
  "北京",
  "四川",
  "湖北",
];

export const MEMBERSHIP_OPTIONS = ["88VIP", "京东 PLUS", "拼多多省钱月卡"];

export interface CartItem {
  productId: string;
  title: string;
  image: string;
  category: string;
  unitPrice: number;
  quantity: number;
}

export interface FavoriteItem {
  id: string;
  title: string;
  image: string;
  price: number;
  category: string;
}

interface PersistedState {
  region?: string;
  memberships?: string[];
  tradeInEnabled?: boolean;
  tradeInDevice?: string;
  tradeInEstimate?: number;
  preference?: Preference;
  cartItems?: CartItem[];
  favorites?: FavoriteItem[];
}

export const useAppStore = defineStore("app", () => {
  const region = ref("浙江");
  const memberships = ref<string[]>([]);
  const tradeInEnabled = ref(false);
  const tradeInDevice = ref("旧手机 / 旧家电");
  const tradeInEstimate = ref(300);
  const preference = ref<Preference>("payment");
  const cartItems = ref<CartItem[]>([]);
  const favorites = ref<FavoriteItem[]>([]);

  const contextPayload = computed<ContextPayload>(() => ({
    region: region.value,
    memberships: [...memberships.value],
    trade_in: tradeInEnabled.value
      ? {
          device_name: tradeInDevice.value || "旧设备",
          estimate: Math.max(0, Number(tradeInEstimate.value) || 0),
        }
      : null,
    preference: preference.value,
  }));

  const contextLabel = computed(() => {
    const parts = [region.value];
    if (memberships.value.length) {
      parts.push(memberships.value.join(" / "));
    }
    if (tradeInEnabled.value) {
      parts.push("以旧换新");
    }
    return parts.join(" · ");
  });

  const cartCount = computed(() =>
    cartItems.value.reduce((sum, item) => sum + item.quantity, 0),
  );

  const cartSubtotal = computed(() =>
    cartItems.value.reduce(
      (sum, item) => sum + item.unitPrice * item.quantity,
      0,
    ),
  );

  function persist() {
    const payload: PersistedState = {
      region: region.value,
      memberships: memberships.value,
      tradeInEnabled: tradeInEnabled.value,
      tradeInDevice: tradeInDevice.value,
      tradeInEstimate: tradeInEstimate.value,
      preference: preference.value,
      cartItems: cartItems.value,
      favorites: favorites.value,
    };
    try {
      uni.setStorageSync(STORAGE_KEY, payload);
    } catch (error) {
      console.warn("save preference failed", error);
    }
  }

  function load() {
    try {
      const raw = uni.getStorageSync(STORAGE_KEY);
      if (!raw) return;
      const saved: PersistedState =
        typeof raw === "string" ? JSON.parse(raw) : (raw as PersistedState);
      if (saved.region) region.value = saved.region;
      if (Array.isArray(saved.memberships)) memberships.value = saved.memberships;
      if (typeof saved.tradeInEnabled === "boolean") {
        tradeInEnabled.value = saved.tradeInEnabled;
      }
      if (saved.tradeInDevice) tradeInDevice.value = saved.tradeInDevice;
      if (typeof saved.tradeInEstimate === "number") {
        tradeInEstimate.value = saved.tradeInEstimate;
      }
      if (saved.preference === "payment" || saved.preference === "net") {
        preference.value = saved.preference;
      }
      if (Array.isArray(saved.cartItems)) cartItems.value = saved.cartItems;
      if (Array.isArray(saved.favorites)) favorites.value = saved.favorites;
    } catch (error) {
      console.warn("load preference failed", error);
    }
  }

  function toggleMembership(name: string) {
    if (memberships.value.includes(name)) {
      memberships.value = memberships.value.filter((item) => item !== name);
    } else {
      memberships.value = [...memberships.value, name];
    }
    persist();
  }

  function addToCart(
    item: Omit<CartItem, "quantity">,
    quantity = 1,
  ) {
    const existing = cartItems.value.find(
      (cartItem) => cartItem.productId === item.productId,
    );
    if (existing) {
      existing.quantity = Math.min(99, existing.quantity + quantity);
    } else {
      cartItems.value = [
        ...cartItems.value,
        { ...item, quantity: Math.max(1, quantity) },
      ];
    }
    persist();
  }

  function addFiller(candidate: FillerCandidate) {
    addToCart({
      productId: candidate.product_id,
      title: candidate.title,
      image: candidate.image,
      category: "",
      unitPrice: candidate.price,
    });
  }

  function updateQuantity(productId: string, quantity: number) {
    const next = Math.max(1, Math.min(99, Math.round(quantity) || 1));
    cartItems.value = cartItems.value.map((item) =>
      item.productId === productId ? { ...item, quantity: next } : item,
    );
    persist();
  }

  function removeFromCart(productId: string) {
    cartItems.value = cartItems.value.filter(
      (item) => item.productId !== productId,
    );
    persist();
  }

  function clearCart() {
    cartItems.value = [];
    persist();
  }

  function isFavorite(productId: string) {
    return favorites.value.some((item) => item.id === productId);
  }

  function toggleFavorite(item: FavoriteItem) {
    if (isFavorite(item.id)) {
      favorites.value = favorites.value.filter((fav) => fav.id !== item.id);
    } else {
      favorites.value = [item, ...favorites.value];
    }
    persist();
    return isFavorite(item.id);
  }

  function resetAll() {
    region.value = "浙江";
    memberships.value = [];
    tradeInEnabled.value = false;
    tradeInDevice.value = "旧手机 / 旧家电";
    tradeInEstimate.value = 300;
    preference.value = "payment";
    cartItems.value = [];
    favorites.value = [];
    persist();
  }

  load();

  return {
    region,
    memberships,
    tradeInEnabled,
    tradeInDevice,
    tradeInEstimate,
    preference,
    cartItems,
    favorites,
    contextPayload,
    contextLabel,
    cartCount,
    cartSubtotal,
    toggleMembership,
    addToCart,
    addFiller,
    updateQuantity,
    removeFromCart,
    clearCart,
    isFavorite,
    toggleFavorite,
    resetAll,
    persist,
  };
});
