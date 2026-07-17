---
name: compound-learnings
description: Post-feature retrospective on the loop itself — assess the plan, the code, and how fast we reached green, then make concrete improvements to the loop-engineering skills, agents, and process. Reads manual-check status from the feature spec to push checks from human to agentic.
argument-hint: "[feature name or empty to auto-detect from recent spec]"
---

# Retrospective + Harness Improvement

Before dispatching a `general-purpose` subagent, load [the agent-dispatch reference](../unit-loop/references/shared/agent-dispatch.md).

**Note: The current year is 2026.**

## Purpose

This phase reflects on the **process we just went through** — not the product. The goal is to make the loop better. Its **primary output is concrete edits to the loop-engineering skills, agents, and process** — not stored notes.

There is no external memory store. The loop "remembers" by getting *better*: rules baked into the skill/agent files, sharper review checks, more verification done agentically instead of by a human. A written retro is optional and strictly secondary to the changes you make.

For eval-driven agent improvement loops, this skill owns implementation-loop lessons only: unit-loop staging, TDD, review, test selection, implementation briefs, and development harness process. Scenario design, simulated-user realism, rubrics, hard invariants, artifact capture, and comparison gates belong to `eval-compound-learnings`.

## Two scopes

This skill runs at two cadences — match the depth to the scope:

- **Per-unit (unit-loop Stage 8)** — arg is a single unit name. Reflect on just that unit's loop: did the spec unit hold up, how many RED→fix retries and why, what smoke test still needed a human, any review finding that repeats a class seen before. Lightweight: a clean unit gets a one-line "ran clean"; a unit with retries/HIGH findings gets a real pass. Gather only this unit's slice (its spec section, its checkpoint commit, its review findings) — skip the cross-unit git-churn analysis. Complements Stage H (which only fires on explicit guidance-gap signals); this catches the softer "what should we improve" that no gap signal flagged.
- **Whole-feature (unit-loop Feature Complete)** — arg is the feature/phase name. The full pass below: all units, git churn across all checkpoints, every manual smoke-test status in the spec, the human-dependency trend, and patterns only visible across the whole phase.

The steps below are written for the whole-feature pass; for a per-unit pass, run the same questions scoped to the one unit and skip steps that need cross-unit history.

## Feature Detection

<feature_name> #$ARGUMENTS </feature_name>

**If empty:** detect from the most recent spec in `loop-engineering/specs/` or from recent checkpoint commits.

## Step 1: Gather the Run

Collect what actually happened on this feature:

1. **Spec** — `loop-engineering/specs/{date}-{feature}.md` (the plan as approved)
2. **Verification docs** — `loop-engineering/verify/*`
3. **Review findings** — `loop-engineering/review/*`
4. **Manual smoke-test status** — every `Manual check` and `Manual status` field in the feature spec
5. **Git history** — the checkpoint commits: count, sequence, and any churn/reverts
6. **The loop transcript** (if available) — where it stalled, retried, or escalated

## Step 2: Assess the Process

Answer these honestly. **Every weak answer is a candidate improvement to the loop.**

### Was the plan good?
- Did the spec hold up, or did units get reworked / split / abandoned mid-flight?
- Were there gaps the plan missed that `gap-detector` / `feasibility-validator` / `utility-pattern-auditor` *should* have caught? → improvement to those agents or `/spec-plan`.
- Were units the right size (one session each), or too big / too granular?

### Was the code good?
- How many review findings, at what severity? A repeated finding *type* → a missing rule in `review-standards` or the project's stack review skill.
- Did the same class of bug appear more than once? → a checklist rule or a reusable test pattern.

