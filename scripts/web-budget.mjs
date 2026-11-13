#!/usr/bin/env node
/**
 * Performance budget check for the production web build.
 *
 * Default mode (used by CI) inspects the gzipped size of everything emitted to
 * `.next/static`. Pass `--browser` to also boot the standalone server and
 * measure LCP/CLS and the decoded script/style weight of key routes.
 *
 * Budgets are deliberately generous enough for shared CI runners while still
 * catching accidental regressions (a new charting library, an unoptimised
 * image, a second font family).
 */
import { gzipSync } from "node:zlib";
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

import { prepareStandalone } from "./serve-standalone.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const webDir = path.join(root, "apps", "web");
const staticDir = path.join(webDir, ".next", "static");

const BUDGETS = {
  jsGzipKb: 340,
  cssGzipKb: 40,
  jsDecodedKb: 750,
  cssDecodedKb: 120,
  lcpMs: 2500,
  cls: 0.1,
};

const ROUTES = ["/", "/sign-in", "/design"];
const browserMode = process.argv.includes("--browser");

function walk(dir) {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(full));
    else if (entry.isFile()) files.push(full);
  }
  return files;
}

function gzipKb(file) {
  return gzipSync(readFileSync(file), { level: 9 }).length / 1024;
}

function staticBudget() {
  if (!existsSync(staticDir)) {
    throw new Error("No production build found. Run `npm run build:web` first.");
  }

  const files = walk(staticDir);
  const totals = { js: 0, css: 0 };
  for (const file of files) {
    if (file.endsWith(".js")) totals.js += gzipKb(file);
    else if (file.endsWith(".css")) totals.css += gzipKb(file);
  }

  console.log("Static assets (gzip):");
  console.log(`  JavaScript  ${totals.js.toFixed(1)} KB  (budget ${BUDGETS.jsGzipKb} KB)`);
  console.log(`  CSS         ${totals.css.toFixed(1)} KB  (budget ${BUDGETS.cssGzipKb} KB)`);

  const failures = [];
  if (totals.js > BUDGETS.jsGzipKb) failures.push("JavaScript gzip budget exceeded");
  if (totals.css > BUDGETS.cssGzipKb) failures.push("CSS gzip budget exceeded");
  return failures;
}

async function waitForServer(url, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // not up yet
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function browserBudget() {
  const { chromium } = await import("@playwright/test");
  prepareStandalone();

  const port = 3100;
  const origin = `http://127.0.0.1:${port}`;
  const server = spawn(process.execPath, ["scripts/serve-standalone.mjs"], {
    cwd: root,
    stdio: "ignore",
    env: { ...process.env, HOSTNAME: "127.0.0.1", PORT: String(port) },
  });

  const stop = () => {
    if (!server.killed) server.kill();
  };
  process.on("exit", stop);

  try {
    await waitForServer(`${origin}/sign-in`);
    const browser = await chromium.launch();
    const metrics = [];

    try {
      for (const route of ROUTES) {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        await page.addInitScript(() => {
          window.__auvyrenPerf = { lcp: 0, cls: 0 };
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries[entries.length - 1];
            if (last) window.__auvyrenPerf.lcp = last.startTime;
          }).observe({ type: "largest-contentful-paint", buffered: true });
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) window.__auvyrenPerf.cls += entry.value;
            }
          }).observe({ type: "layout-shift", buffered: true });
        });

        await page.goto(`${origin}${route}`, { waitUntil: "load" });
        await page.waitForLoadState("networkidle");
        await page.evaluate(() => document.fonts.ready);
        await page.waitForTimeout(600);

        const result = await page.evaluate(() => {
          const resources = performance.getEntriesByType("resource");
          const sum = (pattern) =>
            resources
              .filter((entry) => pattern.test(entry.name))
              .reduce((total, entry) => total + (entry.decodedBodySize || 0), 0);
          return {
            lcp: window.__auvyrenPerf.lcp,
            cls: window.__auvyrenPerf.cls,
            js: sum(/\.js(\?|$)/),
            css: sum(/\.css(\?|$)/),
          };
        });

        metrics.push({ route, ...result });
        await page.close();
      }
    } finally {
      await browser.close();
    }

    console.log("\nBrowser metrics (cold navigation, 1280x900):");
    const failures = [];
    for (const metric of metrics) {
      const jsKb = metric.js / 1024;
      const cssKb = metric.css / 1024;
      console.log(
        `  ${metric.route.padEnd(10)} LCP ${metric.lcp.toFixed(0)} ms  ` +
          `CLS ${metric.cls.toFixed(3)}  JS ${jsKb.toFixed(0)} KB  CSS ${cssKb.toFixed(0)} KB`,
      );
      if (metric.lcp > BUDGETS.lcpMs) failures.push(`${metric.route} LCP budget exceeded`);
      if (metric.cls > BUDGETS.cls) failures.push(`${metric.route} CLS budget exceeded`);
      if (jsKb > BUDGETS.jsDecodedKb) failures.push(`${metric.route} JS budget exceeded`);
      if (cssKb > BUDGETS.cssDecodedKb) failures.push(`${metric.route} CSS budget exceeded`);
    }
    console.log(
      `\nBudgets: LCP <= ${BUDGETS.lcpMs} ms, CLS <= ${BUDGETS.cls}, ` +
        `JS <= ${BUDGETS.jsDecodedKb} KB, CSS <= ${BUDGETS.cssDecodedKb} KB`,
    );
    return failures;
  } finally {
    stop();
  }
}

const failures = staticBudget();
if (browserMode) failures.push(...(await browserBudget()));

if (failures.length > 0) {
  console.error("\nPerformance budget failures:");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

console.log("\nAll performance budgets passed.");
