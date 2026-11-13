const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env || {};

/**
 * Local demo default.  In the WeChat devtools, enable
 * "不校验合法域名" or point VITE_API_BASE at an HTTPS deployment.
 */
export const API_BASE = (env.VITE_API_BASE || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export const DATA_SOURCE_LABEL: Record<string, string> = {
  mock: "演示数据",
  mixed: "混合数据",
  affiliate: "联盟数据",
  user: "用户提交",
};
