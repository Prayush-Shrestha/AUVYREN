import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { createAccount } from "./support";

async function expectNoViolations(page: Page, label: string) {
  await page.evaluate(() => document.fonts.ready.then(() => true));

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();

  const violations = results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    help: violation.help,
    nodes: violation.nodes.map((node) => ({
      target: node.target.join(" "),
      summary: node.failureSummary,
      checks: node.any.map((check) => ({ id: check.id, data: check.data })),
    })),
  }));

  expect(
    violations,
    `${label} has accessibility violations:\n${JSON.stringify(violations, null, 2)}`,
  ).toEqual([]);
}

test.describe("accessibility", () => {
  // Reveal animations are disabled under reduced motion; scanning in this mode
  // keeps measurements stable and verifies the calmer, accessible variant.
  test.use({ reducedMotion: "reduce" });

  test("the landing page passes WCAG A/AA checks", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { level: 1, name: /Make room for what matters/i }),
    ).toBeVisible();
    await expectNoViolations(page, "landing page");
  });

  test("the sign-in and sign-up pages pass WCAG A/AA checks", async ({
    page,
  }) => {
    await page.goto("/sign-in");
    await expectNoViolations(page, "sign-in page");

    await page.goto("/sign-up");
    await expectNoViolations(page, "sign-up page");
  });

  test("the design catalogue passes WCAG A/AA checks", async ({ page }) => {
    await page.goto("/design");
    await expectNoViolations(page, "design catalogue");
  });

  test("workspace pages pass WCAG A/AA checks", async ({ page, context }) => {
    await createAccount(context);

    for (const [path, label] of [
      ["/dashboard", "dashboard"],
      ["/intelligence", "intelligence"],
      ["/notes", "notes"],
      ["/knowledge", "knowledge"],
      ["/settings", "settings"],
    ] as const) {
      await page.goto(path);
      await expect(page.locator("#main-content")).toBeVisible();
      await expectNoViolations(page, label);
    }
  });

  test("the skip link is the first keyboard stop and reaches the main region", async ({
    page,
  }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");

    const skip = page.getByRole("link", { name: "Skip to content" });
    await expect(skip).toBeFocused();

    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#main-content$/);
    await expect(page.locator("#main-content")).toBeFocused();
  });

  test("reduced motion removes long transitions without hiding content", async ({
    page,
  }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");

    await expect(page.getByRole("contentinfo")).toBeVisible();

    const slow = await page.evaluate(() => {
      const parse = (value: string) =>
        Math.max(
          0,
          ...value.split(",").map((part) => parseFloat(part) || 0),
        );
      return [...document.querySelectorAll<HTMLElement>("body *")]
        .filter((element) => {
          const style = getComputedStyle(element);
          return (
            parse(style.transitionDuration) > 0.05 ||
            parse(style.animationDuration) > 0.05
          );
        })
        .slice(0, 10)
        .map((element) => element.tagName.toLowerCase());
    });

    expect(slow).toEqual([]);
  });
});
