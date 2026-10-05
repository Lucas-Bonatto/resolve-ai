import Link from "next/link";
import { ArrowIcon, CheckIcon, MarkIcon } from "@/components/icons";
import { SectionTitle, StatusBadge } from "@/components/ui";

const workflow = [
  { number: "01", title: "Collect evidence", body: "Query bounded enterprise tools and turn logs, transactions, deployments, and tests into inspectable evidence.", tag: "READ · AUTOMATIC" },
  { number: "02", title: "Test hypotheses", body: "Keep competing explanations visible, update confidence, and reject conclusions the evidence does not support.", tag: "TYPED · TRACEABLE" },
  { number: "03", title: "Request approval", body: "Bind critical action approval to the incident, tool call, exact arguments, reviewer, and expiration.", tag: "CRITICAL · PAUSED" },
  { number: "04", title: "Prove the outcome", body: "Validate the remediation and resolve only when controlled checks confirm recovery.", tag: "VALIDATED · AUDITED" },
];

export default function LandingPage() {
  return <>
    <a className="skip-link" href="#public-content">Skip to main content</a>
    <main className="public-page" id="public-content" tabIndex={-1}>
    <header className="public-nav">
      <Link href="/" className="brand"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <nav aria-label="Public navigation"><a href="#workflow">How it works</a><a href="#security">Security</a><Link href="/evals">Evaluations</Link><Link href="/audit">Audit trail</Link></nav>
      <Link href="/dashboard" className="button button-secondary">Explore demo <ArrowIcon /></Link>
    </header>

    <section className="hero">
      <div className="hero-copy">
        <div className="hero-kicker"><span /> Bounded agentic incident &amp; operations intelligence</div>
        <h1>Incidents resolved with <em>evidence.</em></h1>
        <p>A bounded, auditable AI workflow that investigates operational problems, uses enterprise tools, proposes actions, validates solutions, and keeps humans in control.</p>
        <div className="hero-actions"><Link href="/incidents/INC-2026-0042" className="button button-primary">Launch interactive demo <ArrowIcon /></Link><a href="#architecture" className="button button-secondary">View architecture</a></div>
        <div className="trust-row"><span><CheckIcon /> Runs without an API key</span><span><CheckIcon /> No real customer data</span><span><CheckIcon /> Critical actions require approval</span></div>
      </div>

      <div className="hero-console" aria-label="Flagship incident scenario preview">
        <div className="console-bar"><div><i /><i /><i /></div><span>Scenario preview · SIMULATED</span></div>
        <div className="console-body">
          <aside className="console-summary"><small>Active incident</small><h3>Approved payments remain pending</h3><StatusBadge tone="critical">SEV-1</StatusBadge><div className="console-stat"><small>Affected</small><b>37 transactions</b></div><div className="console-stat"><small>Service</small><b>webhook-worker</b></div><div className="console-stat"><small>Agent state</small><b>Awaiting approval</b></div></aside>
          <section className="console-timeline"><h4>Live investigation timeline</h4>
            <div className="preview-event"><b>Transaction search complete</b><p>37 approved payments remain pending.</p></div>
            <div className="preview-event"><b>Evidence correlated</b><p>Schema errors began four minutes after dep_184.</p></div>
            <div className="preview-event"><b>Regression reproduced</b><p>Legacy paymentStatus payload fails on the active release.</p></div>
            <div className="preview-event active"><b>Human decision required</b><p>Rollback dep_184 is critical and paused for review.</p></div>
          </section>
        </div>
      </div>
    </section>

    <section className="proof-strip" aria-label="Engineering proof points"><div className="proof-inner">
      <div className="proof-item"><strong>Evidence-first</strong><span>Every diagnosis cites inspectable IDs</span></div>
      <div className="proof-item"><strong>Fail-closed policy</strong><span>Authorization lives outside the model</span></div>
      <div className="proof-item"><strong>40 eval scenarios</strong><span>Including five injection defenses</span></div>
      <div className="proof-item"><strong>Open MCP tools</strong><span>Typed NovaPay operations server</span></div>
    </div></section>

    <section className="landing-section" id="workflow"><SectionTitle eyebrow="A verifiable workflow" title="From signal to resolution, every step leaves evidence." description="ResolveAI is a manager-oriented agent system, not a chat interface. Workflow state, tool calls, policy decisions, and human approvals are explicit product objects." />
      <div className="workflow-grid">{workflow.map(item => <article className="workflow-card" key={item.number}><span>{item.number}</span><h3>{item.title}</h3><p>{item.body}</p><b>{item.tag}</b></article>)}</div>
    </section>

    <section className="approval-section" id="security"><div className="approval-inner">
      <SectionTitle eyebrow="Humans remain in control" title="Reasoning can suggest. Only policy can authorize." description="The approval gateway re-validates risk, scope, expiration, incident ownership, tool-call identity, and an exact arguments hash before a critical side effect can run." />
      <article className="approval-card-demo"><header><StatusBadge tone="warning">Approval required</StatusBadge><StatusBadge tone="critical">Critical write</StatusBadge></header><h3>Rollback webhook-worker to dep_183</h3><p>Failures began after dep_184 and a controlled regression test reproduced the parser defect.</p><div className="approval-evidence"><span>DEPLOY-184</span><span>LOG-291</span><span>TEST-012</span></div><div className="approval-actions-demo" aria-label="Decision preview"><span className="button button-secondary">Reject</span><span className="button button-success">Approve exact action</span></div></article>
    </div></section>

    <section className="landing-section" id="architecture"><SectionTitle eyebrow="Architecture" title="Agentic where useful. Deterministic where necessary." description="FastAPI owns the workflow, permissions, evidence, and audit trail. The OpenAI Agents SDK produces typed analysis. A deterministic provider powers the same contracts for zero-cost local demos." />
      <div className="workflow-grid">
        <article className="workflow-card"><span>APP</span><h3>Next.js command center</h3><p>Server-first product surfaces with focused client interactions for live events and decisions.</p><b>APP ROUTER · TYPESCRIPT</b></article>
        <article className="workflow-card"><span>CORE</span><h3>FastAPI coordinator</h3><p>Explicit state transitions, validated evidence, bounded tools, and SSE activity streams.</p><b>PYDANTIC · DOMAIN LAYER</b></article>
        <article className="workflow-card"><span>AI</span><h3>Provider boundary</h3><p>Deterministic demo and OpenAI providers return the same structured diagnosis contract.</p><b>AGENTS SDK · EVALS</b></article>
        <article className="workflow-card"><span>TOOLS</span><h3>NovaPay MCP</h3><p>A standalone MCP v2 server exposes fictional operational data with typed schemas and audits.</p><b>MCP · POLICY GATEWAY</b></article>
      </div>
    </section>

    <section className="landing-section open-source"><SectionTitle eyebrow="Open-source engineering case study" title="Inspect the claims. Reproduce the results." description="The demo is fictional. The architecture, security invariants, evaluation runner, and tests are real and inspectable." /><div className="hero-actions"><Link href="/dashboard" className="button button-primary">Open command center <ArrowIcon /></Link><Link href="/evals" className="button button-secondary">View evaluation center</Link></div></section>
    <footer className="public-footer"><Link href="/" className="brand"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link><span>Fictional NovaPay simulation · Agents can reason. Systems must verify.</span></footer>
    </main>
  </>;
}
