import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InvestigationTimeline } from "@/features/war-room/investigation-timeline";
import type { IncidentEvent } from "@/types/domain";

function event(overrides: Partial<IncidentEvent> & Pick<IncidentEvent, "id" | "type" | "title">): IncidentEvent {
  return {
    incident_id: "INC-TEST",
    summary: `${overrides.title} summary`,
    status: "SIMULATED",
    created_at: "2026-10-02T12:00:00Z",
    metadata: {},
    correlation_id: "corr_test",
    agent_run_id: "run_test",
    tool_call_id: null,
    approval_id: null,
    ...overrides,
  };
}

const events: IncidentEvent[] = [
  event({ id: "evt-1", type: "incident.state_changed", title: "Investigation started", metadata: { state: "INVESTIGATING" } }),
  event({ id: "evt-2", type: "tool.started", title: "Running query_application_logs", metadata: { tool: "query_application_logs" } }),
  event({ id: "evt-3", type: "tool.completed", title: "query_application_logs completed", tool_call_id: "tool-1", metadata: { tool_call_id: "tool-1", duration_ms: 4 } }),
  event({ id: "evt-4", type: "approval.requested", title: "Approval requested", approval_id: "approval-1" }),
];

describe("InvestigationTimeline", () => {
  it("defaults to milestones and groups tool events into one expandable activity", () => {
    render(<InvestigationTimeline events={events} />);

    expect(screen.getByText("Investigation started")).toBeInTheDocument();
    expect(screen.getByText("Approval requested")).toBeInTheDocument();
    expect(screen.queryByText("query_application_logs")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Tools 1" }));
    const tool = screen.getByText("query_application_logs").closest("details");
    expect(tool).not.toBeNull();
    expect(tool).not.toHaveAttribute("open");

    fireEvent.click(screen.getByText("query_application_logs"));
    expect(tool).toHaveAttribute("open");
    expect(screen.getByText("tool.started")).toBeInTheDocument();
    expect(screen.getByText("tool.completed")).toBeInTheDocument();
  });

  it("offers a policy-only view without losing the complete event view", () => {
    render(<InvestigationTimeline events={events} />);

    fireEvent.click(screen.getByRole("button", { name: "Policy 1" }));
    expect(screen.getByText("Approval requested")).toBeInTheDocument();
    expect(screen.queryByText("Investigation started")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All events 4" }));
    expect(screen.getByText("Investigation started")).toBeInTheDocument();
    expect(screen.getByText("query_application_logs")).toBeInTheDocument();
  });
});
