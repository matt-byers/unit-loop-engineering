---
name: spec-plan
description: Interview the user, inspect the repository, and write a concise implementation spec whose requirements map to self-contained implementation units. Use for multi-unit, cross-boundary, high-risk, or architecture-shaping work that needs an implementation plan before coding.
---

# Spec Plan

Create the shortest plan that gives an implementation agent everything it needs to complete and verify the work.

Before dispatching an explorer or plan-review agent, load [the agent-dispatch reference](../unit-loop/references/shared/agent-dispatch.md).

## Planning Boundary

Planning is read-only except for the owning spec under `loop-engineering/specs/`. Do not edit code, run tests, or create implementation artifacts. Keep the draft uncommitted until the user explicitly accepts it and asks to begin implementation.

Use `loop-engineering/specs/{DD-MM-YYYY}-{feature-name}.md`.

## Core Rules

### Keep the spec small

- Include only requirements, high-level architecture or flow that materially clarifies the system, implementation units, and verification.
- Prefer editing, merging, or deleting existing text over appending another section.
- Keep one source of truth for each fact. Requirements define goals; units reference requirement IDs. Do not also map units from the requirement list.
- Do not add standalone source audits, boundary summaries, universal-contract sections, review ledgers, or implementation diaries. Put actionable context in the unit that uses it.
- Do not preserve superseded proposals or rejected review feedback in the final spec.
- Reject infrastructure, abstractions, compatibility layers, state machinery, and future-proofing that are not required by an FR/NFR and verified by a unit.
- Use links and exact source paths instead of reproducing external guidance.

### Make every unit self-contained

An implementation agent should be able to read one unit and know:

- which requirements it satisfies;
- what it depends on;
- which files it changes;
- which skills and source material to use;
- what existing behavior to reuse and what to exclude;
- what to build;
- how to prove it works.

Put assumptions, source reuse, exclusions, architecture constraints, and implementation decisions in the owning unit. If one unit creates a shared contract, later units should reference that unit instead of restating the contract.

### Plan tests before implementation

- Every FR and NFR must map through a unit to implementation and verification evidence.
- Every automatable smoke-test behavior must have a test written before implementation. Name the test file, the behavior that should initially fail, the focused command, and the expected passing result.
- Keep three evidence types distinct: tests prove behavior deterministically; self-verification proves the unit and its owning gate pass; smoke tests describe action → user-observable outcome.
- Every smoke test must declare whether a manual check is required. Use `/human-verify` only for human judgment, physical interaction, consent, or user-controlled external setup. Logs, traces, APIs, database state, and other agent-readable evidence are not manual checks.
- The spec is the durable source of truth for required manual checks, their status, and their evidence.

### Use phases only when useful

Group units under optional phases when the work has a meaningful sequence, such as setup → foundation → integration → rollout. A phase is a short outcome label, not another layer of requirements or repeated context.

Do not invent lifecycle states merely to support phase headings. `Depends on` remains the execution authority.

Omit a global execution-waves section by default. `/unit-loop` can derive waves from unit dependencies. Add a compact execution-order diagram only when non-obvious parallelism or branching materially improves understanding.

## 1. Establish Context

### Start from the request

Use the user's description as the feature definition. If it is missing, ask what they want to build. Use linked issue or ticket context when the repository provides it; do not add empty tracking sections.

### Read the owning guidance

Before planning an affected area, read the repository's owning architecture source, development manual, named workflow, and canonical `SKILL.md` files. Use the `unit-loop` stack-selection guidance to identify applicable bundled stack docs and verification gates.

Consult `/review-standards` and relevant installed best-practice skills while planning so implementation and review inherit the same guidance. External skills are advisory: when one is unavailable, record equivalent repository or bundled guidance instead of blocking the plan.

Use current primary framework documentation only when project guidance and installed skills do not answer a version-sensitive question.

### Inspect before asking

For substantial work, inspect in parallel:

1. related implementation and architecture patterns;
2. related tests, fixtures, test conventions, edge cases, and focused and full verification commands;
3. reusable utilities, skills, scripts, and existing artifacts.

Verify that each planned deliverable does not already exist. When it does, plan to reconcile or adapt it rather than recreate or overwrite it. Record exact reuse and exclusion instructions in the owning unit.

When existing behavior is genuinely unclear, record a concise hypothesis in the owning unit with the evidence behind it and the implementation-time check that will confirm or reject it. Do not create a separate hypothesis section.

## 2. Interview and Define Requirements

Read [the interview-workflow reference](../unit-loop/references/shared/interview-workflow.md) when an interview is needed.

- Research before asking.
- Group related questions.
- Resolve user, behavior, scope, failure handling, architecture, and verification decisions.
- Push separate features out of scope.
- Stop when no important ambiguity remains.

Write the requirements first. They are the high-level goals of the plan:

- **Functional requirements** describe observable capabilities or outcomes.
- **Non-functional requirements** describe quality, safety, compatibility, performance, operational, or architectural constraints.
- **Out of scope** records only exclusions needed to prevent implementation drift.

Give each requirement a stable ID. Keep each requirement to one testable statement.

