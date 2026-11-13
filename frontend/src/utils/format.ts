export const PLATFORM_META: Record<
  string,
  { label: string; tone: string; mark: string }
> = {
  jd: { label: "京东", tone: "jd", mark: "京" },
  taobao: { label: "淘宝", tone: "taobao", mark: "淘" },
  pdd: { label: "拼多多", tone: "pdd", mark: "拼" },
  douyin: { label: "抖音", tone: "douyin", mark: "抖" },
};

export const KIND_LABEL: Record<string, string> = {
  store_coupon: "店铺券",
  platform_coupon: "平台券",
  category_coupon: "品类券",
  full_reduction: "满减",
  member: "会员价",
  platform_subsidy: "平台补贴",
  national_subsidy: "国补",
  trade_in: "以旧换新",
  payment_discount: "支付优惠",
  rebate: "返利",
  gift: "赠品",
};

export function formatMoney(value: number, withSymbol = true): string {
  const safe = Number.isFinite(value) ? value : 0;
  const hasCents = Math.abs(safe - Math.round(safe)) > 0.005;
  const text = safe.toLocaleString("zh-CN", {
    minimumFractionDigits: hasCents ? 2 : 0,
    maximumFractionDigits: 2,
  });
  return withSymbol ? `¥${text}` : text;
}

export function formatDiscount(value: number): string {
  if (!value) return "¥0";
  return `-${formatMoney(Math.abs(value))}`;
}

export function formatSigned(value: number): string {
  if (value > 0.005) return `+${formatMoney(value)}`;
  if (value < -0.005) return `-${formatMoney(Math.abs(value))}`;
  return "¥0";
}

export function formatPercent(value: number): string {
  const safe = Number.isFinite(value) ? value : 0;
  return `${Number.isInteger(safe) ? safe : safe.toFixed(1)}%`;
}

export function platformLabel(platform: string): string {
  return PLATFORM_META[platform]?.label || platform;
}

export function platformTone(platform: string): string {
  return PLATFORM_META[platform]?.tone || "default";
}

export function kindLabel(kind: string): string {
  return KIND_LABEL[kind] || kind;
}

export function shortDate(value: string): string {
  if (!value) return "";
  const date = value.slice(0, 10);
  const parts = date.split("-");
  if (parts.length === 3) return `${parts[1]}/${parts[2]}`;
  return date;
}

export function formatDateRange(points: { date: string }[]): string {
  if (!points.length) return "";
  return `${shortDate(points[0].date)} – ${shortDate(points[points.length - 1].date)}`;
}

export function sourceLabel(source: string): string {
  if (source === "mock") return "演示数据";
  if (source === "user") return "用户提交";
  if (source === "affiliate") return "联盟数据";
  if (source === "mixed") return "混合数据";
  return source || "演示数据";
}

export function trendText(value: number): string {
  if (Math.abs(value) < 0.005) return "持平";
  return value > 0 ? `上涨 ${formatMoney(value)}` : `下降 ${formatMoney(Math.abs(value))}`;
}
