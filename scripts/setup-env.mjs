#!/usr/bin/env node
/**
 * Creates a local .env from .env.example with generated development credentials.
 * Existing files are preserved unless --force is passed.
 */
import { randomBytes } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.join(root, ".env.example");
const target = path.join(root, ".env");
const force = process.argv.includes("--force");

if (existsSync(target) && !force) {
  console.log(".env already exists. Use `npm run setup:env -- --force` to replace it.");
  process.exit(0);
}

if (!existsSync(source)) {
  console.error("Missing .env.example at the repository root.");
  process.exit(1);
}

const password = randomBytes(24).toString("base64url");
const secretKey = randomBytes(48).toString("base64url");

const env = readFileSync(source, "utf8")
  .replaceAll("replace-with-a-strong-local-password", password)
  .replaceAll("replace-with-at-least-32-random-characters", secretKey);

writeFileSync(target, env, { encoding: "utf8", mode: 0o600 });
console.log("Created .env with generated development credentials.");
console.log("Next: npm install && npm run db:up && npm run migrate");