## 3. Add High-Level Structure Only When Helpful

After requirements, add an optional architecture or workflow section only when it makes relationships materially easier to understand. Prefer one small Mermaid diagram, tree, or table.

Keep this section structural. Put detailed source paths, edge cases, exclusions, and implementation instructions in units.

## 4. Build Self-Contained Units

Create the smallest independently verifiable units that still produce meaningful progress. Group them under optional phases when that improves navigation.

For every unit:

- list concrete file paths with no “if needed” hedges;
- record requirement IDs only on the unit;
- list semantic and file dependencies;
- name applicable skills;
- include exact existing sources to reuse and behavior to exclude inside the unit implementation notes;
- name the generation method for generated artifacts;
- identify the tests to write or change first, their expected initial failure, and their focused command;
- define deterministic self-verification with expected exit codes or output, followed by the owning full test gate;
- define one or more action → observable-outcome smoke tests and classify each as automated or genuinely manual;
- keep assumptions local and state how implementation will verify them.

When a unit changes a canonical list, registry, mapping, or enumerated contract, list every consumer vocabulary or category it must cover and add a deterministic completeness check that fails when a valid category is orphaned.

Two units depend on each other when they overlap files or when one consumes a type, schema, behavior, or shared decision introduced by the other. Do not force parallelism.

After drafting, verify:

- every FR and NFR is referenced by at least one unit;
- every unit references at least one FR or NFR;
- every FR and NFR has implementation and verification evidence in its units;
- every automatable smoke test maps to a planned test-first artifact;
- no unit silently recreates an existing source or shared contract;
- no requirement or implementation instruction is duplicated in multiple sections.

## 5. Review Without Growing the Plan

Run `agent:gap-detector` for plans with more than three units or meaningful security, data, architecture, or cross-boundary risk. Add the specialist reviewers when their scope applies:

- `agent:utility-pattern-auditor` when a unit adds or replaces utilities, abstractions, infrastructure, or patterns that may already exist in the repository or framework.
- `agent:feasibility-validator` when a unit depends on uncertain framework behavior, external capabilities, credentials, environment setup, cross-unit sequencing, or a verification strategy that may not be runnable.

Ask reviewers for deltas:

- exact requirement or unit affected;
- verified problem;
- smallest correction;
- text that should be replaced or removed.

Reviewers must flag missing requirement-to-test coverage, missing negative or edge-case coverage, unclear deterministic verification, manual checks the agent could perform, and canonical inventories without completeness checks.

Treat findings as hypotheses and verify them against repository evidence. Apply verified findings by editing the owning requirement, diagram, or unit. Discard false positives and out-of-scope suggestions without adding a review log to the spec.

A review suggestion is not actionable unless it protects a requirement, closes an implementation gap, or strengthens verification. Review iterations should make the plan clearer or shorter; they must not accumulate parallel explanations.

The plan is converged when no verified blocking or important gaps remain.

## Spec Template

```markdown
# {Feature Name}

## Requirements

### Functional Requirements

- [ ] **FR1 — {name}:** {one observable capability or outcome}

### Non-Functional Requirements

- [ ] **NFR1 — {name}:** {one quality, safety, compatibility, or operational constraint}

### Out of Scope

- {only exclusions that prevent likely scope drift}

## Architecture / Workflow

{Optional: one concise diagram, tree, table, or cross-unit decision. Omit when unnecessary.}

## Implementation Plan

# Phase 1: {Optional outcome label}

## Unit 1: {name}

**Requirements:** FR1; NFR1

**Depends on:** none

**Apply skills:** `/relevant-skill`

**Changes**

- `exact/path/to/file`

**Implementation**

- {minimum behavior and decisions needed to implement the unit}
- Reuse `{exact source}` for `{specific contract}`.
- Exclude `{domain-specific or obsolete behavior}`.

**Assumptions to verify**

- {Optional assumption}: verify by {read-only inspection or implementation-time check}.

**Tests first**

- `{test file}`: {behavior that must initially fail}
- Red: `{focused test command}` → {expected failure}
- Green: `{focused test command}` → {expected passing result}

**Self-verification**

- `{agent-runnable deterministic check}` → {expected exit code or output}
- `{owning full test gate}` → {expected passing result}

**Smoke tests**

1. **{Scenario}:** {action} → {observable result}
   - **Manual check:** Not required — covered by {test/check}
2. **{Scenario}:** {action} → {observable result}
   - **Manual check:** Required — {human judgment, physical interaction, consent, or user-controlled external setup}
   - **Manual status:** Pending
   - **Evidence:** {agent-readable corroboration, or why only user observation is possible}

## End-to-End Verification

{Optional: only cross-unit journeys not already covered by unit verification.}

## Sources

{Optional: external links referenced by multiple units. Keep repository source paths inside their owning units.}
```

Omit optional headings when empty. Do not include template placeholders in the final spec.

## Output

Write the draft spec and report:

- path;
- FR/NFR count;
- phases and units;
- any genuine unresolved decision.

Do not include a long plan recap in chat. Do not commit or begin implementation until the user explicitly accepts the spec and asks to proceed.