### How fast did we reach green?
- Count the RED→fix retries per stage. Where did we loop the most?
- Where did iterations get wasted (flaky tests, wrong assumptions, context the `implement` subagent needed but wasn't given)? → fix the brief or skill that should have supplied it.
- Did we escalate to the user for something the loop could have resolved itself? → close that gap.

### What still needed a human? (drive this down)
Read **every** smoke-test scenario marked `Manual check: Required` in the feature spec, including its current status and evidence. For each, decide how to make it agentic:
- Can it become an **XCUITest / snapshot / unit test**? → write it now, or add it to the TDD checklist so it's written next time.
- Can it become an **automated review rule or agent check**? → add it to the relevant review agent or `review-standards`.
- Can the stack's UI verification gate or the project's diagnostic tooling catch it? → wire it in.
- If it genuinely needs a human, record **why** in the retro so we revisit later.

**Target: every feature lowers the human-dependency count.** State the count before and after.

## Step 3: Make the Improvements (primary output)

**Restraint first — keep the skills lean.** A patch is debt: every rule added is read on every future run. Only add or change something when there's a *distinct, demonstrated* need (a real failure or repeated friction this run), not a hypothetical. Prefer editing/sharpening an existing rule over adding a new one; prefer the most general phrasing that covers the case (fix one level up) over a narrow new bullet. If a lesson is already covered by existing guidance, the fix is "follow it," not "restate it." A clean unit should produce zero patches. Bloated skills get skimmed and ignored — concision is what keeps them load-bearing.

Apply each improvement now — these are edits to the loop's own files. Map cause → file:

| What you found | Patch this |
|---|---|
| Missed / undocumented domain pattern or decision | the project's architecture doc for the touched area — record the pattern, the decision + its *why*, and where the canonical example lives. This is the default home for a missed pattern (see "fix one level up"). |
| Missing/weak review rule | `review-standards/SKILL.md` or the project's stack review skill (right category + severity) |
| Missing verification / test | the TDD stage in `unit-loop`, or the stack's UI verification gate; or add the test directly |
| Planning blind spot | `/spec-plan` or the relevant plan-review agent (`gap-detector` etc.) |
| `implement` lacked context | `/implement` or `unit-loop`'s subagent brief |
| Process / sequencing issue | `unit-loop` or its stage references |

Dispatch one `general-purpose` subagent per file in a capacity-aware parallel batch:

```text
role: general-purpose
task: Make a targeted improvement to a loop skill/agent file.

File: {path}
Change: {exact rule/edit to make}
Where: {category + severity section, or the specific step}

Read the file in full, make ONLY this change, match the existing style. Return the exact line(s) added/changed and their location (file:line).
mode: parallel
```

Only edit the operating manual for an always-on routing or ownership invariant. Domain guidance belongs in the architecture docs; workflow detail belongs in the owning skill or stage reference.

### Harness ownership and completion gate

Follow the project's harness ownership rules: edit the repository-owned source files for skills, agents, hooks, loop references, and the operating manual, and never edit through generated or adapter copies the project declares as derived. The project's harness documentation names which paths are sources of truth and which are adapters.

After a skill, agent, hook, or loop-reference edit, run the repository's plugin validation and deterministic test commands. Do not report completion or commit a harness improvement until both are GREEN.

## Step 4 (optional): Write the Retro

Only if there are process lessons worth narrating — context for a future similar feature that isn't a concrete rule. Keep it tight:

`loop-engineering/retros/{DD-MM-YYYY}-{feature}.md`

```markdown
# Retro: {Feature}  ·  {DD-MM-YYYY}

## What slowed us down
- {friction}: {why}

## What we changed in response
- {file}: {patch summary}

## Still needs a human (and why)
- {item}: {why it can't be automated yet}
```

Skip this file entirely if every lesson already became a patch.

## Output

```
Retro: {Feature}
Reached green in {N} checkpoints, {R} RED retries, {E} escalations.
Human dependency: {before} → {after}

Loop improvements applied:
  • {file}: {what changed} [{severity/category}]
  • ...
Automated (was human): {list, or "none this run"}
Retro note: {loop-engineering/retros/... or "none — all lessons became patches"}
```
