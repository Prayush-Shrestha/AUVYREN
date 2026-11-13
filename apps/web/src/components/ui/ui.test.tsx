import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CircleAlert } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { Button, IconButton } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import {
  EmptyState,
  ErrorState,
  InlineMessage,
  Spinner,
} from "@/components/ui/states";

describe("Button", () => {
  it("marks itself busy and disabled while loading", () => {
    render(<Button loading>Saving</Button>);

    const button = screen.getByRole("button", { name: "Saving" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("defaults to type=button so forms are not submitted accidentally", () => {
    render(<Button>Plain</Button>);
    expect(screen.getByRole("button", { name: "Plain" })).toHaveAttribute(
      "type",
      "button",
    );
  });

  it("requires an accessible label for icon buttons", () => {
    render(
      <IconButton label="Close menu">
        <CircleAlert aria-hidden="true" />
      </IconButton>,
    );
    expect(screen.getByRole("button", { name: "Close menu" })).toBeEnabled();
  });
});

describe("Field", () => {
  it("connects a label and hint to the control", () => {
    render(
      <Field label="Email address" htmlFor="email" hint="We never share it.">
        <Input id="email" />
      </Field>,
    );

    const input = screen.getByLabelText("Email address");
    expect(input).toHaveAccessibleDescription("We never share it.");
  });

  it("announces errors and supports the optional marker", () => {
    render(
      <Field
        label="Full name"
        htmlFor="name"
        error="Use at least 2 characters."
        optional
      >
        <Input id="name" aria-invalid aria-describedby="name-error" />
      </Field>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Use at least 2 characters.",
    );
    expect(screen.getByText("Optional")).toBeInTheDocument();
    expect(screen.getByLabelText("Full name")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });
});

describe("state components", () => {
  it("renders an empty state with an action", () => {
    render(
      <EmptyState
        icon={CircleAlert}
        eyebrow="Notes"
        title="Nothing here yet"
        description="Capture a thought to begin."
        action={<button type="button">New note</button>}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Nothing here yet" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New note" })).toBeEnabled();
  });

  it("offers a retry action in the error state", async () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        description="The API could not be reached."
        onRetry={onRetry}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("maps inline message tones to live-region roles", () => {
    const { rerender } = render(
      <InlineMessage tone="danger" title="Failed">
        Try again later.
      </InlineMessage>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Failed");

    rerender(
      <InlineMessage tone="success" title="Saved">
        All good.
      </InlineMessage>,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Saved");
  });

  it("hides decorative spinners from assistive technology", () => {
    const { container } = render(<Spinner />);
    expect(container.firstElementChild).toHaveAttribute(
      "aria-hidden",
      "true",
    );
  });
});
