---
name: implement
description: Implement one approved spec unit against tests and repository guidance, then return focused verification evidence. Use directly for a single unit or as unit-loop's implementation stage.
argument-hint: "[spec path] [unit name]"
---

# Implement

Implement one approved unit. Planning, full regression testing, review, behavior verification, commits, and retrospectives remain with the calling workflow.

## Load the Unit

Read the canonical spec and the requested unit in full. If no unit is named, select the first incomplete unit. Do not implement from a paraphrase.

Extract:

- requirements and dependencies;
- changed files and implementation instructions;
- `Apply skills`;
- tests-first expectations;
- self-verification; and
- smoke-test behavior.

Stop when the unit is missing, unapproved, internally contradictory, or requires a product, architecture, security, or other hard-to-reverse decision not already covered by the spec.

## Load Project Guidance

Before editing:

1. Read project architecture documents relevant to the changed files.
2. Select every applicable bundled stack using the unit-loop stack-selection guidance and read each selected stack's architecture and verification references.
3. Load every available skill in the unit's `Apply skills` list. For unavailable optional skills, use the bundled fallback guidance and continue.
4. Inspect the files named by the unit and search for existing utilities, patterns, and deliverables before creating anything.

Project guidance wins when it conflicts with bundled generic guidance.

## Establish the Starting State

The unit's tests-first artifact must exist before production implementation begins.

- When the calling workflow already established credible RED, use that evidence.
- Otherwise run the unit's focused RED command before editing production code.
- If the expected test already passes, inspect whether the behavior exists and reconcile the spec instead of manufacturing a failure.
- Do not weaken assertions, rewrite test intent, or modify gate artifacts to obtain GREEN.

Record the initial changed files with `git status --short`. Preserve unrelated work.

## Implement

- Make the smallest production change that satisfies the unit.
- Reconcile existing artifacts instead of recreating or overwriting them.
- Follow established repository boundaries, naming, and error handling.
- Keep changes inside the unit's declared scope.
- Use current primary documentation when a framework contract remains uncertain after reading project and stack guidance.
- Do not add unrelated features, refactors, abstractions, compatibility layers, or infrastructure.
- Do not commit.

If the tests-first artifact is materially wrong because it models a dependency contract inaccurately, stop and report the evidence to the calling workflow rather than silently rewriting the gate.

## Focused Verification

Run the narrowest checks that establish the implementation is ready for the owning test gate:

1. syntax, import, compile, or type check when applicable;
2. the unit's focused test command; and
3. any focused deterministic self-verification named by the unit.

Do not run the full regression suite, code review, live behavior verification, evals, or release steps when a parent workflow owns them. Treat repeated identical failures as evidence the hypothesis is wrong; inspect actual output before another change.

## Return

Return:

- files changed;
- focused command output and exit status;
- project docs, stack references, and skills applied;
- implementation decisions not fixed by the spec; and
- blockers or remaining uncertainty.

The caller independently verifies `git status --short`, `git diff --stat`, and command output. Disk state, not this report, determines completion.
