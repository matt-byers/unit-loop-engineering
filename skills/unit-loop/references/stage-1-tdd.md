# Stage 1 — TDD: Write Tests First

Load `references/shared/agent-dispatch.md` before dispatching a `general-purpose` subagent for the RED phase.

**Scale to the calibrated tier (Step 0.5):**
- **Tier 1 (Light):** don't spawn a tests-first subagent. Add or adjust just the one or two tests that pin the changed behavior (inline, yourself), or — when the change has no meaningful unit to test (a copy tweak, a config value) — skip tests-first and rely on the verify-after step. Still confirm the new/edited test fails first if you wrote one.
- **Tier 2 / 3:** full tests-first as below (one test per smoke scenario + edge cases), via the subagent.

The rest of this brief is the Tier-2/3 procedure.

Before any implementation exists, write the tests for this unit.

**Return artifact (mandatory gate):** the TDD subagent's report MUST include the verbatim output of `git status --short` and the cheapest RED evidence it used. The orchestrator gates on that — confirming ONLY test files (plus at most test-target wiring) changed — never on the subagent's prose claim of "tests only".

Dispatch a `general-purpose` subagent. A nested sub-orchestrator must wait for its result before evaluating the gate; ending while the result is pending stalls the unit.

```text
role: general-purpose
task: Write tests first for this unit — before any implementation.

Unit: {unit name}
Files to change: {changes from spec}
What this unit does: {description from spec}

Smoke test scenarios from spec:
{smoke tests section verbatim from the spec unit}

Your task:
1. Write one test per smoke test scenario above — these are the primary tests.
   - Place tests following the consuming project's established test layout (integration/journey tests where the project keeps them, unit tests where it keeps those) — never invent a parallel layout. (Examples only: an iOS project might keep journey tests in an integration test target and logic tests in a unit test target; a backend might use `tests/integration/` and `tests/unit/`.)
   - Name each test after its scenario in the project's naming style: `test_happy_path_sign_in`, `testListExpandsOnFirstItem`, etc.
   - For a unit whose artifact is a setup or procedure document, the primary test must EXECUTE the documented procedure against a temp target — copy exactly the documented destinations, run the documented commands, and require the owning verifier/gate to pass. Section-presence and name checks alone cannot prove the document is sufficient.
2. Write any additional unit tests needed to cover edge cases not captured by the scenarios.
3. Confirm the RED with the cheapest artifact that proves the new tests cannot be green before implementation:
   - If the test intentionally references missing API (new type/action/property/method), do NOT run any test invocation. Report the exact test references and `rg`/static evidence that the production symbol does not exist yet. This is a valid RED and avoids paying for a full run just to rediscover a missing symbol.
   - If the expected RED is compile-related but static evidence is ambiguous, run the stack's compile-only check (e.g. a build-for-testing slot) for the relevant test target. It compiles the code and test bundles without launching anything or executing tests. Stacks with no compile step skip this rung.
   - Only run the stack's scoped test invocation when the test is expected to compile and fail at runtime (assertion failure, snapshot mismatch, UI interaction failure). Never run the whole suite in Stage 1.
4. Confirm each failure/evidence is expected — missing function / type / class, or a deliberate runtime assertion — not a syntax error.
5. Report: test file path, test names written (scenario tests first), RED evidence used (static, compile-only, or scoped test) confirming they fail for the right reason.

Do not write any implementation code. Tests only.

SCOPE — HARD BOUNDARY: create/modify ONLY test files (and, if strictly required to make the test target compile and surface the right RED, the project's test-target wiring). You may create implementation/source files ONLY as empty stubs if a stub is the only way to reach a meaningful RED — and if you do, say so explicitly and list every non-test file you touched. Never write a working implementation here. Your final report MUST include the output of `git status --short` so the orchestrator can confirm only test files changed.
mode: sequential
```

**GREEN**: Tests exist and have credible RED evidence from the cheapest sufficient source (static missing-symbol proof, the stack's compile-only check, or a scoped runtime test) — **and the orchestrator has verified via `git status --short` that ONLY test files (plus at most test-target wiring) changed.** If the TDD agent's report and the working tree disagree (it claims "tests only" but source/implementation files changed, or implementation files the unit was meant to create already exist and pass), do NOT advance to Stage 2 on the report — reconcile first: read the files, use the cheapest artifact that answers the discrepancy, and if the implementation is already present and green, skip the redundant Stage 2 and move to the gate that isn't yet satisfied. Advancing the loop is driven by what's on disk, not by the prose (see "Gate on ground truth" in the core).
**RED**: Tests fail with syntax error or wrong file — fix and retry once.
**BLOCKED**: Cannot determine what to test. Emit escalation with: what the unit says and what's ambiguous.
