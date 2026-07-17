# Step 0.6 — Parallel Waves

Load `references/shared/agent-dispatch.md` before dispatching a `general-purpose` subagent for each unit.

Reached once, before Stage 1 runs on anything. Goal: find units in this spec that can safely run concurrently, without two subagents editing the same file or racing the shared git index — and without reaching for worktrees unless a real collision demands it.

**If the spec already has `Depends on:` fields and a `## Unit Execution Waves` section (written by the current `/spec-plan`), skip §1–2 — that section already answers this. Go straight to §3 (collision guard) before dispatch.** §1–2 below are the fallback derivation for specs written before that field existed, or where a hand-edit may have invalidated the recorded waves.

## 1. Detect dependencies (fallback — only if the spec has no recorded wave plan)

For every pair of uncompleted units, decide DEPENDENT or INDEPENDENT. **Default to DEPENDENT** — a missed dependency produces a broken build or a unit implemented against a schema/tool that doesn't exist yet; an unnecessary DEPENDENT just costs some wall-clock.

Two units are DEPENDENT if either is true:

- **File overlap** — their spec `Changes` fields share a file. Read `Changes` literally, including shared registration/config files (a tool-list in a graph-wiring module, a shared fixtures file, a shared test helper) — those collide just as hard as two units editing the same feature file.
- **Semantic/data dependency** — one unit's `Technical Approach`, `Changes`, or `Smoke Tests` assumes a type, schema, table, tool, or state shape that another unit introduces, even in different files. This is the common case: a DB-schema unit feeds a state-shape unit, which feeds a tools unit, which feeds an API unit — such chains are fully sequential despite each unit touching different files. Specs are usually already numbered in dependency order; only pull a later unit forward into an earlier wave if you can positively confirm — by reading both units' Technical Approach sections — that it doesn't need anything an earlier one produces.

Otherwise INDEPENDENT.

## 2. Build waves

A wave is a maximal set of units that are pairwise INDEPENDENT and whose dependencies (per the graph above) are all in earlier, already-complete waves. Compute it as a simple topological pass: wave 1 = units with no incomplete dependency; wave 2 = units whose only dependencies sit in wave 1; and so on.

Report the plan before dispatching anything (see the Step 0.6 example format in the CORE skill file). Both outcomes are normal, and the shape depends on the spec, not on this algorithm: a bottom-up architecture migration (schema → state → tools → API) collapses to one unit per wave because each layer's code imports/type-depends on the one before it; a set of independent bug fixes hitting separate failure modes (fixes that touch disjoint files and don't call into each other) produces real multi-unit waves. Don't force either shape — derive it from the actual `Changes` lists and code dependencies in front of you.

## 3. Collision guard — re-check right before dispatch

Specs can get edited between planning and execution, so re-diff the wave's units' `Changes` lists pairwise immediately before dispatching, even though step 1 already checked this. If two units in the same wave now share a file:

- **Default:** pull one out of the wave and run it in the next wave instead. Zero setup cost, and most waves in this codebase are already file-disjoint.
- **Only if the parallel speed is worth the setup cost:** dispatch that specific pair with `isolation="worktree"` and merge them sequentially afterward. Worktrees are the exception for a genuine same-file collision inside an otherwise-parallel wave — not the default execution mode for waves in general.

## 4. Dispatch a wave (size ≥ 2)

Dispatch one `general-purpose` subagent per unit in a single capacity-aware batch. Each subagent runs that unit's entire Stage 1–6 sequence, including permitted nested logical dispatches, and reads the same briefs used for a sequential unit:

```text
role: general-purpose
task: You are running ONE unit of the unit-loop skill end-to-end, in parallel with sibling agents working on other units' files in the same repo.

Read these from the loaded `/unit-loop` skill before starting, and follow them exactly — do not resolve them from the consumer repository, paraphrase them, or skip them:
- the loaded `/unit-loop` skill's CORE (ground-truth gating, artifact-based gating, the iteration ladder, and the anti-hang protocol)
- its bundled Stage 1 TDD reference
- its bundled Stage 2 implementation reference
- its bundled Stage 3 test-gate reference
- its bundled Stage 4 code-review reference
- its bundled Stage 5/6 conditional-gates reference

Spec file: {spec_path}
Unit to run: {unit name} — read the unit itself from the spec, do not work from a paraphrase.
Rigor tier for this unit: {tier from Step 0.5}
Relevant prior-retro learnings: {learnings from Step 1}

Run Stage 1 through Stage 5/6 (TDD → implement → test gate → code review + behavior-verify, running review and behavior-verify concurrently per CORE) for THIS UNIT ONLY. Follow each stage's logical role declarations and the shared dispatch contract.

Do NOT commit. Do NOT touch the spec file's checkboxes. Do NOT run stages for any other unit — if you notice another unit's files changing under you, that is a sibling agent; do not touch them.

Return GREEN with the Stage 3 test output, the Stage 4 review verdict, and the Stage 5/6 result — or RED/BLOCKED using the same escalation-message shape the skill defines (reason, what you tried, what's needed), including retry counts.
mode: parallel
```

Dispatch every unit in the wave this way, in parallel, in one message.

## 4.5 Shared files and gates inside a wave

- **Shared append-only registries** (extraction maps, manifests, inventories that several units in the wave must extend): every subagent re-reads the file immediately before editing and appends its entries at the end — never rewrites, reorders, or edits other units' entries. Route a wave-shared file of this shape through that discipline instead of pulling the units apart.
- **Wave subagents run scoped gates only.** Whole-tree contract tests (e.g. "every file in the repo is mapped") false-RED against siblings' in-flight files; the orchestrator runs the full deterministic suite exactly once, after the whole wave has landed.
- **Self-review inside a subagent is not a substitute for review.** A subagent that cannot dispatch real reviewer agents should self-review with at least two lenses and say so in its report — but each subagent sees only its own unit, so after the wave lands the orchestrator must run a cross-unit review with real reviewer agents over the wave's combined diff. Cross-unit contract mismatches are invisible to any single subagent.

## 5. Land results — one at a time, as they arrive

Do not wait for the whole wave in lockstep; handle each completed unit as its result arrives:

- **GREEN** — verify ground truth yourself exactly as any stage boundary does (`git status --short` scoped to that unit's `Changes`, spot-check the reported test output is real, not just narrated), then run Stage 7 (Mark Complete) and Stage 8 (per-unit retro, if triggered) for that unit **immediately**, before moving to the next arrival. This is where "commit one at a time, explicit pathspec" (Contended-tree commit hygiene, CORE) binds hardest — never batch two units' commits together, even when both finish within moments of each other.
- **RED** — the subagent already exhausted its own local fix retries for whichever stage tripped (per that stage's brief). Treat it as that unit's stage outcome: dispatch a fresh, better-briefed retry for just that unit, same as the sequential path would. Don't touch sibling units over this.
- **BLOCKED** — do not cancel sibling agents still running. Let the rest of the wave land and commit normally first, then surface this unit's escalation via the standard Escalation Protocol once the wave has otherwise finished.

Once every unit in the wave has landed (GREEN-and-committed, or escalated), run the wave's whole-tree gate and cross-unit review (§4.5), then move to the next wave.

## 6. When not to use a wave

- **Wave size 1** — just run the unit through the normal sequential stage table in CORE. No parallel dispatch, no extra ceremony.
- **Tier-1 units (Step 0.5)** — these already skip subagent fan-out and run inline. Wrapping a Tier-1 unit in a parallel-dispatch subagent adds overhead for a unit that wasn't using subagents in the first place; run Tier-1 units inline even inside an otherwise-parallel wave.
