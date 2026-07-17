# React Stack — Verification Guidance

How the generic gates apply to React units. The project's adapter config (`unit-loop.adapter.yaml`; see the unit-loop skill's `references/project-adapter.md`) maps each slot to a concrete command.

## Iteration ladder

1. Read the code / reason statically.
2. Typecheck (fast, catches most contract drift before any test runs).
3. Live-session iteration: start the dev server once, then edit → hot module reload → inspect per attempt — the workhorse for "does this render/behave right".
4. Scoped component/unit test (single file or test name filter).
5. Scoped browser/e2e test — expensive; confirm, don't discover.
6. Full suite — once per unit as the final regression gate.

## Gate notes

- **test-scoped / test-full:** scope to this unit's test files during the loop (the runner's file or name filter); the full suite runs once after review. Test behavior through the rendered output and user-facing queries (roles, labels, text), not implementation internals.
- **typecheck:** treat as a deterministic gate in its own right — a green test run with a red typecheck is not GREEN.
- **lint:** the project's lint config is the contract; do not disable rules inline to pass a gate.
- **snapshot:** large tree snapshots churn and stop guarding anything; prefer small, intention-revealing snapshots or explicit assertions. Re-record only this unit's snapshots, and inspect the diff before accepting it.
- **ui:** browser tests assert user-visible outcomes via accessible names; wait on conditions, never on fixed sleeps.
- **perf:** measure against a committed budget (bundle size, render count, timing) rather than eyeballing.

## Anti-hang rules

- After 2 identical failures of the same long command with no change to the root cause, stop and report with evidence.
- Watch-mode runners hang non-interactive sessions — always invoke the single-run mode.
- Verify by the produced artifact (build output, coverage file, screenshot), not the exit code alone.
