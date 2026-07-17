---
name: unit-loop
description: "Autonomous feature loop — drives one unit at a time through TDD → implement → verify → review → UX check → mark done without steering at each step. Escalates LOOP BLOCKED messages for decisions it cannot resolve alone. Scope: one spec, all uncompleted units."
argument-hint: "[spec file path or empty to auto-detect]"
---

# Autonomous Feature Loop

Load `references/shared/agent-dispatch.md` before dispatching any child.

```text
role: general-purpose
task: Follow the stage-specific task in the referenced unit-loop stage document for {unit}.
mode: sequential
```

Drives a spec to completion without user steering. The user approved the spec before this runs. Human input is only needed when the loop hits a genuine blocker.

**Note: The current year is 2026.**

> **When this loop (and a full spec) is overkill — check first.** For a **Tier-1 change** (see Step 0.5) — a one/two-file bug fix, copy tweak, or small self-contained helper with low surface and easy reversibility — you do **not** need `/spec-plan`, a spec file, or this loop's subagent machinery. Fix it directly, add or adjust the scoped test that pins the behavior, run one focused review over the diff, commit. Reserve `/spec-plan` + the full loop for multi-unit, high-surface, or hard-to-reverse work. If the loop is *already* running on a change that turns out to be Tier-1, Step 0.5 drops it to that lightweight inline path rather than fanning out. Right-sizing up front is cheaper than a converged plan you didn't need.

## Quick reference

This CORE is always loaded — keep it tight. Each stage's detailed brief lives in a `references/` file, read **only when you enter that stage** (progressive disclosure: don't pay for every stage's brief on every turn). Stage-to-skill routing lives in `references/stage-routing.md`; read it after loading the spec and use it whenever a unit's `Apply skills` list is missing, ambiguous, or needs stage-specific support.

| # | Stage | Brief to read on entry | GREEN gate (the checkable artifact) |
|---|---|---|---|
| 0 | Load spec | (below, in CORE) | spec parsed, units enumerated |
| 1 | TDD — tests first | `references/stage-1-tdd.md` | `git status --short`: only test files changed; tests fail for the right reason |
| 2 | Implement | `references/stage-2-implement.md` | `git status --short` / `git diff --stat`: files changed match the unit |
| 3 | Test gate | `references/stage-3-test-gate.md` | test runner's verbatim pass/fail output: all pass |
| 4 | Code review (+ Stage H) | `references/stage-4-code-review.md` | structured findings: no BLOCKING/HIGH |
| 5 | Behavior verify `[conditional]` | `references/stage-5-6-conditional-gates.md` | the behavior-verification artifact defined by the project/stack adapter (e.g. UI/snapshot verification for a frontend unit, a captured live-run transcript for a backend/agent unit) |
| | ↳ **Stage 4 and Stage 5 run concurrently** after Stage 3 is green — both depend only on Stage 3 and don't mutate source (see "Run review and behavior-verify concurrently" below). | | |
| 6 | Eval gate `[conditional]` | `references/stage-5-6-conditional-gates.md` | eval scores ≥ baseline |
| 7 | Mark complete | `references/stage-7-8-mark-and-retro.md` | commit SHA + spec checkbox flipped |
| 8 | Per-unit retro `[conditional]` | `references/stage-7-8-mark-and-retro.md` | **if** the unit had a RED retry / HIGH finding / guidance-gap signal → `compound-learnings` **invoked** + patches committed (or explicit "ran clean"); **else** a one-line "ran clean, no retro" note (no skill spawn) |
| — | Feature complete | `references/stage-7-8-mark-and-retro.md` | clean warning sweep empty; whole-feature `compound-learnings` **invoked** + patches committed |

(Stage H — Harness Improvement — is a conditional sub-stage of Stage 4; its brief lives in the Stage 4 reference file.)

