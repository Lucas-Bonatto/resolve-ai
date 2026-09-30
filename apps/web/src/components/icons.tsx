import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement>;
const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };

export function MarkIcon(props: Props) { return <svg {...base} {...props}><path d="M12 2 3.8 6.5v6.8c0 4.6 3.5 7.3 8.2 8.7 4.7-1.4 8.2-4.1 8.2-8.7V6.5L12 2Z"/><path d="m8.6 12 2.2 2.2 4.8-5"/></svg>; }
export function PulseIcon(props: Props) { return <svg {...base} {...props}><path d="M3 12h4l2-6 4 12 2-6h6"/></svg>; }
export function IncidentIcon(props: Props) { return <svg {...base} {...props}><path d="M12 9v4m0 4h.01"/><path d="M10.3 3.7 2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/></svg>; }
export function EvalIcon(props: Props) { return <svg {...base} {...props}><path d="M4 19V9m5 10V5m5 14v-7m5 7V3"/></svg>; }
export function LockIcon(props: Props) { return <svg {...base} {...props}><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>; }
export function AuditIcon(props: Props) { return <svg {...base} {...props}><path d="M8 3h8l3 3v15H5V3h3Z"/><path d="M8 11h8M8 15h6M8 7h4"/></svg>; }
export function ArrowIcon(props: Props) { return <svg {...base} {...props}><path d="M5 12h14m-5-5 5 5-5 5"/></svg>; }
export function SparkIcon(props: Props) { return <svg {...base} {...props}><path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z"/><path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15Z"/></svg>; }
export function SearchIcon(props: Props) { return <svg {...base} {...props}><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>; }
export function CheckIcon(props: Props) { return <svg {...base} {...props}><path d="m5 12 4 4L19 6"/></svg>; }
export function ChevronIcon(props: Props) { return <svg {...base} {...props}><path d="m9 18 6-6-6-6"/></svg>; }
