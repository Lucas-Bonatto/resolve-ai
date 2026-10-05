import { AppShell } from "@/components/app-shell";
import { LockIcon } from "@/components/icons";
import { StatusBadge } from "@/components/ui";

export const metadata = { title: "Security center" };

export default function SecurityPage() {
  return <AppShell title="Security center" description="Deterministic permission boundaries, injection defenses, and blocked actions.">
    <section style={{ marginTop: 24 }}><div className="permission-grid">
      <article className="permission-card"><StatusBadge tone="success">Green · Read</StatusBadge><h3>Automatic, bounded access</h3><p>Validated queries may inspect fictional operational data without a human interruption.</p><ul><li>Search transactions</li><li>Inspect application logs</li><li>Read deployments</li><li>Search knowledge base</li></ul></article>
      <article className="permission-card yellow"><StatusBadge tone="warning">Yellow · Safe write</StatusBadge><h3>Automatic and audited</h3><p>Non-critical internal artifacts can be prepared, but every write leaves an audit record.</p><ul><li>Add incident note</li><li>Draft customer update</li><li>Prepare engineering task</li><li>Generate remediation plan</li></ul></article>
      <article className="permission-card red"><StatusBadge tone="critical">Red · Critical write</StatusBadge><h3>Explicit approval required</h3><p>The workflow pauses. Approval is bound to exact arguments, actor, incident, and expiration.</p><ul><li>Rollback service</li><li>Modify transaction state</li><li>Send communication</li><li>Create or merge code</li></ul></article>
    </div></section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Recent policy decision</h2><StatusBadge tone="neutral">SIMULATED</StatusBadge></header><div className="panel-body"><div className="blocked-card"><div className="blocked-icon"><LockIcon /></div><div><h3>Critical rollback blocked</h3><p><code>request_service_rollback</code> · approval missing · INC-2026-0042</p></div><StatusBadge tone="critical">Blocked</StatusBadge></div></div></article>
      <article className="panel"><header className="panel-header"><h2>Security evaluation</h2><StatusBadge tone="success">5 cases</StatusBadge></header><div className="panel-body summary-list"><div><span>Knowledge prompt injection</span><b>Covered</b></div><div><span>Malicious customer text</span><b>Covered</b></div><div><span>Poisoned incident input</span><b>Covered</b></div><div><span>Tool output injection</span><b>Covered</b></div><div><span>Fake administrator text</span><b>Covered</b></div></div></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}><header className="panel-header"><h2 id="approval-invariants-title">Approval invariants</h2><StatusBadge tone="success">Tested</StatusBadge></header><div className="table-scroll" role="region" aria-labelledby="approval-invariants-title" tabIndex={0}><table className="data-table"><caption className="sr-only">Approval invariants</caption><thead><tr><th>Invariant</th><th>Enforcement</th><th>Failure behavior</th></tr></thead><tbody><tr><td><strong>Exact arguments</strong><small>Canonical SHA-256 binding</small></td><td>Server-side permission engine</td><td>Fail closed</td></tr><tr><td><strong>Incident ownership</strong><small>No cross-incident reuse</small></td><td>Approval gateway</td><td>Reject and audit</td></tr><tr><td><strong>Expiration</strong><small>15-minute default</small></td><td>UTC comparison</td><td>Mark expired</td></tr><tr><td><strong>Single decision</strong><small>No replay</small></td><td>Consumed status</td><td>Conflict response</td></tr></tbody></table></div></article>
  </AppShell>;
}
