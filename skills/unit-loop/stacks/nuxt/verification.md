# Nuxt Stack — Verification Guidance

How the generic gates apply to Nuxt units. The project's adapter config (`unit-loop.adapter.yaml`; see the unit-loop skill's `references/project-adapter.md`) maps each slot to a concrete command. Nuxt's Vue component layer and its Nitro server layer verify differently — treat them as two surfaces inside one unit, not one undifferentiated "frontend."

## Iteration ladder

1. Read the code / reason statically.
2. Typecheck (`nuxi typecheck` or equivalent) — regenerate Nuxt's `.nuxt` type layer first if auto-imports or route/composable additions are new; a stale type layer produces false typecheck failures that look like real ones.
3. Live-session iteration: start the dev server once, then edit → hot module reload → inspect per attempt — the workhorse for "does this render/behave right" on the Vue component layer.
4. Scoped component/unit test (single file or test name filter) for component and composable logic.
5. Scoped server-route test — call the route handler directly (in-process or via a local request), not through a browser; this is the cheap way to confirm a Nitro route's contract.
6. Scoped SSR/render test — render a page server-side and assert on the produced HTML for anything a component-mount test can't see (hydration-sensitive markup, meta tags, redirects).
7. Scoped browser/e2e test — expensive; confirm, don't discover.
8. Full suite — once per unit as the final regression gate.

## Gate notes

- **test-scoped / test-full:** scope to this unit's test files during the loop; the full suite runs once after review. Test Vue components through rendered output and user-facing queries; test server routes through their handler contract (input → response shape/status), not through internal Nitro plumbing.
- **typecheck:** a deterministic gate in its own right — auto-import and route-typing errors surface here. Regenerate the project's Nuxt type layer before trusting a red result; a green test run with a red typecheck is not GREEN.
- **lint:** the project's lint config is the contract; do not disable rules inline to pass a gate.
- **snapshot:** prefer small, intention-revealing snapshots over whole-tree captures that churn; re-record only this unit's snapshots and inspect the diff before accepting it. A snapshot renderer captures one render mode only — if the unit's bug is SSR/hydration-specific, a client-only snapshot cannot see it; route that to the SSR/render check instead.
- **ui:** browser tests assert user-visible outcomes via accessible names; wait on conditions, never on fixed sleeps. Whatever browser-automation tool the project already has configured is canonical — don't introduce a second one to satisfy this gate.
- **api-smoke:** probe changed `server/api` routes directly (status code, response shape, auth/validation edge cases) — this is the fast way to verify server-only logic without paying for a full browser session.
- **live-run:** capture the SSR output of a changed page/route from a real running server — this is what catches a hydration mismatch that a component-mount test and a snapshot both miss, because both render client-only.
- **perf:** measure against a committed budget (bundle size, render timing, server-route latency) rather than eyeballing.

## Anti-hang rules

- After 2 identical failures of the same long command with no change to the root cause, stop and report with evidence.
- Watch-mode runners (dev server, test watch mode) hang non-interactive sessions — always invoke the single-run mode.
- Verify by the produced artifact (build output under `.output/`, coverage file, screenshot, captured SSR HTML), not the exit code alone.
