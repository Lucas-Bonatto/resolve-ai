import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AppNavigation } from "../src/components/app-navigation";

vi.mock("next/navigation", () => ({ usePathname: () => "/evals" }));

describe("application navigation", () => {
  it("exposes active-route semantics and an explicit mobile menu state", () => {
    render(<AppNavigation />);

    expect(screen.getByRole("link", { name: "Evaluation" })).toHaveAttribute("aria-current", "page");
    const menu = screen.getByRole("button", { name: "Menu" });
    expect(menu).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(menu);
    expect(screen.getByRole("button", { name: "Close" })).toHaveAttribute("aria-expanded", "true");
  });
});
