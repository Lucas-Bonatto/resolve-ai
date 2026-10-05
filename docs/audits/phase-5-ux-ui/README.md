# Phase 5 UX/UI audit

Audit date: 2026-10-02

Branch: `phase-5-ux-ui-audit`

Baseline: `8027bdc46a8ba2457377d0d9a75075c8c2ef8d76`

## Objective and method

This audit evaluates whether ResolveAI presents its evidence-first incident workflow with the clarity, trust, and operational hierarchy expected of a serious engineering product. It covers the public landing page, Command Center, flagship War Room, critical approval, resolved state, and Evaluation Center.

The review used the running deterministic demo rather than static mockups. The flagship incident was injected, investigated, approved, validated, and resolved through the UI. The benchmark was also executed through the UI. Screens were reviewed at 1440 × 1000 and 390 × 844, with a focused keyboard check on the critical decision controls.

This is a product and accessibility risk audit, not a claim of WCAG conformance. Screen-reader behavior, measured color contrast, browser zoom, forced colors, localization, and a full keyboard-only traversal still require dedicated verification.

## Executive assessment

ResolveAI already has a distinctive, credible desktop visual system and unusually strong execution-honesty patterns. Evidence IDs, simulated/executed labels, competing hypotheses, approval scope, and visible evaluation failures make the product feel inspectable rather than theatrical.

The current release should not be treated as presentation-ready, however. Two trust-critical problems lead the backlog:

1. The Command Center presents static fixture data as current operational posture even after the flagship incident is resolved and an evaluation has executed.
2. The authenticated product shell overflows horizontally at a standard 390 px viewport, truncating navigation and incident metadata.

The flagship workflow also makes the operator work too hard at the two moments that matter most: the critical decision appears after a long evidence and hypothesis trail, while the final recovery proof appears below an exhaustive event stream.

## Evidence walkthrough

1. **Landing page — desktop. Healthy with a copy caveat.** The hierarchy, primary action, engineering proof points, and approval preview communicate the product clearly. The phrase “Autonomous incident & operations intelligence” overstates the bounded manager-style architecture. [Screenshot 01](./screenshots/01-landing-desktop.png)
2. **War Room before injection — desktop. Healthy.** The empty state is calm and has one obvious action, although it uses more vertical space than necessary. [Screenshot 02](./screenshots/02-war-room-empty-desktop.png)
3. **War Room awaiting approval — desktop. Mixed.** Evidence and hypotheses are legible, but the critical decision is below four hypothesis cards and the event stream dominates the page length. [Screenshot 03](./screenshots/03-war-room-awaiting-approval-desktop.png)
4. **War Room resolved — desktop. Mixed.** The state and validation are honest, but post-remediation validation and the incident report are far below the timeline instead of being summarized near the top. [Screenshot 04](./screenshots/04-war-room-resolved-desktop.png)
5. **Evaluation Center before execution — desktop. Mixed.** “Sample data” and “Not executed” are honest. Six large metric cards containing only dashes make the empty state feel unfinished rather than instructional. [Screenshot 05](./screenshots/05-evaluation-empty-desktop.png)
6. **Evaluation Center after execution — desktop. Mixed.** The known failure remains visible, but 97.5% appears in success green, the header says “1 failures,” and the run contract lacks a useful code revision. [Screenshot 06](./screenshots/06-evaluation-result-desktop.png)
7. **Command Center after the incident and evaluation ran — desktop. Needs correction.** The page still says “1 awaiting demo launch,” “Awaiting demo,” and “Execute before claiming results.” This contradicts the backend state observed in the same session. [Screenshot 07](./screenshots/07-dashboard-desktop.png)
8. **Landing page — mobile. Mixed.** The hero and primary actions remain readable, but the brand and top action collide and truncate in the header. [Screenshot 08](./screenshots/08-landing-mobile.png)
9. **Evaluation result — mobile. Needs correction.** The product shell becomes a horizontally scrollable row and cuts off navigation at 390 px. The metric grid itself remains readable. [Screenshot 09](./screenshots/09-evaluation-result-mobile.png)
10. **War Room awaiting approval — mobile, initial viewport. Needs correction.** Horizontal overflow truncates navigation, incident metadata, and the SIMULATED badge. The long single-column order places the decision several screens below the current state. [Screenshot 10](./screenshots/10-war-room-awaiting-approval-mobile.png)
11. **Critical decision — mobile keyboard focus. Mixed but operable.** The complete decision card fits once reached, both actions have large targets, and the Reject button has a visible focus ring. The card remains approximately 6,000 CSS pixels below the top and the page still has horizontal overflow. [Screenshot 11](./screenshots/11-war-room-decision-keyboard-mobile.png)

