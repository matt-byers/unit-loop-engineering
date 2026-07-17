# FastAPI Stack — Verification Guidance

How the generic gates apply to FastAPI units. The project's adapter config (`unit-loop.adapter.yaml`; see the unit-loop skill's `references/project-adapter.md`) maps each slot to a concrete command.

## Iteration ladder

1. Read the code / reason statically.
2. Scoped pytest (single file, class, or `-k` expression) — the workhorse for logic and contract correctness.
3. In-process endpoint tests via the framework's test client — no server, no network.
4. Live-run transcript against a running service — for behavior only observable end-to-end (streaming, auth flows, real dependencies).
5. Full suite — once per unit as the final regression gate.

## Gate notes

- **test-scoped / test-full:** hermetic by default — tests never contact live services; external keys are blanked in the test fixture layer and live/destructive tests gate behind an explicit opt-in flag, not on credentials being present. Scope to this unit's tests during the loop; the full suite runs once after review.
- **typecheck:** a deterministic gate in its own right; framework hook overrides and collection fields must match the base class's declared types.
- **lint:** the project's lint config is the contract; do not disable rules inline to pass a gate.
- **api-smoke:** probe the changed endpoints for status, schema shape, and auth behavior. Read-only probes run freely; mutating probes need explicit confirmation and a scoped test database.
- **perf:** measure query counts and latency against a committed baseline; an N+1 introduced by a new relationship is a per-unit check, not a phase-end discovery.

## Blast-radius rule

A changed function signature, serialized message, or wire payload has consumers beyond its own unit test — integration tests often script literal arguments and assert shapes byte-for-byte. Grep the test tree for the old name/field before changing any contract, update the drivers in the same unit, and rely on the full-suite pass to catch the rest.

## Anti-hang rules

- After 2 identical failures of the same command with no change to the root cause, stop and report with evidence.
- Debug one variable with the cheapest probe (a single test, a log line), not a full-pipeline rerun; after 2 blind fix attempts, instrument before a third.
- Verify by the produced artifact (response body, DB row, transcript), not the exit code alone.
