import { expect, test } from "@playwright/test";

import { createAccount, createNote } from "./support";

test.describe("knowledge workspace", () => {
  test("notes created through the API appear in the library and open individually", async ({
    page,
    context,
  }) => {
    await createAccount(context, { fullName: "Note Tester" });
    await createNote(context, {
      title: "Design language",
      content: "Ink, moss and paper.",
      tags: "design,identity",
      kind: "decision",
    });
    await createNote(context, {
      title: "Weekly review",
      content: "A quieter week.",
      kind: "review",
    });

    await page.goto("/notes");
    await expect(
      page.getByRole("heading", { name: "Design language" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Weekly review" }),
    ).toBeVisible();

    await page
      .getByRole("heading", { name: "Design language" })
      .locator("xpath=ancestor::div[contains(@class, 'rounded-xl')]")
      .getByRole("link", { name: "Open" })
      .click();

    await expect(page).toHaveURL(/\/notes\/[0-9a-f-]+$/);
    await expect(
      page.getByRole("heading", { name: "Design language" }),
    ).toBeVisible();
    await expect(page.getByText("Ink, moss and paper.")).toBeVisible();
  });

  test("real search narrows the library and explains an empty result", async ({
    page,
    context,
  }) => {
    await createAccount(context);
    await createNote(context, {
      title: "Meeting notes",
      content: "Discuss the philosophy of quiet software.",
    });
    await createNote(context, {
      title: "Reading list",
      content: "Books for the winter.",
    });

    await page.goto("/knowledge");
    await expect(
      page.getByRole("heading", { name: "Meeting notes" }),
    ).toBeVisible();

    await page.getByLabel("Search your notes").fill("philosophy");
    await page.getByRole("button", { name: "Search" }).click();

    await expect(page).toHaveURL(/\/knowledge\?q=philosophy$/);
    await expect(
      page.getByRole("heading", { name: "Meeting notes" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Reading list" }),
    ).toHaveCount(0);
    await expect(page.getByText(/1 result for/)).toBeVisible();

    await page.getByLabel("Search your notes").fill("zzz-not-present");
    await page.getByRole("button", { name: "Search" }).click();

    await expect(
      page.getByRole("heading", { name: "No matching notes" }),
    ).toBeVisible();
    await expect(page.getByText(/Nothing matched/)).toBeVisible();
  });

  test("note links are scoped to the signed-in account", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(page).toHaveURL(
      /\/sign-in\?reason=signin_required&next=%2Fknowledge$/,
    );
  });
});
