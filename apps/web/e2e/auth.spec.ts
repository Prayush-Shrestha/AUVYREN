import { expect, test } from "@playwright/test";

import {
  PASSWORD,
  createAccount,
  registerAccount,
  uniqueEmail,
} from "./support";

test.describe("authentication", () => {
  test("a visitor can create an account and enter the workspace", async ({
    page,
  }) => {
    const email = uniqueEmail("signup");

    await page.goto("/sign-up");
    await expect(
      page.getByRole("heading", { name: "Begin with a quieter default." }),
    ).toBeVisible();

    await page.getByLabel("Your name").fill("Ada Lovelace");
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(
      page.getByRole("heading", { name: "Welcome back, Ada." }),
    ).toBeVisible();

    const session = (await page.context().cookies()).find(
      (cookie) => cookie.name === "auv_session",
    );
    expect(session?.httpOnly).toBe(true);
    expect(session?.sameSite).toBe("Lax");
  });

  test("empty and malformed submissions are refused before the API", async ({
    page,
  }) => {
    await page.goto("/sign-in");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("Enter your email address.")).toBeVisible();
    await expect(page.getByText("Enter your password.")).toBeVisible();
    await expect(page).toHaveURL(/\/sign-in$/);

    await page.getByLabel("Email address").fill("not-an-email");
    await page.getByLabel("Password").fill("short");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("Enter a valid email address.")).toBeVisible();
    await expect(page.getByText("Use at least 12 characters.")).toBeVisible();
    await expect(page).toHaveURL(/\/sign-in$/);
  });

  test("a wrong password is reported without revealing account existence", async ({
    page,
  }) => {
    const { email } = await registerAccount({ prefix: "wrong-password" });

    await page.goto("/sign-in");
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password").fill("this is not the password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Email or password is incorrect.")).toBeVisible();
    await expect(page).toHaveURL(/\/sign-in$/);
  });

  test("a protected workspace survives a sign-in round trip", async ({ page }) => {
    const { email, password } = await registerAccount({ prefix: "protected" });

    await page.goto("/settings");
    await expect(page).toHaveURL(
      /\/sign-in\?reason=signin_required&next=%2Fsettings$/,
    );
    await expect(page.getByText("Sign in to continue")).toBeVisible();

    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/settings$/);
    await expect(
      page.getByRole("heading", { name: "Shape the space around you." }),
    ).toBeVisible();
  });

  test("the account menu signs out and clears the session cookie", async ({
    page,
    context,
  }) => {
    await createAccount(context, { fullName: "Grace Hopper" });
    await page.goto("/dashboard");
    await expect(
      page.getByRole("heading", { name: "Welcome back, Grace." }),
    ).toBeVisible();

    await page
      .getByRole("button", { name: /account menu for Grace Hopper/ })
      .click();
    await page.getByRole("menuitem", { name: "Sign out" }).click();

    await expect(page).toHaveURL(/\/sign-in\?reason=signed_out$/);
    await expect(page.getByText("You are signed out")).toBeVisible();
    await expect
      .poll(
        async () =>
          (await context.cookies()).some(
            (cookie) => cookie.name === "auv_session",
          ),
        { message: "session cookie should be cleared after sign-out" },
      )
      .toBe(false);
  });
});
