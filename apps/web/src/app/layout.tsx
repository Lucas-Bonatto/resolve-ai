import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "ResolveAI — Inteligência agentiva limitada para incidentes", template: "%s · ResolveAI" },
  description: "Um sistema auditável de resposta a incidentes com IA limitada, evidências, ferramentas, avaliações, políticas determinísticas e aprovações humanas.",
  metadataBase: new URL("https://resolveai.example"),
  openGraph: { title: "ResolveAI", description: "Agentes podem raciocinar. Sistemas devem verificar.", type: "website" },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
