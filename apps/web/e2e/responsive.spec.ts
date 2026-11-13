import { expect, test, type Page } from "@playwright/test";

import { createAccount, createNote } from "./support";

async function expectNoHorizontalOverflow(page: Page, label: string) {
  await page.evaluate(() => document.fonts.ready.then(() => true));
  const { scrollWidth, innerWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(
    scrollWidth,
    `${label} overflows horizontally (${scrollWidth}px > ${innerWidth}px)`,
  ).toBeLessThanOrEqual(innerWidth + 1);
}

test.describe("mobile responsiveness", () => {
  test("the landing page fits the viewport and offers the mobile menu", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { level: 1, name: /Make room for what matters/i }),
    ).toBeVisible();
    await expectNoHorizontalOverflow(page, "landing page");

    await page.getByRole("button", { name: "Open navigation" }).click();
    const dialog = page.getByRole("dialog", { name: "Auvyren" });
    await expect(dialog).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();

    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .getByRole("dialog", { name: "Auvyren" })
      .getByRole("link", { name: "Sign in" })
      .click();

    await expect(page).toHaveURL(/\/sign-in$/);
    await expect(
      page.getByRole("heading", { name: "Return to your space." }),
    ).toBeVisible();
    await expectNoHorizontalOverflow(page, "sign-in page");
  });

  test("the workspace navigation opens, closes and reaches knowledge", async ({
    page,
    context,
  }) => {
    await createAccount(context, { fullName: "Mobile Tester" });
    await page.goto("/dashboard");
    await expect(
      page.getByRole("heading", { name: "Welcome back, Mobile." }),
    ).toBeVisible();
    await expectNoHorizontalOverflow(page, "dashboard");

    await page
      .getByRole("button", { name: "Open workspace navigation" })
      .click();
    const dialog = page.getByRole("dialog", { name: "Workspace" });
    await expect(dialog).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();

    await page
      .getByRole("button", { name: "Open workspace navigation" })
      .click();
    await dialog.getByRole("link", { name: "Knowledge" }).click();

    await expect(page).toHaveURL(/\/knowledge$/);
    await expect(
      page.getByRole("heading", { name: "Welcome back, Mobile." }),
    ).toBeVisible();
    await expect(dialog).toBeHidden();
    await expectNoHorizontalOverflow(page, "knowledge page");
  });

  test("knowledge search remains usable on a narrow screen", async ({
    page,
    context,
  }) => {
    await createAccount(context);
    await createNote(context, {
      title: "Pocket note",
      content: "Captured on the small screen.",
    });

    await page.goto("/knowledge");
    await page.getByLabel("Search your notes").fill("Pocket");
    await page.getByRole("button", { name: "Search" }).click();

    await expect(page).toHaveURL(/\/knowledge\?q=Pocket$/);
    await expect(
      page.getByRole("heading", { name: "Pocket note" }),
    ).toBeVisible();
    await expectNoHorizontalOverflow(page, "knowledge search results");
  });
});
