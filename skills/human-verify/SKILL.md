---
name: human-verify
description: "Guide user-run verification for spec smoke tests that genuinely need human judgment or external setup, record the result in the owning spec, and convert repeatable observations into automation. The spec is the only durable source of truth."
argument-hint: "[unit name or empty to detect from recent BLOCKED]"
---

# Human Verify

Before dispatching a `general-purpose` subagent, load the agent-dispatch reference bundled with the `unit-loop` skill.

Use this skill only for smoke-test scenarios that the agent cannot complete alone because they require human judgment, physical sensation, interactive consent, or user-controlled external setup. Do not create a separate verification log or ledger. The owning file in `loop-engineering/specs/` is the sole durable record.

## Step 0: Find the Owning Spec

<unit_name> #$ARGUMENTS </unit_name>

If the unit is omitted, use the current `LOOP BLOCKED` context or the most recent spec with a pending manual smoke test. Read the unit and its smoke tests in full.

For every scenario, distinguish:

- Agent verification already completed, including tests, commands, logs, screenshots, traces, or database assertions.
- A manual check marked `Required` with `Manual status: Pending` in the spec.
- A scenario that can now be verified agentically and should no longer require the user.

Report the unit, the number of pending manual checks, and what the agent has already established. Never ask the user to repeat an agent-verifiable assertion.

## Step 1: Minimize the Human Action

Before involving the user, run every safe agent-owned setup and assertion available. The human should perform only the irreducible action, such as judging animation feel, confirming a haptic, completing OAuth consent, or enabling an external service they control.

Present one pending scenario at a time:

```text
Scenario {N}/{total}: {name}
You: {minimum action}
Expected: {observable outcome from the spec}
I will verify: {agent-readable evidence, when available}
```

Ask what they did and observed. If the answer is only "it worked," ask what specifically confirmed it. Capture the exact action, observation, result, setup, and friction.

## Step 2: Verify and Classify

Pull any agent-readable evidence named by the scenario. Classify the result:

- `Passed` only when the user observation and any promised agent evidence agree.
- `Failed` when the expected result did not occur or evidence contradicts it.
- `Blocked` when required setup or evidence is unavailable.

Then classify the future verification path:

- `Automate now`: expressible with an existing command, test, UI driver, log, trace, or query.
- `Add coverage`: needs a new XCTest, XCUITest, snapshot, pytest, or integration test.
- `Keep manual`: genuinely subjective, physical, consent-gated, or dependent on user-controlled external state.

## Step 3: Update the Spec In Place

Update the matching smoke-test scenario in the owning spec. Preserve its steps and expected result, then set:

```markdown
- **Manual check:** Required — {reason}
- **Manual status:** Passed | Failed | Blocked | Pending — {YYYY-MM-DD; concise observation or blocker}
- **Evidence:** {agent evidence path/query/result, or "user observation only — {why}"}
```

If the scenario is now fully agent-verifiable, replace those fields with:

```markdown
- **Manual check:** Not required — automated by {test/check}
```

Do not copy the result anywhere else. Do not create files outside the owning spec.

For `Automate now` items, use this logical dispatch only when the durable check is more than a small local edit:

```text
role: general-purpose
task: Add the identified durable automated check to the specified test, verification skill, or spec Self-Verification section; run its focused validation and return the changed paths plus result.
mode: sequential
```

Make small local edits directly. For `Add coverage`, add the precise missing test case to the spec and leave the manual check pending until that coverage is implemented and proven.

## Step 4: Report

Report pass, fail, and blocked counts; the exact spec updated; any automation added; and the remaining pending manual checks in that spec.

If any check failed, hand the observed failure to `/bug-loop` when it fits that scope or back to `/unit-loop` when it requires a broader change. If a check is blocked by missing external setup, leave its spec status `Blocked` with the specific requirement.

## Design Intent

Manual verification is part of the spec, not a parallel workflow. Each run should either close a spec scenario or make it more agentic. A feature cannot be declared complete while a required manual check is `Pending`, `Failed`, or `Blocked`; a deliberate deferral must change the spec's scope instead of silently accepting an unverified requirement.
