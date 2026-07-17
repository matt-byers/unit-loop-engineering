# Stage 4 — Code Review (+ Stage H: Harness Improvement)

Load `references/shared/agent-dispatch.md` before dispatching `agent:architecture` or another reviewer.

**Return artifact (mandatory gate):** the concatenated findings from all review agents, each finding carrying a severity (BLOCKING/HIGH/MEDIUM/LOW per the review-standards Severity-Tier Mapping) and a `file:line`. The orchestrator gates on the presence/absence of BLOCKING/HIGH findings in that structured output — never on a "looks clean" sentence. The `git diff` gate-file audit below is itself a checkable artifact.

First, determine the unit type from the changed files:

```bash
git diff HEAD~1..HEAD --name-only
```

- **iOS unit**: any `.swift` files changed → use iOS review set
- **Backend unit**: any `.py` files changed → use backend review set
- **Mixed**: run both sets

Get the full diff:
```bash
git diff HEAD~1..HEAD
```

## Gate-file audit (gate integrity)

Gate files are the verification artifacts an implementation could quietly edit to make a failing gate pass instead of fixing the code — snapshot baselines, performance baselines, eval scenarios. Their path patterns come from **`gate_file_patterns` in the project's `unit-loop.adapter.yaml`** (see `references/project-adapter.md`) — never from a hardcoded list in this skill.

Before the review agents run, check whether this unit touched any of them:
```bash
git diff HEAD~1..HEAD --name-only | grep -E '{the project's declared gate-file path patterns}' || echo "no gate files touched"
```
**If the project has not declared `gate_file_patterns` in its `unit-loop.adapter.yaml`, say so explicitly in the review report** — e.g. "gate-file audit skipped: no gate-file patterns declared by this project" — never silently print "no gate files touched" when there was nothing to check against.

If any gate file changed, **pass that fact into the review brief** and require the reviewers to confirm the change is justified by the unit's spec (e.g. an intentional visual re-baseline that the unit explicitly calls for) — not a silent edit to dodge a red gate. An unjustified gate-file edit is a BLOCKING finding (the `GATE_FILE_MODIFICATION` pattern, P1/BLOCKING, in `review-standards`). The bundled `PostToolUse` hook records gate-file edits as a secondary audit trail when configured by the project (it also catches edits later reverted); the `git diff` above remains authoritative whether or not the hook runs.

## Transformation-claim audit (copy/extraction units)

When a unit copies or extracts files and claims a per-file transformation (generalized, sanitized, redacted, rewritten), the claim is itself a gate artifact: require a reviewer to verify it against the source with a byte comparison (`cmp`/`diff` against the copied-from file). A byte-identical copy carrying a transformed claim is a HIGH finding — the provenance note is false, and the file usually still needs the transformation it claims.

**Wait for every dispatched reviewer before evaluating the gate.** A child running Stage 4 for its own unit has no supervisor to collect later notifications, so it must block or poll until every reviewer reaches a terminal result.

## iOS units — run all 3 in parallel

```text
role: agent:architecture
task: Review the iOS unit's architecture against project guidance. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:security
task: Review the iOS unit's security against project guidance. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: general-purpose
task: Read the project's stack review skill (e.g. a Swift/iOS review skill) in full, then review this iOS unit. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

A stack review skill, where the project provides one, replaces `type-safety` for that stack — it covers stack-specific concurrency, framework patterns, performance, and security, which are more specific and higher-signal than a generic type-safety check.

## Backend units — select reviewers by tier and surface (don't reflexively run all 6)

The full backend set is `architecture`, `security`, `type-safety`, `patterns-utilities`, `performance-database`, `simplicity`. Running all six on a small diff is the single biggest source of wasted wall-clock in the loop (six agents each re-reading the codebase to review 30 lines). **Pick by the calibrated tier (Step 0.5) and by what the diff actually touches:**

- **Tier 1 (Light):** ONE pass — self-review the diff, or a single reviewer for the one dimension actually at risk. Skip the fan-out.
- **Tier 2 (Standard):** only the dimensions the diff touches. Always `architecture` + `simplicity` (cheap, always relevant). Add `security` **only if** the diff touches auth/`user_id`/untrusted input/secrets/URLs/SQL; `performance-database` **only if** it touches queries/loops-over-data/indexes; `type-safety` for non-trivial typing/casts/framework overrides; `patterns-utilities` when it adds a helper that might duplicate an existing one. A pure in-memory helper with no DB and no auth does not need `security` or `performance-database` — say so and skip them.
- **Tier 3 (Rigorous):** all six, **plus adversarial verification** — for each HIGH/BLOCKING finding, dispatch the `general-purpose` subagent skeptic template below before acting. A finding that survives refutation is real; one that does not is dropped with a note.

State which reviewers you ran and which you skipped and why (one line) — a skipped reviewer is a deliberate, recorded choice, not an omission.

```text
role: agent:architecture
task: Review the backend unit's architecture. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:security
task: Review the backend unit's security because its diff touches a DB write path. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:simplicity
task: Review the backend unit for unnecessary complexity. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:type-safety
task: Review the backend unit's non-trivial typing, casts, and framework overrides. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:patterns-utilities
task: Review the backend unit for duplicated helpers and missed established utilities. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: agent:performance-database
task: Review the backend unit's queries, indexes, and loops over data. Unit: {unit name}. Files: {file list}. Gate-file evidence: {gate evidence}. Diff: {git diff}. Return severity and file:line for every finding.
mode: parallel
```

```text
role: general-purpose
task: Try to refute {HIGH or BLOCKING finding} using {diff}, repository evidence, and the applicable project guidance. Return CONFIRMED with evidence or REFUTED with evidence; do not propose unrelated findings.
mode: sequential
```

Skipped in this example: performance-database (no queries added), type-safety (no non-trivial typing), patterns-utilities (no new shared helper).

**GREEN**: No BLOCKING or HIGH severity findings across all agents.
**BLOCKED**: Any BLOCKING finding → escalate with the specific finding, file/line, and what decision is needed.
**RED (HIGH findings)**: Dispatch the fix subagent below, then rerun the affected project-role reviewer using its complete template. One retry. If still HIGH: BLOCKED.

```text
role: general-purpose
task: Fix {HIGH finding} in {unit diff}. Preserve the unit scope, run its focused verification, and return changed files plus verbatim verification output.
mode: sequential
```

## Guidance gap check (Stage 4)

After all review agents complete, spawn a harness evaluator subagent whose only job is to classify findings as guidance gaps:

```text
role: general-purpose
task: You are a harness evaluator. Your job is NOT to find more bugs — the review is done. Your job is to identify which findings represent gaps in the existing skill guidance.

