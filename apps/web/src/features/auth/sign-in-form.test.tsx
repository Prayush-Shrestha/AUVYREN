import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SignInForm } from "@/features/auth/sign-in-form";
import { ApiError } from "@/lib/api/client";

const mocks = vi.hoisted(() => ({
  signIn: vi.fn(),
  replace: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ signIn: mocks.signIn }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace, refresh: mocks.refresh }),
}));

vi.mock("next/link", async () => {
  const React = await import("react");
  return {
    default: ({
      href,
      children,
      ...props
    }: React.ComponentProps<"a"> & { href: string }) =>
      React.createElement("a", { href, ...props }, children),
  };
});

describe("SignInForm", () => {
  it("blocks an empty submission with field-level guidance", async () => {
    const user = userEvent.setup();
    render(<SignInForm />);

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByText("Enter your email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
    expect(mocks.signIn).not.toHaveBeenCalled();
  });

  it("rejects a malformed email and a short password", async () => {
    const user = userEvent.setup();
    render(<SignInForm />);

    await user.type(screen.getByLabelText("Email address"), "not-an-email");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Use at least 12 characters.")).toBeInTheDocument();
    expect(mocks.signIn).not.toHaveBeenCalled();
  });

  it("signs in, trims the email and follows the next path", async () => {
    const user = userEvent.setup();
    mocks.signIn.mockResolvedValueOnce({ id: "1" });
    render(<SignInForm nextPath="/settings" />);

    await user.type(
      screen.getByLabelText("Email address"),
      "  ada@example.com  ",
    );
    await user.type(
      screen.getByLabelText("Password"),
      "correct horse battery staple",
    );
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(mocks.signIn).toHaveBeenCalledWith({
      email: "ada@example.com",
      password: "correct horse battery staple",
    });
    expect(mocks.replace).toHaveBeenCalledWith("/settings");
    expect(mocks.refresh).toHaveBeenCalledTimes(1);
  });

  it("surfaces API field errors and the form-level detail", async () => {
    const user = userEvent.setup();
    mocks.signIn.mockRejectedValueOnce(
      new ApiError({
        type: "https://auvyren.app/problems/invalid_credentials",
        title: "Sign-in failed",
        status: 401,
        detail: "The email or password is incorrect.",
        instance: "/api/v1/auth/login",
        code: "invalid_credentials",
        errors: [
          { field: "body.email", message: "No account uses this email.", type: "value_error" },
        ],
      }),
    );
    render(<SignInForm />);

    await user.type(screen.getByLabelText("Email address"), "ada@example.com");
    await user.type(
      screen.getByLabelText("Password"),
      "correct horse battery staple",
    );
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("The email or password is incorrect."),
    ).toBeInTheDocument();
    expect(screen.getByText("No account uses this email.")).toBeInTheDocument();
    expect(mocks.replace).not.toHaveBeenCalled();
  });

  it("explains an expired session before the form", () => {
    render(<SignInForm reason="expired" />);
    expect(screen.getByText("Your session ended")).toBeInTheDocument();
  });
});
