#!/usr/bin/env node
/**
 * Runs a Python command from apps/api using the project virtual environment.
 * Usage: node scripts/api.mjs -m pytest
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const apiDir = path.join(root, "apps", "api");
const venvPython =
  process.platform === "win32"
    ? path.join(apiDir, ".venv", "Scripts", "python.exe")
    : path.join(apiDir, ".venv", "bin", "python");
// CI installs into the runner's Python; developers use the project venv.
const python = existsSync(venvPython)
  ? venvPython
  : process.platform === "win32"
    ? "python"
    : "python3";

const child = spawn(python, process.argv.slice(2), {
  cwd: apiDir,
  stdio: "inherit",
  env: { ...process.env, PYTHONUNBUFFERED: "1" },
});

child.on("error", (error) => {
  console.error(`Failed to start the API command: ${error.message}`);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
