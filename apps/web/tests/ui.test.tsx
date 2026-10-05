import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "../src/app/page";
import { StatusBadge } from "../src/components/ui";
import { IncidentTable } from "../src/features/incidents/incident-table";

describe("product UI", () => {
  it("renders semantic status text", () => {
    render(<StatusBadge tone="critical">SEV-1</StatusBadge>);
    expect(screen.getByText("SEV-1")).toHaveClass("status-critical");
  });

  it("filters the fictional incident list", () => {
    render(<IncidentTable />);
    expect(screen.getByRole("region", { name: "Tabela de resultados de incidentes" })).toBeInTheDocument();
    expect(screen.getByText("Resultados de incidentes", { selector: "caption" })).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(/pesquisar incidentes/i), {
      target: { value: "autenticação" },
    });
    expect(screen.getByText("Pico de falhas de autenticação")).toBeInTheDocument();
    expect(screen.queryByText("Pagamentos aprovados continuam pendentes")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("1 incidente corresponde aos filtros atuais.");
  });

  it("describes the product as bounded agentic rather than autonomous", () => {
    render(<LandingPage />);

    expect(screen.getByText(/Inteligência agentiva limitada/i)).toBeInTheDocument();
    expect(screen.queryByText(/incidente autônomo/i)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Pular para o conteúdo principal" })).toHaveAttribute("href", "#public-content");
    expect(screen.queryByRole("button", { name: "Rejeitar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Aprovar ação exata" })).not.toBeInTheDocument();
  });
});
