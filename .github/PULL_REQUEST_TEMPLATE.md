## What changed

Describe the user-visible outcome and the smallest useful implementation summary.

## Why

Describe the problem and evidence motivating this change.

## Trust boundary

- [ ] No permission or approval invariant changed.
- [ ] Any changed invariant is documented and tested.
- [ ] Simulated and executed behavior remain clearly labeled.
- [ ] Untrusted content cannot influence authorization.
- [ ] No secret, private reasoning, or unrestricted resource access was introduced.

## Verification

- [ ] Python tests, lint, and type checking
- [ ] Web tests, lint, type checking, and production build
- [ ] Browser flow when UI or workflow behavior changed
- [ ] Relevant evaluations compared with the previous generated result
- [ ] Screenshots or recordings for visual changes
- [ ] Demo Mode and flagship scenario remain functional

## Compatibility and data

- [ ] Public API/type changes are reflected in backend, frontend, tests, and docs
- [ ] Database changes include a reviewed migration and fresh/upgrade verification
- [ ] Backward compatibility was preserved or the break is explicitly documented
- [ ] Dependency and lockfile changes are intentional

## Documentation

List updated docs, ADRs, evaluation cases, and known limitations.

## Not executed

List any check that could not run and the exact reason. Do not imply CI or deployment success that was not observed.
