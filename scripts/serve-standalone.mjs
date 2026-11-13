#!/usr/bin/env node
/**
 * Serves the production standalone build produced by `npm run build:web`.
 *
 * `next start` warns that it is incompatible with `output: "standalone"`, so
 * CI and local smoke tests use this wrapper instead. It copies the static
 * assets into the standalone tree first, exactly as the Docker image does.
 */
import { cpSync, existsSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const webDir = path.join(root, "apps", "web");
const standalone = path.join(webDir, ".next", "standalone");
const appDir = path.join(standalone, "apps", "web");
const serverEntry = path.join(appDir, "server.js");

export function prepareStandalone() {
  if (!existsSync(serverEntry)) {
    throw new Error(
      "Standalone server not found. Run `npm run build:web` before serving.",
    );
  }

  cpSync(path.join(webDir, ".next", "static"), path.join(appDir, ".next", "static"), {
    recursive: true,
  });

  const publicDir = path.join(webDir, "public");
  if (existsSync(publicDir)) {
    cpSync(publicDir, path.join(appDir, "public"), { recursive: true });
  }

  return serverEntry;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const entry = prepareStandalone();
  const child = spawn(process.execPath, [entry], {
    cwd: appDir,
    stdio: "inherit",
    env: {
      ...process.env,
      NODE_ENV: "production",
      PORT: process.env.PORT ?? "3000",
      HOSTNAME: process.env.HOSTNAME ?? "0.0.0.0",
    },
  });

  for (const signal of ["SIGINT", "SIGTERM", "SIGBREAK"]) {
    process.on(signal, () => child.kill(signal));
  }
  child.on("exit", (code, signal) => {
    if (signal) process.kill(process.pid, signal);
    else process.exit(code ?? 1);
  });
}