## Prioritized findings

### P0 — Product truth: Command Center state contradicts the live workflow

The Command Center calls itself “Operational posture” but renders hard-coded fixture metrics, queue entries, activity, service health, and evaluation posture. During this audit the actual incident was `RESOLVED` and a 40-case evaluation had executed, while the dashboard still reported “Awaiting demo” and “Execute before claiming results.”

This is more than stale copy: it undermines the product's central promise that claims follow system evidence.

**Recommendation:** either bind the flagship and evaluation summary to backend state, or separate the page into unmistakably labeled `LIVE DEMO STATE` and `SAMPLE FIXTURE HISTORY` regions. Never combine them under one unlabeled operational posture.

### P1 — Responsive shell: standard mobile width is horizontally broken

At 390 px, the desktop sidebar is converted into a single non-wrapping row with `overflow-x: auto`. The brand and all five navigation links exceed the viewport, producing persistent horizontal page scrolling and clipped content. The War Room header compounds this by keeping its metadata badges on one line.

**Recommendation:** replace the scrolling row with a compact mobile header and an accessible menu/drawer, preserve a direct route back to the Command Center, apply `aria-current` to the active destination, and ensure page-level overflow stays at zero. Let War Room metadata wrap below the title.

### P1 — Decision hierarchy: the critical approval is too far from the current state

The approval card appears after four detailed hypothesis cards in the third column on desktop and near the end of a roughly 6,000 px mobile document. The operator sees `AWAITING APPROVAL` long before seeing what is awaiting them.

**Recommendation:** when an approval is pending, promote a compact decision summary directly below the incident header. Keep the full bound action and evidence card sticky on desktop or early in the mobile source order. Use explicit labels such as “Reject rollback” and “Approve exact rollback.”

### P1 — Investigation hierarchy: low-level events obscure milestones

Every tool start and completion is rendered as a full timeline event. This is valuable audit detail, but it overwhelms the user-facing progression and pushes diagnosis, remediation, validation, and reporting out of view.

**Recommendation:** default to milestone events, group tool start/completion pairs into expandable technical activity, and provide a filter for `Milestones`, `Tools`, `Policy`, and `All events`. Preserve every event in the audit record.

### P1 — Outcome hierarchy: recovery proof arrives too late

The resolved state is honest, but validation evidence and the incident report sit below the full event stream. An operator opening a resolved incident should not have to traverse the investigation history to learn whether recovery was proven.

**Recommendation:** render a resolved summary immediately under the incident header: remediation execution status, validation outcome, affected-event recovery, and links to the relevant evidence. Keep the full timeline below it.

### P1 — Product claim: “Autonomous” conflicts with the implemented architecture

The landing kicker and page metadata describe ResolveAI as autonomous, while the product and constitution intentionally emphasize bounded agentic phases, deterministic policy, and human approval.

**Recommendation:** use “Bounded agentic incident & operations intelligence” or similarly precise language in both visible copy and metadata.

### P2 — Evaluation communication needs more decision context

The executed result shows 97.5% in success green despite a visible regression. It exposes zero bypasses and unauthorized writes but does not show the number of active policy-boundary probes. `Code revision unknown` prevents reproducibility, and “1 failures” is grammatically incorrect.

**Recommendation:** lead with `39 / 40 passed`, use neutral or warning treatment while failures exist, show probe count alongside zero violations, display timestamp/duration/revision, and provide a previous-run comparison. Use singular/plural-aware copy.

### P2 — Accessibility semantics and readability need a dedicated pass

Positive evidence includes semantic headings, text labels in addition to color, 44 px critical action controls, reduced-motion support, and a visible focus indicator on the tested Reject action.

Risks found in implementation and DOM inspection:

