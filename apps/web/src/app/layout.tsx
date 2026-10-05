import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "ResolveAI — Bounded Agentic Incident Intelligence", template: "%s · ResolveAI" },
  description: "A bounded, auditable AI incident-response system with evidence, tools, evaluations, deterministic policy, and human approvals.",
  metadataBase: new URL("https://resolveai.example"),
  openGraph: { title: "ResolveAI", description: "Agents can reason. Systems must verify.", type: "website" },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