Review findings from this unit:
{concatenated output from all review agents}

Current skill files (read these in full before evaluating):
- the project's stack review skill (when one exists)
- the loaded `/review-standards` skill
- the loaded `/unit-loop` skill's CORE and bundled references

For each finding in the review output, apply this one criterion: 'Could a subagent following current guidance have avoided this? If yes → not a gap (fix and move on). If no → emit a GUIDANCE GAP.'

- YES (foreseeable) → the guidance already covers it, the subagent just didn't follow it. Not a gap.
- NO (not foreseeable) → the skill files have no rule that would have prevented this. This IS a guidance gap.

For each guidance gap, output ONE line in this exact format:
GUIDANCE GAP: [skill file path] / [rule to add as a checklist item] / [BLOCKING|HIGH|MEDIUM|LOW] / [category name in that skill file]

If no gaps found, output: NO GUIDANCE GAPS

Do not output anything else.
mode: sequential
```

Collect all `GUIDANCE GAP:` lines from the evaluator's output. If any found, Stage H fires **after Stage 4's normal GREEN/RED/BLOCKED outcome** — it never blocks or delays progress on the current unit.

---

# Stage H — Harness Improvement (conditional)

**Trigger:** Any `GUIDANCE GAP:` signals collected from Stage 3 or Stage 4.

**Skip if:** No gaps were found.

**Return artifact (mandatory gate):** for each patch, the exact line(s) added and their `file:line` location — proof the skill/doc file actually changed. The orchestrator confirms the edit landed before reporting the harness improved.

**Does NOT block or redo the current unit.** The current unit's implementation is kept — it passed review or is being fixed by the normal RED path. Stage H runs after the unit's gate outcome is determined and improves the loop for the *next* unit.

## Principle: fix one level up — never overfit a general skill to a specific problem

When formulating a patch, solve the problem at **one level of abstraction higher** than the instance that failed. The failure is almost never "the agent didn't know pattern X" — it's "the agent didn't look where pattern X already lives, or didn't do the research that would have surfaced it." So fix the **process of finding the right answer**, not the answer.

- ❌ Overfit: add "use a debounced publisher for search-as-you-type" to a skill.
- ✅ One level up: add "before building reactive UI input, check `Features/` for the established Combine/TCA pattern and confirm against the TCA docs via Context7" — so the agent discovers the right pattern itself, here *and* in cases we haven't seen yet.

A good patch makes the agent more likely to **discover** correct patterns across the whole problem space. A bad patch only answers the one case that just broke. Smell test: if the rule names a specific library, value, or snippet tied to one feature, it's overfit — raise it a level (where to look, what to verify, what to research).

**Where the fix goes:**
- A missed **domain pattern or decision** (the stack's "right way") → document it in the project's architecture doc for the touched area. These are read at planning time, so documenting it there is what makes the next plan follow it. This is the home for most "we missed a pattern" gaps.
- A missed **process rule** (how the loop itself should have caught it — a review check, a verification step, where to look) → patch the relevant skill/agent.

## Step 1: Deduplicate and print gaps

```
Harness gaps found ({N}):
1. {skill file} → "{rule}" [{severity}] [{category}]
2. ...
```

## Step 2: Patch each skill file

For each unique gap, spawn a subagent:

```text
role: general-purpose
task: Add a missing rule to a skill file.

Skill file: {file path}
Rule to add: {rule text}
Severity tier: {BLOCKING|HIGH|MEDIUM|LOW}
Category: {category name}

Instructions:
1. Read the skill file in full.
2. Find the named category section and the correct severity tier within it.
3. Add the rule as a new checklist item (- [ ] format), matching the existing style exactly.
4. Do not change anything else.

CRITICAL — fix one level up, do not overfit: the rule must improve how the agent FINDS the right approach (where to look in the codebase, what to verify, what to research), not hardcode a specific answer tied to this one feature. If you are about to name a specific pattern, library, value, or snippet, generalise it to the search/research step that would have surfaced it.

Return: the exact line(s) added and their location (file:line).
mode: parallel
```

Run patches **in parallel** if multiple gaps. The patch to the skill file **is** the durable record — there is no separate memory store to log to.

## Step 3: Report and continue

```
Harness improved — {N} rule(s) added for future units
  • {skill file}: "{rule summary}" [{severity}]
  • ...
Continuing to Stage {5 or 6 or 7}...
```

The current unit proceeds normally.
