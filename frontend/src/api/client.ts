import { API_BASE } from "./config";
import type {
  CartItemInput,
  CartResponse,
  ConfigResponse,
  ContextPayload,
  HistoryResponse,
  HomeResponse,
  ProductDetailResponse,
  ProductListResponse,
  StrategyResult,
  SubmissionListResponse,
  SubmissionResponse,
  SubsidyCheckResponse,
} from "./types";

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type QueryValue = string | number | boolean | undefined | null;

function queryString(params: Record<string, QueryValue>): string {
  const pairs: string[] = [];
  Object.keys(params).forEach((key) => {
    const value = params[key];
    if (value === undefined || value === null || value === "") return;
    pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  });
  return pairs.length ? `?${pairs.join("&")}` : "";
}

function request<T>(
  path: string,
  options: { method?: "GET" | "POST" | "DELETE"; data?: unknown } = {},
): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method: options.method || "GET",
      data: options.data as Record<string, unknown> | undefined,
      timeout: 20000,
      header: { "Content-Type": "application/json" },
      success: (res) => {
        const status = res.statusCode || 0;
        if (status >= 200 && status < 300) {
          resolve(res.data as T);
          return;
        }
        const detail = (res.data as { detail?: unknown } | undefined)?.detail;
        let message = `请求失败（${status}）`;
        if (typeof detail === "string" && detail) {
          message = detail;
        } else if (Array.isArray(detail)) {
          message = detail
            .map((item) =>
              typeof item === "string"
                ? item
                : item && typeof item === "object" && "msg" in item
                  ? String((item as { msg: unknown }).msg)
                  : "",
            )
            .filter(Boolean)
            .join("；") || message;
        }
        reject(new ApiError(message, status));
      },
      fail: (err) => {
        reject(
          new ApiError(
            `无法连接后端：${err.errMsg || "网络错误"}。请确认 API 已启动（${API_BASE}）。`,
          ),
        );
      },
    });
  });
}

export interface ComparePayload extends ContextPayload {
  product_id: string;
}

export interface CartPayload extends ContextPayload {
  items: CartItemInput[];
  include_fillers?: boolean;
}

export interface SubsidyPayload {
  category: string;
  price: number;
  platform: string;
  region: string;
  memberships: string[];
  trade_in: ContextPayload["trade_in"];
}

export interface SubmissionPayload {
  product_id: string;
  platform: string;
  price: number;
  link?: string;
  note?: string;
}

export const api = {
  home: () => request<HomeResponse>("/api/home"),

  products: (params: { q?: string; category?: string; limit?: number } = {}) =>
    request<ProductListResponse>(`/api/products${queryString(params)}`),

  product: (productId: string) =>
    request<ProductDetailResponse>(`/api/products/${encodeURIComponent(productId)}`),

  config: () => request<ConfigResponse>("/api/config"),

  compare: (payload: ComparePayload) =>
    request<StrategyResult>("/api/compare", { method: "POST", data: payload }),

  strategy: (payload: ComparePayload) =>
    request<StrategyResult>("/api/strategy", { method: "POST", data: payload }),

  cart: (payload: CartPayload) =>
    request<CartResponse>("/api/cart/optimize", { method: "POST", data: payload }),

  history: (productId: string, days = 90, platform = "") =>
    request<HistoryResponse>(
      `/api/products/${encodeURIComponent(productId)}/history${queryString({ days, platform })}`,
    ),

  subsidy: (payload: SubsidyPayload) =>
    request<SubsidyCheckResponse>("/api/subsidy/check", {
      method: "POST",
      data: payload,
    }),

  submitPrice: (payload: SubmissionPayload) =>
    request<SubmissionResponse>("/api/submissions", {
      method: "POST",
      data: payload,
    }),

  submissions: () => request<SubmissionListResponse>("/api/submissions?limit=20"),

  deleteSubmission: (submissionId: number) =>
    request<{ deleted: number; message: string }>(
      `/api/submissions/${submissionId}`,
      { method: "DELETE" },
    ),
};
