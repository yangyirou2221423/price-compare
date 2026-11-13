<script setup lang="ts">
import { onLaunch } from "@dcloudio/uni-app";

onLaunch(() => {
  // Keep the demo quiet in production builds; useful in the console when
  // debugging API connectivity.
  console.log("[价策] demo launched");
});
</script>

<style>
page,
:root {
  --ink: #0e1b2c;
  --ink-soft: #203449;
  --paper: #f6f3ec;
  --paper-deep: #efe9dc;
  --card: #ffffff;
  --amber: #e9a23b;
  --amber-soft: #f7e3bf;
  --amber-deep: #a9680f;
  --green: #1f7a5c;
  --green-soft: #dcede6;
  --red: #c2543c;
  --red-soft: #f7e1da;
  --muted: #6f7b8d;
  --muted-light: #9aa3b0;
  --line: #e6dfd2;
  --line-strong: #d8cfbe;
}

page {
  min-height: 100%;
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", sans-serif;
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}

/* #ifdef H5 */
body {
  margin: 0;
  background: radial-gradient(circle at 18% 0%, #fffaee 0, #f6f3ec 42%, #f1ece2 100%);
  min-height: 100vh;
}
/* #endif */

view,
text,
button,
input,
textarea,
scroll-view {
  box-sizing: border-box;
}

.page-shell {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 18px 110px;
}

.page-shell--narrow {
  max-width: 860px;
}

.top-safe {
  padding-top: var(--status-bar-height, 0px);
}

.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: 0 12px 30px rgba(14, 27, 44, 0.055);
}

.card-pad {
  padding: 18px;
}

.section {
  margin-top: 26px;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 13px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--ink);
}

.section-sub {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.eyebrow {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 2.2px;
  text-transform: uppercase;
  color: var(--amber-deep);
}

.muted {
  color: var(--muted);
}

.small {
  font-size: 13px;
}

.tiny {
  font-size: 11px;
}

.money {
  font-family: "DIN Alternate", "Bahnschrift", "Consolas", monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.6px;
  font-weight: 800;
}

.money-lg {
  font-family: "DIN Alternate", "Bahnschrift", "Consolas", monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: -1.2px;
  font-weight: 800;
}

.flex {
  display: flex;
  align-items: center;
}

.between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.wrap {
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  margin: 0;
  border: 0;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
  background: transparent;
  color: var(--ink);
}

.btn::after {
  border: 0;
}

.btn-primary {
  background: var(--ink);
  color: #fff8ea;
}

.btn-amber {
  background: var(--amber);
  color: #2a1a00;
  box-shadow: 0 8px 18px rgba(233, 162, 59, 0.28);
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--line-strong);
  color: var(--ink);
}

.btn-soft {
  background: var(--paper-deep);
  color: var(--ink);
}

.btn-block {
  width: 100%;
}

.btn-sm {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 11px;
  font-size: 13px;
}

.btn[disabled] {
  opacity: 0.48;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--paper-deep);
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 650;
  border: 1px solid transparent;
}

.chip-active {
  background: var(--ink);
  color: #fff7e9;
}

.chip-ghost {
  background: transparent;
  border-color: var(--line-strong);
}

.chip-amber {
  background: var(--amber-soft);
  color: var(--amber-deep);
}

.chip-green {
  background: var(--green-soft);
  color: var(--green);
}

.chip-red {
  background: var(--red-soft);
  color: var(--red);
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 8px;
  background: var(--paper-deep);
  color: var(--muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.4px;
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 14px 0;
}

.notice {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--paper-deep);
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.notice--amber {
  background: #fdf3df;
  color: #7a4d08;
}

.notice--red {
  background: var(--red-soft);
  color: #8b3524;
}

.grid-products {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.grid-products > .grid-item {
  width: 48.6%;
  margin-bottom: 16px;
}

.stat-grid {
  display: flex;
  flex-wrap: wrap;
}

.stat-grid > .stat {
  width: 50%;
  padding: 8px 0;
}

.form-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  margin-bottom: 7px;
}

.input,
.picker-field {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fbf8f2;
  color: var(--ink);
  font-size: 15px;
  line-height: 44px;
}

.input-placeholder {
  color: var(--muted-light);
}

.loading {
  padding: 40px 0;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}

.skeleton {
  background: linear-gradient(90deg, #eee8dc 25%, #f8f4eb 37%, #eee8dc 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 12px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: 0 0;
  }
}

.fade-in {
  animation: rise 0.38s ease both;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.safe-bottom {
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}

.mt-8 {
  margin-top: 8px;
}

.mt-12 {
  margin-top: 12px;
}

.mt-16 {
  margin-top: 16px;
}

.mt-24 {
  margin-top: 24px;
}

.w-full {
  width: 100%;
}

@media (max-width: 720px) {
  .page-shell {
    padding: 0 14px 100px;
  }

  .grid-products > .grid-item {
    width: 100%;
    margin-bottom: 14px;
  }

  .section-title {
    font-size: 18px;
  }
}
</style>