- the War Room nests a second `<main>` inside the AppShell `<main>`;
- there is no skip link for repeated navigation;
- primary navigation has no active `aria-current` state;
- mobile navigation depends on horizontal scrolling without an explicit affordance;
- several metadata labels use 8–10 px text and should be reviewed at zoom;
- muted foreground/background combinations still need measured contrast verification;
- a full keyboard order and screen-reader announcement audit has not yet been run.

**Recommendation:** keep a single main landmark, add a skip link and active-route semantics, retain the existing focus treatment, increase the smallest operational text, and validate contrast and zoom before release.

## Implementation signals

| Area | Current implementation signal | Likely owning file |
| --- | --- | --- |
| Dashboard truth | Static metrics and `incidentFixtures` render as operational posture | `apps/web/src/app/dashboard/page.tsx` |
| Mobile shell | Sidebar becomes one non-wrapping horizontal row | `apps/web/src/app/globals.css` |
| Navigation semantics | Links do not expose active state | `apps/web/src/components/app-shell.tsx` |
| Nested landmarks | War Room middle column is another `<main>` | `apps/web/src/features/war-room/war-room.tsx` |
| Timeline density | Every event is mapped directly into the primary timeline | `apps/web/src/features/war-room/war-room.tsx` |
| Evaluation tone | Success tone is applied to result cards regardless of failures | `apps/web/src/features/evaluations/evaluation-center.tsx` |
| Autonomy claim | Visible kicker and document metadata use “Autonomous” | `apps/web/src/app/page.tsx`, `apps/web/src/app/layout.tsx` |

## Recommended implementation sequence

1. Fix Command Center truth labeling/data binding and the 390 px shell overflow.
2. Promote pending approvals and resolved validation summaries near the incident header.
3. Introduce milestone-first timeline grouping without removing audit detail.
4. Improve evaluation status language, provenance, and comparison context.
5. Correct semantic landmarks, skip navigation, active-route state, smallest text, and measured contrast.
6. Re-run the flagship Playwright flow at desktop and narrow widths, then complete keyboard and screen-reader checks.

## What should remain unchanged

- Backend-owned authorization and exact-action approval binding.
- Evidence IDs beside hypotheses, diagnosis, and decisions.
- Clear `SIMULATED`, `EXECUTED`, `NOT_EXECUTED`, and failure states.
- Visible known evaluation regressions.
- Validation before `RESOLVED`.
- The restrained operational visual language and absence of chat-style interaction.

## Remediation pass 1 — 2026-10-02

The first implementation pass closed the two leading findings:

- The Command Center now reads incidents and the latest evaluation from the local API. Live metrics, the incident queue, evaluation pass count, visible failures, and active boundary-probe count follow backend state.
- Static activity and service-health examples remain available only as explicitly labeled `SAMPLE FIXTURE HISTORY` and `SAMPLE FIXTURE` sections.
- The misleading “Inject incident” link is now “Open flagship”; injection still happens only through the War Room action.
- The mobile shell now uses a bounded disclosure menu instead of a non-wrapping horizontal navigation row.
- Active navigation exposes `aria-current="page"`, a skip link targets the single main landmark, and the nested War Room `<main>` was removed.
- The landing header now layers above the decorative hero graphic, preventing the brand and demo action from being visually clipped.
- Playwright verifies the live resolved dashboard state, evaluation `39/40` result, `30` boundary probes, keyboard-operable approval, mobile menu visibility, and absence of horizontal overflow at 390 px.

Evidence after remediation:

1. **Command Center — desktop.** Live incident and evaluation data are separated from labeled fixtures. [Screenshot 12](./screenshots/12-dashboard-corrected-desktop.png)
2. **Command Center — mobile.** The page fits the viewport without horizontal scrolling. [Screenshot 13](./screenshots/13-dashboard-corrected-mobile.png)
3. **Mobile navigation expanded.** All destinations are visible and the current route has active semantics. [Screenshot 14](./screenshots/14-navigation-mobile-open.png)
4. **Landing — mobile.** Brand and “Explore demo” action are no longer obscured by the hero decoration. [Screenshot 15](./screenshots/15-landing-corrected-mobile.png)

The remaining P1 work is approval/outcome prominence, milestone-first timeline grouping, and precise bounded-agentic product copy.

