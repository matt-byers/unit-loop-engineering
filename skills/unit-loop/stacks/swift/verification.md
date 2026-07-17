# Swift Stack — Verification Guidance

How the generic gates apply to Swift units. The project's adapter config (`unit-loop.adapter.yaml`; see the unit-loop skill's `references/project-adapter.md`) maps each slot to a concrete command; this doc explains when each gate earns its cost.

## Iteration ladder

Reach for the cheapest rung that answers the question, and drop back down after:

1. Read the code / reason statically.
2. Scoped build-for-testing (compiles app + test bundles, no simulator launch) — answers "does this compile".
3. Live-session iteration: launch the app once, then hot reload + screenshot per attempt — the workhorse for "does this render/behave right".
4. Scoped unit/store test for logic correctness.
5. Scoped snapshot test for deterministic pixel layout.
6. Scoped UI test (single method) — expensive; use to confirm an interaction you already believe is correct, not to discover whether it is.
7. Full suite — once per unit as the final regression gate, never mid-debugging.

## Gate notes

- **test-scoped / test-full:** run scoped to this unit's test classes during the loop; the full suite runs once after review.
- **build:** a test-bundle compile is the cheap RED/compile check; warnings from incremental builds are not trustworthy — certify zero-warning claims only from a build that actually recompiled the files in question.
- **snapshot:** record scoped to this unit's snapshot classes only, inspect the recorded image (identical spinners "pass" while testing nothing), then rerun without recording. Async-loaded content and live-composited materials never render in a synchronous snapshot host — cover those with a live screenshot instead of keeping a blank baseline that reads as coverage.
- **ui:** UI tests assert reachability and interaction, never exact pixel geometry on custom-positioned views — route exact-position assertions to snapshots. Wait for hittable, not mere existence, before tapping anything behind an animation; scope taps by element type, not any-element label match.
- **perf:** compare against a committed baseline the project owns; take the median of sampled iterations because early iterations are warm-up outliers.

## Anti-hang rules

- Never run the same multi-minute build/test command twice expecting a different result — after 2 identical failures, stop and report with evidence.
- Verify by the produced artifact (files on disk, images, result bundles), not the exit code or summary line.
- Redirect long command output to a log file and grep for the real error; never pipe raw build logs into context.
