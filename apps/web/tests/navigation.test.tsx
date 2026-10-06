import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AppNavigation } from "../src/components/app-navigation";
import { api } from "../src/lib/api";

vi.mock("next/navigation", () => ({ usePathname: () => "/evals" }));
vi.mock("../src/lib/api", () => ({ api: { runtime: vi.fn() } }));

describe("application navigation", () => {
  it("exposes active-route semantics and an explicit mobile menu state", async () => {
    vi.mocked(api.runtime).mockResolvedValue({ deployment_profile: "local", interactive: true, mutations_allowed: true, real_ai_enabled: false, fictional_data: true });
    render(<AppNavigation />);

    expect(await screen.findByText("Ambiente de demonstração")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Avaliações" })).toHaveAttribute("aria-current", "page");
    const menu = screen.getByRole("button", { name: "Menu" });
    expect(menu).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(menu);
    expect(screen.getByRole("button", { name: "Fechar" })).toHaveAttribute("aria-expanded", "true");
  });

  it("labels the public showcase as read-only", async () => {
    vi.mocked(api.runtime).mockResolvedValue({ deployment_profile: "public_showcase", interactive: false, mutations_allowed: false, real_ai_enabled: false, fictional_data: true });

    render(<AppNavigation />);

    expect(await screen.findByText("Vitrine pública")).toBeInTheDocument();
    expect(screen.getByText("Somente leitura")).toBeInTheDocument();
  });
});