## Remediation pass 2 — 2026-10-02

The second implementation pass corrected the two trust-critical hierarchy problems in the flagship War Room:

- A pending critical decision now appears directly below the incident header, before evidence, hypotheses, and the investigation timeline.
- The decision presents the exact requested action, reason, potential impact, and bound evidence once, with explicit `Reject rollback` and `Approve exact rollback` controls.
- A completed validation now promotes recovery proof and the incident report to the same top-level position. Failed validation receives a distinct critical treatment and is never presented as resolution success.
- The former lower-page approval, validation, and report duplicates were removed. Historical approval state remains visible in the policy column after a decision.
- Playwright now asserts that the pending decision and completed outcome precede the timeline, that the decision heading is visible in the initial 390 px viewport, and that the exact-action controls remain keyboard operable.

Visual evidence after remediation:

1. **Decision hierarchy — desktop.** The pending critical action is visible immediately below current incident state. [Screenshot 16](./screenshots/16-war-room-decision-promoted-desktop.jpg)
2. **Decision hierarchy — mobile.** The decision starts in the initial 390 × 844 viewport without horizontal overflow. [Screenshot 17](./screenshots/17-war-room-decision-promoted-mobile.jpg)
3. **Outcome hierarchy — desktop.** Validation proof and the incident report precede the investigation timeline. [Screenshot 18](./screenshots/18-war-room-outcome-promoted-desktop.jpg)
4. **Outcome hierarchy — mobile.** Recovery status remains concise and readable before the long-form investigation record. [Screenshot 19](./screenshots/19-war-room-outcome-promoted-mobile.jpg)

At that checkpoint, the remaining P1 work was milestone-first timeline grouping and precise bounded-agentic product copy; evaluation provenance and comparison context remained P2 work.

## Remediation pass 3 — 2026-10-05

The third implementation pass closes the remaining timeline, product-language, and evaluation-communication findings:

- The War Room defaults to milestone events and reports the number of milestones and technical activities without deleting any event.
- `Milestones`, `Tools`, `Policy`, and `All events` filters are keyboard-operable toggle buttons. Tool start/completion pairs are grouped into expandable technical activities that retain event type, execution label, event ID, duration, and summary.
- The landing page and document metadata now describe ResolveAI as bounded agentic. Product copy no longer implies an autonomous operator.
- The Evaluation Center leads with the executed `passed / total` contract, treats a non-perfect run as warning rather than success, uses singular failure copy, and exposes UTC execution time, suite, run kind, result ID, provider/model, code revision, average case duration, and active boundary probes.
- Previous-run comparison appears only when a prior executed result exists in the current process. Demo reset clears that history and the empty state says so explicitly.
- The documented `RESOLVEAI_CODE_REVISION` setting now reaches the runner. CI supplies `github.sha`; Compose forwards an explicitly configured revision; missing provenance is shown as `Not configured`.

Visual evidence after remediation:

1. **Milestone-first timeline — desktop.** The primary record emphasizes workflow milestones. [Screenshot 20](./screenshots/20-war-room-milestones-desktop.jpg)
2. **Expandable technical activity — desktop.** Tool-level events remain inspectable without dominating the workflow. [Screenshot 21](./screenshots/21-war-room-technical-activity-desktop.jpg)
3. **Timeline filters — mobile.** All four views remain usable at 390 × 844 without page overflow. [Screenshot 22](./screenshots/22-war-room-timeline-mobile.jpg)
4. **Evaluation provenance — desktop.** The executed result leads with `39 / 40`, visible warning state, provenance, and honest previous-run context. [Screenshot 23](./screenshots/23-evaluation-provenance-desktop.jpg)
5. **Evaluation provenance — mobile.** Run identity and security context remain readable in a single column. [Screenshot 24](./screenshots/24-evaluation-provenance-mobile.jpg)
6. **Bounded-agentic language — desktop.** The landing claim now matches the manager-style architecture. [Screenshot 25](./screenshots/25-landing-bounded-agentic-desktop.jpg)

The remaining audit work is a dedicated screen-reader, zoom, forced-colors, and measured-contrast pass. Public demo media and deployment remain product-launch tasks rather than audit remediation.
