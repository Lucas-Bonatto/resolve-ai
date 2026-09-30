import type { ReactNode } from "react";

export function StatusBadge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "critical" | "warning" | "success" | "info" }) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow">{children}</div>;
}

export function SectionTitle({ eyebrow, title, description }: { eyebrow: string; title: string; description?: string }) {
  return <div className="section-title"><Eyebrow>{eyebrow}</Eyebrow><h2>{title}</h2>{description && <p>{description}</p>}</div>;
}

export function MetricCard({ label, value, detail, tone = "default" }: { label: string; value: string; detail: string; tone?: "default" | "good" | "warn" }) {
  return <article className={`metric-card metric-${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>;
}