**Always-on rules (apply at every stage — read in full below):**
- Gate on ground truth, never on a subagent's prose.
- Artifact-based gating: every stage gates on a checkable artifact named in the subagent brief, never on a narrative.
- **Stage routing** — `references/stage-routing.md` is the authority on which docs, skills, project agents, and gates apply at each phase. The spec's `Apply skills` list remains the portable handoff, but if it is missing or incomplete, derive the missing entries from stage routing before dispatching implementation or review.
- **Skill continuity** — the unit's applicable best-practice skills (selected from `/spec-plan`'s canonical unit-type table and recorded in the spec) must be surfaced in EVERY implement and review subagent brief, and the subagent must report which it applied; when you customize or shorten a brief, copy the skill list verbatim — never drop it. An orchestrator-written brief that omits the unit's best-practice skills is a process miss (a hand-written parallel brief silently dropping them is how skills get used unevenly).
- **Independent units run in parallel as full-pipeline subagents, not by hand-rolling concurrent stage calls.** Step 0.6 (`references/parallel-waves.md`) is where dependency detection, wave-building, the same-file collision guard, and the dispatch protocol live — always build the wave plan there before batching anything, don't improvise a parallel dispatch inline. The rest of this rule set (ground-truth gating, one-at-a-time commits, contended-tree hygiene below) applies unchanged inside a wave.
- **Contended-tree commit hygiene** — when another session may share this working tree, (a) commit with an EXPLICIT pathspec — `git commit -- <this unit's files>` — never a bare `git commit`/`git commit -a`, which commits the whole index and silently captures another session's staged files; verify with `git diff --cached --name-only` before committing; (b) commit each unit IMMEDIATELY after it verifies — uncommitted work is unprotected and a parallel `git stash` can sweep it away; (c) if HEAD moves unexpectedly, or tracked changes vanish while untracked files survive, suspect a parallel `git stash`/commit — check `git stash list` and recover with `git stash apply` rather than assuming the work is lost or re-doing it; keep a backup branch before any history surgery.
- **Live collision with another session's WIP** — a transient import/test error, or a file you already committed showing as modified with no edit from you, means another session is actively editing files you overlap with (not necessarily your unit's own files — a spec dependency, a shared registry, a shared prompt file). Don't chase every intermediate state: re-read the CURRENT content of any shared file immediately before you edit or gate on it, rather than trusting a snapshot from earlier in the unit. If the collision changes a fact your spec depends on (a file's existence, a tool's registration, a scope boundary), ask the user once with the concrete discrepancy; if they don't respond and multiple independent review agents converge on the same reading of ground truth (consistent, deliberate-looking evidence — not just one transient diff), prefer that ground truth over a stale verbal confirmation and adapt the spec's scope with a changelog note documenting the flip, rather than re-creating something the other session is actively and consistently removing. Never fight the other session's tree to force your original plan through.
- **The iteration ladder — climb only as high as the question in front of you requires, and drop back down immediately after.** During implementation and any RED→fix cycle, reach for the CHEAPEST rung that can answer the question. Never default to the top rung because it's the most thorough — thoroughness is what the end-of-unit pass (tactic 2 below) is for, not what you reach for mid-debugging.
  1. **Read the code / reason statically** — free, instant.
  2. **Compile/typecheck only (the stack's build-without-running-tests slot)** — confirms "does this compile/parse" in a fraction of a full test run's time. Stacks with no compile step skip this rung.
  3. **Live-session iteration** (start the project's live app/dev-server session ONCE, then edit → hot reload → inspect per attempt) — near-zero cost per iteration once the one startup is paid. This is the workhorse stack-adapter slot for "does this render/behave right" — UI, gesture, layout debugging belongs here, not in a full test invocation.
  4. **Scoped unit test** (the stack's scoped test invocation, single class/case) — for logic correctness; no live app session or interaction synthesis needed.
  5. **Scoped snapshot/deterministic-visual test** — deterministic pixel-exact layout, still no live interaction needed. (Only for stacks that define a snapshot gate.)
  6. **Scoped end-to-end/UI test (single method)** — expensive: full compile + fresh app launch + real interaction synthesis. Use to CONFIRM an interaction you already believe is correct from rungs 1-5, not to discover whether it's correct.
  7. **Full suite (the project's deterministic test gate command)** — most expensive; exactly once per unit as the final regression gate (tactic 2 below), never mid-debugging.

  Before rung 6 or 7, be able to state which of rungs 1-5 you already tried and why they couldn't answer the question — "I want to check if this fixed it" does not justify skipping straight to a full test run.

  **This ladder governs iteration and early RED confirmation.** Stage 1 should prove the newly-written test is a real RED with the cheapest sufficient artifact: static missing-symbol evidence first, then a compile-only check if compile behavior is unclear, and only a scoped test run when the expected RED is a runtime assertion failure. Stage 3 remains the first mandatory test-execution gate.
- **Right-size the whole process to the change — not just verification (see Step 0.5 tiers).** The calibrated tier scales TDD depth, review breadth, *and* verification together: a Tier-1 change skips the subagent fan-out and the 6-agent review entirely, a Tier-3 change gets the full treatment. The tactics below are the verification half of that; apply them at the tier you picked.
- **Match verification depth to the scope of the change.** Run the *minimum* that validates THIS unit during the loop; pay for full-suite / full-build verification *once*, at the end, as a regression check. Don't rebuild the world or run all tests at every stage. Seven tactics:
  1. **Stage 1 TDD is test-authoring, not a build gate.** Confirm RED cheaply: for tests that intentionally reference missing API, grep/static inspection of the test and production files is enough; for ambiguous compile behavior, use the stack's compile-only check; reserve a scoped test run for tests expected to compile and fail at runtime. During implement and per-unit test-gate, run ONLY this unit's test classes via the stack's scoped test invocation, not the full suite. **Scoped snapshot runs must use the same environment/reference-directory configuration the project's deterministic test gate sets** — a raw scoped invocation without it can resolve baselines to the wrong (or read-only) path and produce a *false RED*. When in doubt, verify snapshots via the project's deterministic test gate command, not a hand-rolled invocation.
  2. **Full regression suite runs ONCE** — after code review (Stage 4) is GREEN, before Mark (Stage 7) — to catch cross-unit breakage. Not at every stage.
  3. **Re-record ONLY the unit's snapshots** (scoped record) — never a blanket record-all-baselines run; that churns unrelated baselines and buries the real diff.
  4. **Skip the live-session golden-path for static visual units** already covered by snapshot baselines + a visual baseline inspection; reserve live UI automation for units that add NEW interactive flow/gestures.
  5. **When a unit's own spec already flags its visual gate as "live session, not snapshot" (async/remote content, or rendering effects the snapshot renderer cannot reproduce per the stack's architecture doc), do NOT run a per-unit cold snapshot record+verify cycle at all.** Each scoped test invocation still pays a multi-minute cold/incremental build, and the resulting baseline for these units is empty or blank — a slow build purchasing a worthless artifact. Instead: start the live app session ONCE at the start of a run of visual units, then iterate purely through hot reload across the whole run of units, and verify each one with a **live screenshot** of the actual state, not a synchronous snapshot render. Defer any snapshot re-record to ONE pass at feature-end (tactic 2's full-suite pass already covers this) — and if the re-recorded baseline comes back blank/near-blank, exclude that test rather than keeping a blank baseline that reads as coverage.
  6. **A build compiles a test bundle; hot reload only refreshes a view already running in a live process.** Don't reach for hot reload to satisfy a unit-test/snapshot gate — those need a real compile. Reach for it specifically to *look at* a view change without paying a build each time.
  7. **This applies just as hard to debugging a gesture/layout/positioning bug as it does to "static visual units"** — see the iteration ladder above. If the live-session inspector tooling hits friction (an empty element tree, a stale ref) on the first try, debug that friction or fall back to a manual/scripted interaction — do not abandon the live-session loop wholesale and revert to rebuild-per-iteration (observed directly in the source project: ~10 full test-suite cycles were burned where hot reload + screenshot would have done it in seconds each).
- Retry budget + hang breaker (see Escalation Protocol).
- Anti-hang protocol for long commands.
- Never pipe raw build logs into context — only pre-parsed summaries (the project's test gate script should produce these).
- Implementation decisions follow `references/shared/decision-tree.md`.
- Select stack packs with `references/stack-selection.md`, map project commands with `references/project-adapter.md`, and use `references/third-party-skill-registry.md` fallbacks when external skills are unavailable.
- Harness-improvement patches (changes under project skills, project agents, or `loop-engineering/`) are committed as a separate `loop:` commit — never folded into a feature unit's commit.

---

## Step 0: Load Spec

<spec_path> #$ARGUMENTS </spec_path>

**If empty:** Find the most recently modified spec in `loop-engineering/specs/` with at least one uncompleted unit (`- [ ]`).

```bash
ls -t loop-engineering/specs/*.md | head -5
```

Read the spec. Extract:
- Feature name
- All implementation units (find lines matching `### Unit`)
- Which units are already checked off (`- [x]`) vs pending (`- [ ]`)
- For each unit: the **Changes** (files), **Self-Verification**, and **Smoke Tests** fields

Report:
```
Spec: loop-engineering/specs/{file}
Units: {N} total, {M} completed, {K} remaining
Starting with: Unit {n} — {name}
```

## Step 0.5: Calibrate rigor to scope

**The loop's default is maximum ceremony (full TDD + 6-agent review + full-suite regression per unit). That is right for a risky multi-unit feature and wasteful for a one-file bug fix.** Before running any stage, size the work and pick a rigor tier. Re-judge per unit when units differ in risk. The user can always override ("quick fix" / "be thorough"), and a later finding can pull you *up* a tier mid-unit.

Score the work on four signals — **any single HIGH bumps the tier up**:
- **Surface/risk** — touches auth, `user_id`, untrusted input, secrets, money, RLS, a DB migration, the state schema, or a wire/SSE/API/tool contract → HIGH. A pure internal helper, copy/string tweak, config value, or self-contained function → LOW.
- **Size** — 1–2 files, no new abstraction → LOW; several files or a new subsystem → HIGH.
- **Reversibility** — trivially revertible → LOW; data-affecting / hard to reverse → HIGH.
- **Type** — mechanical fix or refactor under existing tests → LOW; genuinely new behavior → MED/HIGH.

| Tier | Fits | Process to run |
|---|---|---|
| **1 — Light** | 1–2 files, low surface, reversible — the typical bug fix, copy tweak, or small internal helper | **Skip the subagent fan-out — do it inline.** Add/adjust the one or two tests that pin the behavior (or verify-after when there's no meaningful unit to test), implement, run the scoped tests, do **one** review pass over the diff (self-review, or a single reviewer for the one dimension at risk), commit. No tests-first subagent, no 6-agent review, no per-unit doc/retro unless a real lesson surfaces. |
| **2 — Standard** | a few files, some real surface, new behavior in one area | Tests-first for the unit → implement → scoped tests → **targeted review: only the dimensions the diff actually touches** (Stage 4 selection) → full suite once before mark. |
| **3 — Rigorous** | security/auth, data migration, state-schema or wire/contract change, multi-unit feature, anything hard to reverse | Full treatment: full tests-first, the full review set **+ adversarial verification of findings**, full suite, doc/retro. |

Announce the tier and the one signal that set it (`Tier 1 — single-file internal fix, reversible`), then run the stages at that tier. **When torn between two tiers, pick the lower** and let review/verification pull you up — don't pre-pay for rigor the change may not need. A whole spec can be one tier while a single risky unit inside it is bumped higher.

## Step 0.6: Map Unit Dependencies & Build a Wave Plan

Before running units one at a time, check whether any of them are independent enough to run concurrently. **Check the spec first — `/spec-plan` now writes a `Depends on:` field per unit and a `## Unit Execution Waves` section directly into the spec.** If both are present, that IS the wave plan (no need to re-derive it) — but still run the collision guard in `references/parallel-waves.md` §3 before dispatch, since specs can be edited or partially hand-written after planning. If the spec predates this (no `Depends on:` fields), read `references/parallel-waves.md` now and derive the wave plan yourself using its dependency rules.

Report the wave plan before Stage 1 runs on anything, e.g.:

```
Wave 1: Unit 1
Wave 2: Unit 2, Unit 3 (independent — disjoint files, no shared state)
Wave 3: Unit 4
```

A spec where every unit builds on the previous one's schema/state/tools collapses to one unit per wave — that's a correct answer, not a failed search for parallelism. Re-check the wave plan if a unit's scope changes mid-spec (a RED cycle that touches an unplanned file, a spec edit).

## Step 1: Recall Prior Retros

Skim `loop-engineering/retros/` for any retrospective relevant to this feature type and surface its key process lessons before the first unit. The loop's hard rules already live in the skill/agent files and load automatically — this step is only for the softer, contextual lessons a retro captured (what slowed us down last time, traps to avoid). If there are no relevant retros, say so and continue.

---

## The Unit Loop

For each uncompleted unit, run through the stages in the Quick-reference table **in order**. **On entering a stage, read its `references/` brief** — that file holds the subagent prompt, the exact GREEN/RED/BLOCKED conditions, and the required return artifact. Advance only on GREEN. On RED, attempt to fix (per-stage caps live in each brief). On BLOCKED, stop and emit the escalation message.

**If Step 0.6 grouped this unit into a multi-unit wave, don't run the stages below directly — dispatch it via `references/parallel-waves.md` instead.** Same GREEN/RED/BLOCKED gates, same stage briefs, just executed inside that unit's own parallel subagent alongside its wave-mates. A wave of size 1 (or a Tier-1 unit, which skips subagent fan-out entirely) runs the sequential path below as normal.

### Gate on ground truth, never on a subagent's prose

A stage outcome is decided by the **actual working-tree state** — `git status --short`, the files on disk, the real test run — **not** by what a subagent's final message claims. Subagent reports drift from reality: an agent can overstep its scope (write files it was told not to), under-report (say "no implementation written" when files exist), or mis-state what passed. If the orchestrator advances on the narrative alone, it will redo or collide with work that already exists, or mark done something that never ran.

So at **every stage boundary**, before deciding GREEN/RED/BLOCKED, the orchestrator (main thread) independently verifies:
- `git status --short` — what *actually* changed, vs. what this stage was supposed to change.
- For test/build gates: re-read the result file or re-run the check; don't trust "all green" prose.
- If the working tree diverges from the stage's contract (e.g. a TDD stage produced non-test files, or files the unit already had are being recreated), **stop and reconcile before advancing** — investigate who wrote what and whether the work is already done, rather than dispatching the next stage on a false premise.

This is cheap (one `git status`) and prevents the whole class of "spinning on already-done or out-of-scope work."

### Artifact-based gating — every stage gates on a checkable artifact

Generalises the ground-truth rule above. Every stage's subagent brief names a **mandatory return artifact** — a thing on disk or a verbatim tool output the orchestrator can check — and the GREEN/RED decision is made against *that artifact*, never against the subagent's prose summary. Stages that change code gate on `git status --short` / `git diff --stat`; the test gate on the runner's verbatim pass/fail output; the retro on the retro file existing/updated. If a brief's artifact wasn't returned, treat the stage as not-done and re-run — do not advance on a narrative that an artifact was produced.

### Run review and behavior-verify concurrently

**Stage 4 (code review) and Stage 5 (behavior verify) both depend only on Stage 3 (test gate) being GREEN, and neither mutates source** — so once Stage 3 is green, dispatch both in one batch and gate **Stage 7 (Mark complete) on BOTH being GREEN**:
- **Frontend/UI unit:** Stage 4 review agents + the Stage 5 UI/snapshot verification gate in parallel; mark only when review has no BLOCKING/HIGH *and* the verification gate shows tests pass with no snapshot diffs.
- **Backend/agent unit that changes observable behavior:** Stage 4 review agents + the Stage 5 live behavior-verification run in parallel (the transcript/artifact it writes isn't a source mutation); mark only when review is clean *and* the artifact shows the change working end-to-end. A backend unit with no behavioral surface has no Stage 5 — run Stage 4 alone.

**Precondition — tools must be pre-allowlisted.** This concurrency only works if the loop's recurring tool calls are pre-allowlisted in `.claude/settings.json` (git, the project's build/test commands, jq/grep, etc.). **Backgrounded or fanned-out subagents auto-DENY any tool call that would otherwise prompt for permission**, so a non-allowlisted command would silently fail inside a concurrent subagent. If a needed tool is *not* allowlisted, fall back to running Stage 4 and Stage 5 **sequentially** (Stage 4, then Stage 5) rather than concurrently.

### Anti-hang protocol for long commands (builds, tests, codegen)

Most wasted wall-clock in this loop comes from a subagent re-running a multi-minute build/test/record command in a loop, misreading its result, and never stopping. Every subagent brief that runs such commands MUST carry these rules, and the orchestrator follows them too:

1. **Verify by the produced artifact, not the exit code or summary line.** Before concluding a build/record/codegen "worked" or "failed as expected," check the thing it was supposed to *produce* — files on disk, a row count, generated output. A step that is "expected to fail" (e.g. snapshot record mode) MUST still leave its artifact; **zero artifacts means it did not run**, whatever the exit code says. Filesystem ground truth overrides the "TEST FAILED" summary.
2. **Read the tool's own message before applying a "known/expected failure" template.** Confirm the actual library/tool text on *this* run; never infer "by-design failure" from an exit code alone. (A `read only` / permission / `rec=false` / missing-env message is a *real* failure, not the by-design one.)
3. **Circuit-breaker — never run the same expensive command twice expecting a different result.** After **2 identical failures** of the same multi-minute command with no change to the root cause, STOP and report BLOCKED with the evidence. Every retry must follow a *deliberate change* to the input — state what changed and what different result you expect. **The same cap applies when the blocker is external contention (another session's build/tree state), not your own command** — after ~2-3 attempts to get a clean confirmation run blocked by someone else's WIP, stop chasing a clean window: commit the reasoned, already-diagnosed fix with an explicit "unverified due to environmental contention" note, rather than continuing to re-poll. Retrying against a shared, actively-changing tree costs the user's time waiting on you, not just yours — this is a different flavor of the same "don't loop hoping it clears" discipline as an identical-command retry.
4. **Timeout every build/test invocation, and treat a timeout or interrupt as BLOCKED, not retry.** Set an explicit, tight `timeout` on any build/test Bash call. Exit **143/144 (SIGTERM/INTERRUPTED)** and timeouts are *never* "transient" — they mean killed/hung; surface them, don't re-run identically.
5. **Shorten the feedback loop before iterating — hard cap: 2 blind fix attempts, then instrument.** Debug one variable with the *cheapest* command that exposes it — a single scoped test case, an `env`/debug-print probe — not the full clean-regen-build-test pipeline. If a full-cycle re-run "fixes" a hypothesis-driven guess and the observed failure value doesn't change (e.g. the same exact number, the same exact error), that's not evidence the hypothesis was *close* — it's evidence the theory is wrong and you're guessing blind. **After 2 such attempts on the same assertion, stop guessing and add direct instrumentation** (use the stack's structured logging facility and read it back through the channel that actually captures the process under test — a plain stdout print may never reach the runner's captured log) before trying a 3rd fix. One instrumented run that shows the actual runtime value is worth more than five theory-driven rebuilds. Pay the full pipeline once, to confirm the final fix.
6. **Don't gate a long command behind `… | tail -N`** (it blocks until completion and hides the real error). Redirect stdout/stderr to a log file (`command > /path/to.log 2>&1`) and run the shell call synchronously in the foreground, with no trailing `&` or `nohup`, until the command exits. Then grep the log for the real error message, not the trailing summary.
7. **Never pipe raw build logs into context** — they are huge and low-signal. Use pre-parsed summaries where the project's test gate script produces them; if you must read a raw log, grep it for the specific error and quote only that.
8. **A UI-automation framework's geometry query on a custom-positioned view is not reliable ground truth — don't assert exact geometry through it.** Observed directly in the source project: an overlay's reported frame read `0.0` from the UI-test framework across four structurally different positioning implementations, while direct log instrumentation proved the underlying layout math was computing the correct value the whole time. The mismatch was a limitation in how the framework's accessibility-frame query resolves custom-positioned view compositions, not an app bug — six rebuild cycles were burned chasing it as if it were one. **Route exact-position/exact-clamping assertions to a snapshot test instead** (deterministic, no gesture choreography, seconds not minutes per iteration); end-to-end UI tests should only assert reachability and interaction (element exists, a tap dispatches the expected observable effect), never pixel geometry, for custom-positioned views.

**Pre-flight check before ANY build/test invocation that shares mutable build state: check for an already-running build process and wait for a clear result before starting your own.** Two build processes racing the same shared build cache/derived-data path can silently interrupt or corrupt each other's build even when neither is backgrounded — observed repeatedly as "build interrupted" mid-dependency-compile with zero error lines. This is expected in a shared working tree with concurrent sessions (per "Contended-tree commit hygiene" above) — it is not a sign anything is broken, just contention. If the check finds a live process, wait for it to clear (poll every 5-10s) before proceeding; do not run your own build over it.

**Observed failure mode: a child detached a multi-minute build call and ended its turn before the command finished.** The child process was killed when the session ended, leaving an interrupted build without a test result. Any build/test-class command must run synchronously: do not append `&` or use `nohup`; the shell call must block until the command exits.

**Orchestrator corollary — don't fire-and-forget a loopable agent.** A long subagent (especially `implement`) that can loop on a flaky command is invisible if you dispatch it and end your turn. If such an agent is backgrounded, monitor its progress (poll the working tree / its artifact), and if it runs well past the expected time with no artifact change, stop it and take over — don't wait for the user to notice. Backgrounding also risks the agent's context resetting mid-task and re-doing setup, so prefer foreground for steps that can loop. **If a subagent backgrounds a build/test command twice in the same unit despite being told not to, stop delegating that specific step and have the orchestrator run it directly** — a third delegation attempt is unlikely to behave differently.

**Detection signal for the same failure mode in your own dispatches:** if the sentence you are about to end your turn on is "waiting for" / "waiting on" the agents you just fired, that sentence IS the fire-and-forget failure, not a status update — stop, and instead block/poll (`Monitor`, or a foreground call) until they actually return. This applies doubly when you are yourself a nested sub-orchestrator dispatching your own Stage 4 review agents (per `parallel-waves.md`): you have no supervisor left to hand an arrival notification to but yourself, so ending your turn on "waiting for the review agents to report back" silently stalls the unit until someone else notices and takes over.

---

## Escalation Protocol

When any stage reaches BLOCKED, stop immediately and output:

```
LOOP BLOCKED — {stage name}
Unit: {unit name from spec}
Reason: {one sentence — what specifically is wrong}
What I tried: {brief — how many retries, what the fix attempts were}
What I need: {specific decision or action from user — be precise}

To verify manually, run these smoke tests:
{smoke tests section verbatim from the spec unit}
```

Do not attempt to continue past a BLOCKED state. Do not skip stages.

Run `/human-verify {unit name}` to guide the verification, record the result in the owning spec, and convert observations into automation. Re-invoke `/unit-loop` once the blocker is resolved.

### When to escalate

- **Per-stage BLOCKED** — any stage's brief reaches its BLOCKED condition (see that stage's `references/` file).
- **Cumulative retry budget** — each stage has its own local RED cap, but track RED cycles *across all stages* in the unit too: **more than 4 total RED cycles in one unit → escalate**, with the full retry history (which stages went RED, how many times, the fix attempts) — not just the local per-stage count. A subtle problem that bounces stage-to-stage burns wall-clock without ever tripping a single stage's local cap; the cumulative budget catches it.
- **Per-stage hang breaker** — if a subagent makes no progress past **N minutes** (no artifact change, no working-tree change), kill it and escalate rather than waiting for a human to notice the hang. **N is a starting value to tune via retros** — no external source fixes the number; begin around 15-20 min for build/test-heavy stages and adjust from the retro evidence.

---

## Decision Rules During the Loop

Follow the shared implementation decision tree in `references/shared/decision-tree.md`. (Covered by spec → proceed; pure implementation detail → decide autonomously; affects architecture/UX/security or is hard to reverse → escalate as BLOCKED; missing optional skill → use the bundled fallback; missing required runtime dependency → escalate as BLOCKED.)
