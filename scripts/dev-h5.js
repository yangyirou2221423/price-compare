/* Dev-server wrapper used by the in-app Browser preview.
 * Sets the portable Node.js on PATH, then starts the uni-app H5 dev server.
 */
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const nodeDir = path.join(root, "tools", "node-v22.23.5-win-x64");
if (fs.existsSync(nodeDir)) {
  process.env.PATH = `${nodeDir};${process.env.PATH || ""}`;
}

const child = spawn(
  "npm.cmd",
  ["run", "dev:h5", "--", "--host", "127.0.0.1", "--port", "5173"],
  {
    cwd: path.join(root, "frontend"),
    stdio: "inherit",
    shell: true,
    env: process.env,
  },
);

child.on("exit", (code) => process.exit(code === null ? 0 : code));
process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGTERM", () => child.kill("SIGTERM"));
