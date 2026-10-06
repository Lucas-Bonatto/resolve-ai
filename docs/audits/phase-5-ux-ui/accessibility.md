# Accessibility audit and remediation

Audit date: 2026-10-05

Scope: public landing page, application shell, incident list, flagship War Room, Evaluation Center, Security Center, and Audit Log.

Target: a focused WCAG 2.2 AA-informed engineering pass. This is not a conformance certification. The audit combined DOM inspection, keyboard interaction, rendered color measurement, desktop and 320 px screenshots, component tests, and Playwright checks. It did not include a session with NVDA, JAWS, VoiceOver, or another real assistive technology.

## Evidence walkthrough

1. **Landing page, 1440 px — healthy structure; contrast issues found.** The page had one main heading, a named public navigation, and a clear reading order. Workflow numbers and architecture codes used `#9aa49e` on white (2.57:1), and the approval preview exposed two non-functional buttons to keyboard users. [Screenshot 01](./accessibility-screenshots/01-landing-desktop.jpg)
2. **War Room approval state, 1440 px — healthy workflow semantics; disclosure focus needed correction.** The pending decision was early in source order and the timeline filters exposed pressed state. Opening evidence did not move focus to the new content or expose expanded state, and closing it did not restore focus. [Screenshot 02](./accessibility-screenshots/02-war-room-approval-desktop.jpg)
3. **War Room, 320 px — healthy reflow.** The critical decision, evidence, and timeline fit the viewport without page-level horizontal scrolling. [Screenshot 03](./accessibility-screenshots/03-war-room-320px-reflow.jpg)
4. **Evaluation Center, 1440 px — honest result; async announcement and narrow reflow gaps found.** Provenance and the visible failing case remained truthful, but run completion was not announced through a live region. At 320 px, chart labels widened the document beyond the viewport. [Screenshot 04](./accessibility-screenshots/04-evaluation-desktop.jpg)
5. **Keyboard and focus — remediated and covered.** Both shells now provide skip navigation. Focus uses a solid high-contrast outline with a white separation halo. Evidence disclosure moves focus to its heading and returns focus to the originating button when closed. The mobile navigation and critical approval remain keyboard operable.
6. **Names, roles, and status messages — remediated and covered.** Scrollable tables have captions, named focusable regions, and bounded horizontal scrolling. Incident filtering, evaluation progress/completion, and incident state changes expose polite status messages. API failures use alerts. Decorative approval controls on the landing preview are no longer interactive.
7. **Contrast and non-color state — focused issues remediated.** Muted metadata now uses the established `--muted` token, warning text uses `#8a500c` on `#fff1d7` (5.82:1), the dark-shell wordmark uses the lighter lime token, and state remains explicit in text. This was a targeted rendered-color review, not an exhaustive contrast scan of every possible dynamic payload.
8. **320 px reflow and forced colors — automated post-change checks healthy.** Evaluation and Security surfaces no longer create page-level horizontal overflow at 320 px; wide tables remain operable inside named scroll regions. Playwright emulates forced colors and reduced motion, then verifies a visible focus outline and explicit critical-risk text.

## Implemented remediation

- Added a landing-page skip link and removed false interactive controls from its static approval preview.
- Strengthened focus visibility and added forced-colors styles for controls, state borders, selected navigation, charts, confidence bars, health indicators, and timeline markers.
- Corrected the measured low-contrast metadata, warning, wordmark, evidence, and timeline treatments without changing the visual hierarchy.
- Added table captions and named, keyboard-focusable scroll regions to incidents, audit records, approval invariants, and failing evaluation cases.
- Added polite live status for incident state, incident-filter result counts, and evaluation execution.
- Added explicit evidence disclosure state plus deterministic focus entry and restoration.
- Fixed 320 px Evaluation and Security overflow while preserving table content rather than clipping it.
- Added unit and browser regression coverage for these behaviors.

## WCAG considerations

| Consideration | Evidence in this pass | Status |
| --- | --- | --- |
| 1.3.1 Info and Relationships | Headings, captions, table regions, labels, and state text | Improved and automated |
| 1.4.3 Contrast (Minimum) | Targeted rendered-color measurements and token corrections | Focused pass complete; not exhaustive certification |
| 1.4.10 Reflow | Core routes checked at 320 CSS px; wide data remains locally scrollable | Automated regression |
| 1.4.11 Non-text Contrast | Stronger focus treatment and forced-colors boundary overrides | Automated regression plus code review |
| 2.4.1 Bypass Blocks | Skip links in public and application shells | Automated component coverage |
| 2.4.7 Focus Visible | Solid outline/halo and forced-colors focus | Automated browser coverage |
| 2.5.8 Target Size (Minimum) | Public navigation, panel actions, evidence close, mobile and critical controls enlarged | Focused review complete |
| 4.1.2 Name, Role, Value | Named navigation/table regions and evidence expanded state | Automated component/browser coverage |
| 4.1.3 Status Messages | Incident, filter, evaluation, and error announcements | Automated component/browser coverage |

## Verification limits

- The integrated audit browser captured and inspected the four screenshots above before remediation. Its permission review became unavailable during post-change recapture, so no post-change screenshot is presented as evidence.
- Post-change behavior was instead verified by the repository's component, build, and Playwright suites. That is useful engineering evidence, but it does not substitute for a real screen-reader session.
- Browser zoom at 200%, speech output quality, verbosity across screen readers, OS-native high-contrast rendering, touch exploration, and localization remain manual release checks.
