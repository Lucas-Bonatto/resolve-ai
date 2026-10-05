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
    fireEvent.change(screen.getByPlaceholderText(/search incidents/i), {
      target: { value: "authentication" },
    });
    expect(screen.getByText("Authentication failure spike")).toBeInTheDocument();
    expect(screen.queryByText("Approved payments remain pending")).not.toBeInTheDocument();
  });

  it("describes the product as bounded agentic rather than autonomous", () => {
    render(<LandingPage />);

    expect(screen.getByText(/Bounded agentic incident/i)).toBeInTheDocument();
    expect(screen.queryByText(/Autonomous incident/i)).not.toBeInTheDocument();
  });
});
