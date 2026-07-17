# Stage 3 — Test Gate

Load `references/shared/agent-dispatch.md` before dispatching `agent:test-runner` or a `general-purpose` subagent to repair failures.

This stage has **two clearly-separated gates**. Right-size verification to the change: the loop's per-unit GREEN/RED gate runs ONLY this unit's tests; the full regression suite runs ONCE per unit, after code review is GREEN, to catch cross-unit breakage — not at every stage.

**Return artifact (mandatory gate):** the test runner's **verbatim** pass/fail output (total passed/failed/skipped, plus file:line + message for any failure). The orchestrator gates on that exact output — never on a "looks green" summary. Never pipe raw build logs into context; only the pre-parsed summary the project's test gate script produces.

---

## Gate A — Per-unit test gate (during the loop)

This is the loop's GREEN/RED gate. Run ONLY this unit's test class(es) via the stack's scoped test invocation — not the full suite.

```text
role: agent:test-runner
task: Run ONLY this unit's test classes for this project — do NOT run the full suite. The recent change was: {unit name}.
Use: the stack's scoped test invocation for {TestClass} [{TestClass2} …] (one scope per class this unit added/changed).

Report:
- Tests run (this unit's classes only): passed / failed / skipped
- Any failing test: file path, test name, failure message
- Whether this unit's tests are GREEN
mode: sequential
```

**Scoped snapshot re-record (orchestrator action):** if this unit's snapshots need recording, re-record ONLY this unit's snapshot test class(es) (a scoped record run), never a blanket record-all-baselines full run — a blanket run churns unrelated baselines. This is an ORCHESTRATOR-level action, never done inside the implement subagent.

**GREEN**: This unit's tests pass, zero type errors.
**RED**: One or more of this unit's tests fail. Spawn a fix subagent with the failure output. Retry the per-unit gate. Maximum 2 fix+retry cycles. After 2 RED outcomes: BLOCKED.
**BLOCKED**: Test infrastructure broken (env issue, missing fixture, build won't compile). Escalate with the error.

> **A test-target compile failure is not automatically this unit's RED.** A shared test target can be broken by an unrelated file the user is editing concurrently in a parallel session (e.g. a WIP reference to a not-yet-defined member). Before treating a compile failure as RED or BLOCKED, check `git status`/`git diff` for the unit's own files: if the failing file is **outside** this unit's scope, it is the user's uncommitted WIP — not this unit's regression. Do NOT edit it and do NOT `git checkout`/overwrite it. Isolate it non-destructively (back it up, then `git stash push -- <path>` or wait for the tree to settle), run the scoped gate, then restore it. The break may be transient, so re-check ground truth before escalating.

---

## Gate B — Full regression suite (once, after Stage 4 review is GREEN, before Stage 7 Mark)

Run the project's full deterministic test gate command ONCE, after Stage 4 (code review) is GREEN, before Stage 7 (Mark complete). For frontend/UI units, Stage 4 review runs concurrent with Gate A above (the scoped per-unit check); the full regression suite is the post-review step — so the ordering is: Gate A + Stage 4/5 concurrent → review GREEN → Gate B (full regression) → Mark. Rationale: the per-unit gate proves THIS unit's tests pass, but a unit can silently break something elsewhere; the full suite catches that cross-unit breakage. Paying for it once per unit (not per stage) keeps the loop fast while still guarding the whole suite before merge.

```text
role: agent:test-runner
task: Run the FULL test suite for this project (the project's deterministic test gate command). The recent change was: {unit name}. This is the cross-unit regression check before marking the unit done.

Report:
- Total tests: passed / failed / skipped
- Any failing test: file path, test name, failure message
- Whether all tests are GREEN
mode: sequential
```

**GREEN**: All tests pass, zero type errors → proceed to Mark.
**RED**: A test outside this unit's classes regressed. Spawn a fix subagent with the failure output. Retry. Maximum 2 fix+retry cycles. After 2 RED outcomes: BLOCKED.
**BLOCKED**: Test infrastructure broken. Escalate with the error.

## Per-unit warning surfacing (after Gate A GREEN)

Once the per-unit test gate (Gate A) is GREEN, force-recompile **only this unit's new/changed source files** to surface the stack's warning classes (e.g. strict-concurrency in a Swift stack, or deprecations) that incremental builds hide — instead of waiting for the feature-end clean build. Key it to the unit's changed files:

```bash
git diff --name-only HEAD~1..HEAD | grep -E "{the stack's source-file extensions}"
```

`touch` those files (to invalidate their cached object) and rebuild so the compiler re-emits their diagnostics, then read the warnings for *those files only*. This is a targeted recompile of a handful of files, not a clean build of the world — it stays cheap per-unit while catching warnings in files this unit authored or changed that an interim incremental build already compiled clean. The full clean warning sweep at **Feature Complete** still owns the cross-file NFR1 enforcement; this step only closes the gap for the unit's own files.

> **Warning counts from an incremental build are not trustworthy.** The project's test gate (and any plain scoped build) in a compiled stack typically builds incrementally — it only recompiles files that changed since the last build, so compiler warnings (stack-specific warning classes, e.g. strict-concurrency or deprecations) in files it *doesn't* recompile never re-appear in the log. This means a per-unit "zero warnings" check can read clean while real warnings sit in untouched files — or even in a file this unit created, if an interim build already compiled it. So: trust the incremental run for **pass/fail**, but do **not** certify a zero-warnings policy (NFR1) from it. Warning enforcement requires a build that actually recompiles — see the clean warning sweep at **Feature Complete**. Per-unit, a full clean build (it rebuilds every dependency) is usually too slow to run every unit; reserve it for the phase boundary. If you must spot-check a single unit's new file for warnings, force just that recompile rather than cleaning the world.

Fix subagent task:
```text
role: general-purpose
task: Fix failing tests.

Unit implemented: {unit name}
Test failures:
{test runner output}

Fix the failures. Do not change test assertions — if the test is right and the code is wrong, fix the code. If the test itself is wrong, explain why before changing it. The symmetric trap: if making a test pass requires degrading the artifact's content or contorting the implementation (e.g. a test pattern that also matches inside an unrelated construct), suspect the test — verify its intent against the spec, then fix or escalate the test; never bend the content to fit a flawed test.
Return: what you changed and why.

IMPORTANT — Guidance gap detection. Apply this one criterion: **Could a subagent following current guidance have avoided this? If yes → not a gap (fix and move on). If no → emit a GUIDANCE GAP.** When it is a gap, add one or more lines at the end of your response in this exact format:
GUIDANCE GAP: [skill file path] / [rule to add] / [severity: BLOCKING|HIGH|MEDIUM|LOW] / [category in that skill]

Example:
GUIDANCE GAP: skills/review-standards/SKILL.md / Effects started from a lifecycle hook must be cancellable with a stable id / HIGH / Category 2 — Framework Pattern Compliance

If no guidance gap exists (the fix was simply a bug), do not add this line.
mode: sequential
```
