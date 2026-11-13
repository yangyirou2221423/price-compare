export type Preference = "payment" | "net";

export interface TradeInPayload {
  device_name: string;
  estimate: number;
}

export interface ContextPayload {
  region: string;
  memberships: string[];
  trade_in: TradeInPayload | null;
  preference: Preference;
}

export interface AppliedBenefit {
  benefit_id: string;
  name: string;
  kind: string;
  stage: number;
  amount: number;
  price_before: number;
  price_after: number;
  is_net_benefit: boolean;
  description: string;
  rule_id?: string | null;
}

export interface RejectedBenefit {
  benefit_id: string;
  name: string;
  reason_code: string;
  reason: string;
}

export interface PlatformResult {
  offer_id: string;
  platform: string;
  platform_name: string;
  shop_name: string;
  list_price: number;
  shipping_fee: number;
  base_price: number;
  goods_price: number;
  final_price: number;
  net_price: number;
  discount_total: number;
  promo_savings: number;
  trade_in_value: number;
  rebate_value: number;
  gift_value: number;
  savings_pct: number;
  applied: AppliedBenefit[];
  rejected: RejectedBenefit[];
  optimal: boolean;
  note: string;
}

export interface StrategyResult {
  product_id: string;
  product_title: string;
  product_image: string;
  product_category: string;
  region: string;
  preference: Preference;
  best_platform: string;
  best_offer_id: string;
  best: PlatformResult;
  results: PlatformResult[];
  savings_abs: number;
  savings_pct: number;
  summary: string;
  assumptions: string[];
  engine_version: string;
  data_source: string;
  generated_at: string;
  optimal: boolean;
}

export interface Requirements {
  memberships: string[];
  regions: string[];
  trade_in: boolean;
  first_order: boolean;
  min_quantity: number;
}

export interface Benefit {
  id: string;
  name: string;
  kind: string;
  scope: string;
  value_type: string;
  value: number;
  threshold: number;
  step?: number | null;
  max_discount?: number | null;
  threshold_base: string;
  price_cap?: number | null;
  price_cap_base: string;
  stage: number;
  stack_group?: string | null;
  exclusive_with: string[];
  requires: Requirements;
  valid_from?: string | null;
  valid_to?: string | null;
  description: string;
  source: string;
  rule_id?: string | null;
}

export interface Offer {
  id: string;
  product_id: string;
  platform: string;
  platform_name: string;
  shop_name: string;
  list_price: number;
  shipping_fee: number;
  url: string;
  source: string;
  updated_at?: string | null;
  benefits: Benefit[];
}

export interface Product {
  id: string;
  title: string;
  brand: string;
  model: string;
  category: string;
  specs: string;
  image: string;
  tags: string[];
  description: string;
  featured: boolean;
  offers: Offer[];
}

export interface OfferBrief {
  offer_id: string;
  platform: string;
  platform_name: string;
  shop_name: string;
  list_price: number;
  shipping_fee: number;
  source: string;
}

export interface ProductDetailResponse {
  product: Product;
  offers: OfferBrief[];
}

export interface ProductCard {
  id: string;
  title: string;
  brand: string;
  category: string;
  specs: string;
  image: string;
  tags: string[];
  featured: boolean;
  offer_count: number;
  best_platform: string;
  best_platform_name: string;
  best_price: number;
  net_price: number;
  list_price: number;
  savings: number;
  savings_pct: number;
  summary: string;
  data_source: string;
}

export interface ProductListResponse {
  products: ProductCard[];
  total: number;
}

export interface HomeResponse {
  products: ProductCard[];
  regions: string[];
  memberships: string[];
  default_region: string;
  generated_at: string;
  data_note: string;
}

export interface CartItemInput {
  product_id: string;
  quantity: number;
}

export interface CartLine {
  product_id: string;
  title: string;
  category: string;
  quantity: number;
  unit_price: number;
  list_subtotal: number;
  line_discount: number;
  line_final: number;
  applied: AppliedBenefit[];
}

export interface CartOrder {
  platform: string;
  platform_name: string;
  lines: CartLine[];
  list_subtotal: number;
  line_discount_total: number;
  order_discount_total: number;
  final_price: number;
  net_price: number;
  rebate_value: number;
  order_applied: AppliedBenefit[];
  order_rejected: RejectedBenefit[];
}

export interface CartResult {
  region: string;
  preference: Preference;
  orders: CartOrder[];
  total_payment: number;
  total_net: number;
  baseline_payment: number;
  baseline_platform: string;
  savings_vs_baseline: number;
  optimal: boolean;
  assignment: Record<string, string>;
  notes: string[];
  engine_version: string;
  generated_at: string;
}

export interface FillerCandidate {
  product_id: string;
  title: string;
  image: string;
  price: number;
  new_total: number;
  net_increase: number;
  reason: string;
}

export interface FillerSuggestion {
  platform: string;
  platform_name: string;
  benefit_id: string;
  benefit_name: string;
  gap: number;
  candidates: FillerCandidate[];
  warning: string;
}

export interface CartResponse {
  cart: CartResult;
  fillers: FillerSuggestion[];
}

export interface PricePoint {
  date: string;
  price: number;
}

export interface PriceHistoryAnalysis {
  product_id: string;
  platform: string;
  platform_name: string;
  days: number;
  points: PricePoint[];
  current_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  p25: number;
  p75: number;
  percentile: number;
  is_low: boolean;
  lowest_30d: number;
  lowest_90d: number;
  trend_7d: number;
  trend_7d_pct: number;
  fake_drop: boolean;
  verdict: string;
  generated_at: string;
}

export interface HistoryResponse {
  product_id: string;
  product_title: string;
  days: number;
  series: PriceHistoryAnalysis[];
  data_note: string;
}

export interface SubsidyCheckItem {
  rule_id: string;
  name: string;
  eligible: boolean;
  amount: number;
  reason: string;
  description: string;
  source: string;
  version: string;
  effective: string;
}

export interface SubsidyCheckResponse {
  category: string;
  price: number;
  platform: string;
  platform_name: string;
  region: string;
  total_estimated: number;
  items: SubsidyCheckItem[];
  notes: string[];
}

export interface SubmissionResponse {
  id: number;
  message: string;
  created_at: string;
}

export interface SubmissionListResponse {
  submissions: SubmissionResponse[];
  total: number;
}

export interface PlatformInfo {
  id: string;
  name: string;
  short: string;
}

export interface ConfigResponse {
  platforms: PlatformInfo[];
  regions: string[];
  memberships: string[];
  categories: string[];
  engine_version: string;
  data_note: string;
}
