# Node Stack — Verification Guidance

How the generic gates apply to Node.js units. The project's adapter config (`unit-loop.adapter.yaml`; see the unit-loop skill's `references/project-adapter.md`) maps each slot to a concrete command.

## Iteration ladder

1. Read the code / reason statically.
2. Typecheck when the project is TypeScript — the cheapest contract check.
3. Scoped test run (single file or name filter) — the workhorse for logic correctness.
4. In-process endpoint tests via the framework's injection/test client — no listening socket needed.
5. Live-run against a locally started service — for behavior only observable end-to-end (streaming, sockets, real dependencies).
6. Full suite — once per unit as the final regression gate.

## Gate notes

- **test-scoped / test-full:** hermetic by default — no live network calls; external services are faked at the client boundary and destructive/integration tests gate behind an explicit opt-in flag. Scope to this unit's tests during the loop; the full suite runs once after review.
- **build:** for TypeScript or bundled services, a clean compile is a deterministic gate; for plain JavaScript the project may map build to a no-op and rely on lint + test.
- **lint:** the project's lint config is the contract; do not disable rules inline to pass a gate.
- **api-smoke:** probe the changed endpoints for status, schema shape, and auth behavior. Read-only probes run freely; mutating probes need explicit confirmation and a scoped test database.
- **perf:** measure against a committed baseline (latency, event-loop delay, memory) rather than eyeballing.

## Anti-hang rules

- After 2 identical failures of the same command with no change to the root cause, stop and report with evidence.
- Watch-mode runners and servers without a timeout hang non-interactive sessions — always invoke single-run modes and bound live-run checks.
- A test process that does not exit usually holds an open handle (server, pool, timer) — fix the leak; do not mask it with a force-exit flag.
- Verify by the produced artifact (response body, DB row, log line), not the exit code alone.
