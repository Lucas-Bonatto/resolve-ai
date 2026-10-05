"use client";

import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/ui";
import type { IncidentEvent } from "@/types/domain";

type TimelineFilter = "milestones" | "tools" | "policy" | "all";

type TimelineEntry =
  | { kind: "event"; id: string; event: IncidentEvent }
  | { kind: "tool"; id: string; tool: string; events: IncidentEvent[] };

const policyStates = new Set(["AWAITING_APPROVAL", "EXECUTING"]);

function eventTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function toolName(event: IncidentEvent): string {
  const metadataName = event.metadata.tool;
  if (typeof metadataName === "string") return metadataName;
  if (event.title.startsWith("Running ")) return event.title.slice("Running ".length);
  if (event.title.endsWith(" completed")) return event.title.slice(0, -" completed".length);
  return event.title;
}

function isPolicyEvent(event: IncidentEvent): boolean {
  const state = event.metadata.state;
  return event.type.startsWith("approval.") || (
    event.type === "incident.state_changed"
    && typeof state === "string"
    && policyStates.has(state)
  );
}

export function groupTimelineEntries(events: IncidentEvent[]): TimelineEntry[] {
  const chronological: TimelineEntry[] = [];

  for (const event of events) {
    if (!event.type.startsWith("tool.")) {
      chronological.push({ kind: "event", id: event.id, event });
      continue;
    }

    const name = toolName(event);
    if (event.type === "tool.completed") {
      const pending = [...chronological].reverse().find(entry => (
        entry.kind === "tool"
        && entry.tool === name
        && !entry.events.some(item => item.type === "tool.completed")
      ));
      if (pending?.kind === "tool") {
        pending.events.push(event);
        pending.id = event.tool_call_id ?? pending.id;
        continue;
      }
    }

    chronological.push({
      kind: "tool",
      id: event.tool_call_id ?? event.id,
      tool: name,
      events: [event],
    });
  }

  return chronological.reverse();
}

function MilestoneEvent({ event }: { event: IncidentEvent }) {
  const eventClass = event.type.startsWith("approval.") ? " approval" : "";
  return (
    <article className={`timeline-event${eventClass}`}>
      <span className="timeline-time">{eventTime(event.created_at)}</span>
      <h4>{event.title}</h4>
      <p>{event.summary}</p>
      <div className="event-meta">
        <span>{event.type}</span>
        <span>{event.status}</span>
      </div>
    </article>
  );
}

function TechnicalActivity({ entry }: { entry: Extract<TimelineEntry, { kind: "tool" }> }) {
  const latest = entry.events.at(-1) ?? entry.events[0];
  const duration = latest.metadata.duration_ms;
  const completed = entry.events.some(event => event.type === "tool.completed");

  return (
    <details className="timeline-activity">
      <summary>
        <span className="timeline-activity-copy">
          <span className="timeline-time">{eventTime(latest.created_at)}</span>
          <b>{entry.tool}</b>
          <small>{entry.events.length} technical {entry.events.length === 1 ? "event" : "events"}</small>
        </span>
        <span className="timeline-activity-status">
          {typeof duration === "number" && <span>{duration} ms</span>}
          <StatusBadge tone={completed ? "info" : "warning"}>{completed ? "Completed" : "In progress"}</StatusBadge>
        </span>
      </summary>
      <div className="timeline-activity-detail">
        {entry.events.map(event => (
          <article key={event.id}>
            <div>
              <b>{event.title}</b>
              <span>{eventTime(event.created_at)}</span>
            </div>
            <p>{event.summary}</p>
            <div className="event-meta">
              <span>{event.type}</span>
              <span>{event.status}</span>
              <span>{event.id}</span>
            </div>
          </article>
        ))}
      </div>
    </details>
  );
}

export function InvestigationTimeline({ events }: { events: IncidentEvent[] }) {
  const [filter, setFilter] = useState<TimelineFilter>("milestones");
  const entries = useMemo(() => groupTimelineEntries(events), [events]);
  const milestoneCount = entries.filter(entry => entry.kind === "event").length;
  const toolCount = entries.filter(entry => entry.kind === "tool").length;
  const policyCount = entries.filter(entry => (
    entry.kind === "event" && isPolicyEvent(entry.event)
  )).length;
  const filtered = entries.filter(entry => {
    if (filter === "all") return true;
    if (filter === "tools") return entry.kind === "tool";
    if (filter === "policy") return entry.kind === "event" && isPolicyEvent(entry.event);
    return entry.kind === "event";
  });
  const filters: Array<{ id: TimelineFilter; label: string; count: number }> = [
    { id: "milestones", label: "Milestones", count: milestoneCount },
    { id: "tools", label: "Tools", count: toolCount },
    { id: "policy", label: "Policy", count: policyCount },
    { id: "all", label: "All events", count: events.length },
  ];

  return (
    <section className="war-card">
      <header className="war-card-head">
        <h3>Investigation timeline</h3>
        <span className="status-badge status-info"><i className="live-dot" /> Event stream</span>
      </header>
      <div className="timeline-controls">
        <p>{milestoneCount} milestones · {toolCount} technical activities</p>
        <div className="timeline-filters" role="group" aria-label="Timeline filters">
          {filters.map(item => (
            <button
              type="button"
              key={item.id}
              aria-pressed={filter === item.id}
              onClick={() => setFilter(item.id)}
            >
              {item.label} <span>{item.count}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="timeline">
        {filtered.length > 0 ? filtered.map(entry => (
          entry.kind === "event"
            ? <MilestoneEvent event={entry.event} key={entry.id} />
            : <TechnicalActivity entry={entry} key={entry.id} />
        )) : (
          <div className="timeline-empty">No events match this view yet.</div>
        )}
      </div>
    </section>
  );
}
