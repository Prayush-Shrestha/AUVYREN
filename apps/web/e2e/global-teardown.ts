import { execFileSync } from "node:child_process";
import path from "node:path";

export default function globalTeardown() {
  const root = path.resolve(__dirname, "../../..");
  try {
    execFileSync(
      process.execPath,
      ["scripts/api.mjs", "scripts/cleanup_e2e.py"],
      { cwd: root, stdio: "inherit" },
    );
  } catch (error) {
    console.warn("Could not clean up e2e accounts:", error);
  }
}
