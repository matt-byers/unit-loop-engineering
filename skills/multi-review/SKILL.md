---
name: multi-review
description: Run exhaustive multi-agent parallel code review with taxonomy-based findings
argument-hint: "[origin: branch|pr <number>|area <path>] [base: main]"
---

# Exhaustive code review with parallel specialist agents

Before dispatching `agent:architecture` or another reviewer, load the agent-dispatch reference bundled with the `unit-loop` skill.

## Quick reference

1. **Required reading** — load `review-standards` (taxonomy + severity tiers) and the decision-tree reference bundled with the `unit-loop` skill.
2. **Determine review origin** — branch diff (default) / PR / area audit.
3. **Pre-agent analysis** — unrelated-changes, removed-export impact, new-concept inventory.
4. **Spawn 6 parallel review agents** — type-safety, patterns-utilities, performance-database, architecture, security, simplicity.
5. **Architectural zoom-out** → **finding verification** (agents are not oracles) → **classify by scope**.
6. **Generate review document** → **fix loop** (P1 by tier, then P2/P3) → **re-review** → **completion** → trigger `/compound-learnings`.

## Introduction

**Note: The current year is 2026.**

Unit Work review spawns 7 parallel specialist agents to perform exhaustive code review. Reviews are taxonomy-based, mapping findings to 47 known issue patterns with tier-based severity ranking.

---

## Required Reading

**Before reviewing, load the `review-standards` skill which contains:**

- 47 issue patterns with detection criteria and severity tiers
- Team standards to enforce
- Implementation checklists

The skill provides the taxonomy reference needed for categorizing findings.

**Shared decision boundary.** When a fix decision during review needs autonomy-vs-escalate judgment (proceed, decide autonomously, or stop for the user), follow the decision-tree reference bundled with the `unit-loop` skill. Do not restate it here.

## Determine Review Origin

Parse the arguments to determine what to review:

**Branch Diff (default):**
```bash
# multi-review [base-branch]
BASE_BRANCH="${1:-main}"
git diff $BASE_BRANCH...HEAD --stat
git diff $BASE_BRANCH...HEAD
```

When using branch diff mode, check if a PR exists for the current branch:
```bash
CURRENT_BRANCH=$(git branch --show-current)
gh pr list --head "$CURRENT_BRANCH" --json number,title,url
```

**If PR exists:** Prompt user: "Found PR #{number}: {title}. Review PR or branch diff?"
- **Review PR** - Switch to PR Review mode
- **Review branch diff** - Continue with branch diff

**PR Review:**
```bash
# multi-review pr <number>
# OR
# multi-review pr (auto-detect)
```

**If `pr` is specified WITHOUT a number:** Auto-detect PR by current branch:
```bash
CURRENT_BRANCH=$(git branch --show-current)
gh pr list --head "$CURRENT_BRANCH" --json number,title,url
```

- **If single PR found:** Confirm: "Found PR #{number}: {title}. Review this?"
  - If user confirms: Proceed with PR review
  - If user declines: Ask for PR number manually
- **If multiple PRs found:** Present list and ask user to select
- **If no PR found:** Ask for PR number manually

**If PR number is provided:**
```bash
gh pr view $PR_NUMBER --json title,body,files,additions,deletions
gh pr diff $PR_NUMBER
```

**Codebase Area Audit:**
```bash
# multi-review area <dir_path>
# Review all files in a directory/pattern
find "$AREA_PATH" -type f \( -name "*.ts" -o -name "*.py" -o -name "*.rb" \)
```

## Pre-Agent Analysis

Before spawning specialist agents, perform these checks directly. These catch issues that require holistic diff awareness — no single agent can reliably detect them.

### 1. Unrelated Changes Check

Review the list of files in the diff against the PR title/purpose:

- For each file, ask: "Is this change related to the PR's stated purpose?"
- Config files (tsconfig.json, package.json, etc.) changed without clear relation to the feature → flag as `REVERT_UNRELATED_CHANGES`
- Files that appear to be drive-by fixes or unrelated refactors → flag as `REVERT_UNRELATED_CHANGES`

These are immediate findings — they don't need agent processing.

### 2. Removed Export Impact Check

Parse the diff for removed or renamed exports (functions, types, classes, constants):

```bash
# Look for removed exports in the diff
# Lines starting with - that contain 'export'
```

For each removed/renamed export:
1. **Search the codebase** for usages of the removed name using Grep
2. If still referenced elsewhere, flag as `BREAKING_CHANGE_CONCERN` (P1 Tier 1)
3. Include the list of files still referencing the removed export

### 3. New Concept Inventory

List any new domain concepts introduced in the diff (new type names, new ID patterns, new module names, new terminology). Pass this inventory to agents with the note:

> "These new concepts were introduced in this PR. Scrutinize whether each is well-defined, clearly named, and necessary."

This gives agents explicit targets to question rather than hoping they notice new concepts on their own.

---

## Severity Tiers

Issues are categorized into two tiers that affect priority ranking:

### Tier 1 - Correctness (Always Higher Priority)
Issues affecting whether code works correctly:
- Security vulnerabilities
- Architecture problems (wrong boundaries, circular deps)
- Implementation bugs (incorrect logic, runtime errors)
- Type safety violations (casting that hides bugs)
- Functionality gaps (missing error handling, edge cases)

### Tier 2 - Cleanliness (Lower Priority)
Issues affecting maintainability but not correctness:
- Naming clarity
- File organization
- Code duplication (when not causing bugs)
- Comment quality
- Import/style consistency

**At the same P-level, Tier 1 issues must be addressed before Tier 2 issues.**

## Severity Definitions

| Level | Tier 1 (Correctness) | Tier 2 (Cleanliness) |
|-------|---------------------|---------------------|
| P1 CRITICAL | Security vuln, arch causing bugs, runtime errors | (Rare) Cleanliness issue causing production confusion |
| P2 IMPORTANT | Type casting, incomplete guards, boundary violations | Significant duplication, wrong file location |
| P3 NICE-TO-HAVE | Minor edge cases, defensive improvements | Naming nits, comment removal, style consistency |

## Spawn Parallel Review Agents

Launch all 6 review agents in parallel with the diff context. Each agent should reference the issue patterns taxonomy.

1. **type-safety** - TYPE_SAFETY_IMPROVEMENT, UNNECESSARY_CAST, NULL_HANDLING, RUNTIME_VALIDATION, SCHEMA_VALIDATION_MISSING, TYPE_CHOICE_QUESTION
2. **patterns-utilities** - BETTER_IMPLEMENTATION_APPROACH, EXISTING_UTILITY_AVAILABLE, CODE_DUPLICATION, MAKE_SELF_DOCUMENTING, NAMING_CLARITY, ERROR_HANDLING_NEEDED, NAMING_CONVENTION, USE_CONSTANT, FRAGILE_IMPLEMENTATION, IMPORT_STYLE_CONSISTENCY, MAGIC_NUMBER, ERROR_MESSAGE_CLARITY, LIMIT_BOUNDARY_CONCERN, VERIFY_DOCUMENTATION_ACCURACY
3. **performance-database** - DATABASE_INDEX_MISSING, PARALLELIZATION_OPPORTUNITY, PERFORMANCE_OPTIMIZATION, DATABASE_QUERY_OPTIMIZATION
4. **architecture** - ARCHITECTURAL_CONCERN, FILE_ORGANIZATION, WRONG_LOCATION, BREAKING_CHANGE_CONCERN, TESTING_VERIFICATION, CONFIGURATION_VERIFICATION, SCOPE_CREEP, SCOPE_REDUCTION, ENVIRONMENT_CONFIGURATION
5. **security** - INJECTION_VULNERABILITY, AUTHENTICATION_BYPASS, AUTHORIZATION_BYPASS, SENSITIVE_DATA_EXPOSURE, XSS_VULNERABILITY, SECURITY_PERMISSIONS, RATE_LIMITING_NEEDED
6. **simplicity** - REDUNDANT_LOGIC, REMOVE_UNUSED_CODE, CONSOLIDATE_LOGIC, NIT_MINOR_ISSUE, EXTRACT_TO_HELPER, FUNCTION_SIGNATURE_REFACTOR, REMOVE_DEBUG_CODE, REMOVE_COMMENT, AI_GENERATED_CODE_CONCERN

```text
role: agent:type-safety
task: Review {diff} using the type-safety taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

```text
role: agent:patterns-utilities
task: Review {diff} using the patterns-utilities taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

```text
role: agent:performance-database
task: Review {diff} using the performance-database taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

```text
role: agent:architecture
task: Review {diff} using the architecture taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

```text
role: agent:security
task: Review {diff} using the security taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

```text
role: agent:simplicity
task: Review {diff} using the simplicity taxonomy above, recalled context, new concepts, and pre-agent findings. Return only the required finding format with file:line evidence.
mode: parallel
```

**Include recalled context and pre-agent findings in agent prompts:**

When spawning agents, include any relevant memories from Context Recall AND findings from Pre-Agent Analysis:

```markdown
**Past Learnings (from team memory):**
- {learning 1 relevant to this agent's domain}
- {learning 2}

Watch for these patterns based on past issues.

**New Concepts Introduced (from pre-agent analysis):**
- {concept 1} - Scrutinize naming, necessity, and clarity
- {concept 2}

**Pre-Agent Findings (already flagged):**
- {REVERT_UNRELATED_CHANGES findings, if any}
- {BREAKING_CHANGE_CONCERN findings, if any}
```

This ensures agents are informed by past mistakes AND have explicit targets to scrutinize. For example, if pre-agent analysis found a new `target_agent_id` concept, the patterns-utilities agent should verify the naming is clear and consistent.

Each reviewer returns findings in this format:

```markdown
### [PATTERN_NAME] - Severity: P1/P2/P3 - Tier: 1/2

**Location:** `file:line`

**Issue:** What's wrong

**Why:** Link to pattern from issue-patterns.md

**Fix:**
// Before
problematic code

// After
fixed code
```

## Architectural Zoom-Out

Before verifying individual findings, read the full diff holistically to assess whether the PR's fundamental approach is sound. Use the `ARCHITECTURAL_DIRECTION` pattern from issue-patterns.md as a rubric.

**Evaluate against signal patterns:**
- Is this building something new when an existing service/module should be extended?
- Is logic in the wrong layer?
- Is this creating a new abstraction when the work belongs in an existing one?
- Is this solving a symptom instead of the root cause?
- Is this reimplementing a flow that already exists?

**If the approach is sound:** Note "Architectural direction: sound" and proceed to Finding Verification.

**If concerns exist:** Create a non-actionable `Architectural Direction` observation in the review document. This is informational only — flagging for the developer to consider. It does not have a severity, does not enter the fix loop, and is not a P1/P2/P3 finding.

Differentiate from related patterns:
- Individual files in wrong location → WRONG_LOCATION (reviewable finding)
- Tight coupling between modules → ARCHITECTURAL_CONCERN (reviewable finding)
- Code that could be structured better → FILE_ORGANIZATION (reviewable finding)
- This pattern is about the entire PR direction being wrong, not individual code issues

**High bar:** Most PRs have a sound approach with imperfect execution. Only flag when fixing individual issues would be wasted effort because the foundation needs rethinking.

## Finding Verification (Critical)

**Agents are not oracles.** Their findings are hypotheses that must be verified before presenting to the user.

For each finding from the review agents:

1. **Check factual accuracy**: Does the claim hold up?
   - "Utility exists at X" → Actually read the file, confirm it exists and does what's claimed
   - "Pattern violation" → Verify the pattern actually applies to this context
   - "Security issue" → Confirm the vulnerability is real and exploitable

2. **Check scope relevance**: Is this finding in-scope for the current review?
   - A real issue but unrelated to this change → Dismiss (note for existing code section)
   - A stylistic preference vs actual problem → Dismiss
   - Pre-existing issue not introduced by this change → Move to "Existing Code Issues"

3. **Check blast radius**: For each verified finding, assess whether the fix would touch files outside the current diff.
   - If the fix stays within the diff's file footprint → No tag needed
   - If the fix would require changes to files not in the diff → Tag as `SCOPE_INCREASE` with a list of files the fix would expand to
   - The tag is metadata, not priority — the finding keeps its original severity

4. **Classify the finding**:
   - **VERIFIED**: Factually correct and in-scope, fix stays within diff → Include in review
   - **VERIFIED + SCOPE_INCREASE**: Factually correct and in-scope, but fix expands to files outside the diff → Include in review with scope tag
   - **DISMISSED**: False positive or out of scope → Document rationale, don't include in main review

**Only VERIFIED findings are presented to the user for action.**

Document verification decisions internally:
```markdown
### Finding: {original finding summary}
**Agent:** {type-safety|patterns-utilities|etc.}
**Original Severity:** P1/P2/P3
**Verification Status:** VERIFIED | VERIFIED + SCOPE_INCREASE | DISMISSED
**Blast Radius:** {files the fix would expand to, or "within diff"}
**Rationale:** {why this was verified or dismissed}
**Action:** {what will be done, or "none - dismissed"}
```

This verification step prevents wasting user time on false positives and ensures all presented findings are actionable.

Findings targeting different files can be verified in parallel. When multiple findings exist, read files for independent findings simultaneously using parallel tool calls before classifying.

## Classify Findings by Scope

Cross-reference each finding with the diff to classify scope:

- **PR Change** - Issue is in code added/modified by this change (appears in diff with `+` prefix)
- **Existing Code** - Issue predates this change (context lines, surrounding code)

PR authors must address issues in their changes. Existing code issues are informational.

## Generate Review Document

Create `loop-engineering/review/{DD-MM-YYYY}-{feature-name}.md`:

```markdown
# Code Review: {Feature Name}

## Summary
- P1 Issues: {count} ({tier1_count} correctness, {tier2_count} cleanliness)
- P2 Issues: {count}
- P3 Issues: {count}
- Scope-increasing fixes: {count}

## Architectural Direction
{Only include this section if the zoom-out step flagged concerns. Informational only — not actionable by the review system.}

{Description of the directional concern and what the developer should consider.}

## P1 - Critical Issues (Tier 1 first, then Tier 2)

### Correctness Issues
{List all P1 Tier 1 findings}
{Findings with SCOPE_INCREASE get an inline `SCOPE_INCREASE` marker and a "Fix expands to:" line}

### Cleanliness Issues
{List all P1 Tier 2 findings}

## P2 - Important Issues

### Correctness Issues
{List all P2 Tier 1 findings}

### Cleanliness Issues
{List all P2 Tier 2 findings}

## P3 - Nice-to-Have

{List all P3 findings}

## Existing Code Issues (Informational)
Issues found in code that predates this change. Not blocking, but worth noting:
{List with file:line and brief description}

## What's Good
{Positive observations - following patterns, good structure, etc.}

## Fix Implementation Principles
- **Minimize blast radius**: Fixes must stay within the PR's existing file footprint wherever possible. Do not refactor surrounding code, add new abstractions, or touch unrelated files.
- **Reuse existing utilities**: Before writing new code for a fix, search for existing utilities, helpers, and patterns in the codebase. Prefer calling what already exists over creating something new.
- **No scope creep during fixes**: A fix addresses the finding and nothing else. Do not improve adjacent code, add extra error handling, or "clean up while we're here."

## Review Status
- [ ] All P1s resolved
- [ ] P2s addressed or explicitly deferred
- [ ] P3s documented for future consideration
```

## Fix Loop

### For P1 Issues (Ordered by Tier)

Fix Tier 1 (correctness) P1 issues first, then Tier 2 (cleanliness) P1 issues:

1. Present each P1 issue to user, starting with Tier 1. For P1s with `SCOPE_INCREASE`, add a note: "Fixing this will touch files beyond the current diff: {list of files}". P1s still get fixed regardless of scope increase.
2. **Research the correct fix** - If unsure about best practice, query Context7:
   ```
   mcp__plugin_context7_context7__resolve-library-id
     query: "<issue type, e.g., 'secure password hashing'>"
     libraryName: "<relevant framework>"

   mcp__plugin_context7_context7__query-docs
     libraryId: "<from above>"
     query: "<specific fix pattern>"
   ```
3. **If fix approach is unclear after research:** Trigger interview loop.

   Read the interview-workflow reference bundled with the `unit-loop` skill for question patterns.

   Present to user via the harness's structured question tool (e.g. AskUserQuestion on Claude):
   - **Clarify fix approach** - Answer questions about expected behavior
   - **Skip this issue** - Defer to manual fix later
   - **Accept current implementation** - Issue is acceptable as-is

   After interview, dispatch `agent:gap-detector` again to validate the fix approach before implementing.

4. Implement the fix
5. Create new checkpoint: `checkpoint({n}+1): fix {issue}`
6. Re-run affected review agents on fixed code
7. Repeat until no P1s remain

### For P2/P3 Issues

After P1s are resolved, present remaining issues. Group scope-increasing findings separately within each priority:

```
P1 issues resolved.

Remaining issues:

**P2 - IMPORTANT (Correctness):**
1. {issue description}

**P2 - IMPORTANT (Cleanliness):**
1. {issue description}

**P2 - Scope-Increasing** `SCOPE_INCREASE`:
1. {issue description} → Fix expands to: {file list}

**P3 - NICE-TO-HAVE:**
1. {issue description}

What would you like to do?
```

Use the harness's structured question tool (e.g. AskUserQuestion on Claude):
- **Fix P2s now** - Implement P2 fixes
- **Fix P2s (skip scope-increasing)** - Fix P2s but defer all scope-expanding fixes
- **Defer P2s** - Document and continue
- **Fix specific issues** - Select which to fix
- **Continue to PR** - Accept current state

## Re-Review Protocol

After fixes, re-run only the affected review agents:

- If type issue fixed -> dispatch `agent:type-safety` again
- If pattern issue fixed -> dispatch `agent:patterns-utilities` again
- If performance issue fixed -> dispatch `agent:performance-database` again
- If architecture issue fixed -> dispatch `agent:architecture` again
- If security issue fixed -> dispatch `agent:security` again
- If simplicity issue fixed -> dispatch `agent:simplicity` again

Continue until review is clean or user accepts state.

## Completion

When review is complete:

```
Code review complete.

**Final Status:**
- P1: 0 remaining (all fixed)
- P2: {X} fixed, {Y} deferred
- P3: {Z} noted for future

Patterns found: {list of PATTERN_NAMEs}

Review document: loop-engineering/review/{date}-{feature}.md

Ready for PR creation. The /compound-learnings phase will run automatically to capture learnings.
```

## Trigger Compound Phase

After review completion, automatically invoke `/compound-learnings` to capture learnings before creating PR.

## Quick Pattern Reference

**Most common issues to watch for:**
1. BETTER_IMPLEMENTATION_APPROACH (18%) - Search first
2. TYPE_SAFETY_IMPROVEMENT (12%) - No casting
3. EXISTING_UTILITY_AVAILABLE (10%) - Check utilities
4. CODE_DUPLICATION (8%) - Look for existing
5. NULL_HANDLING (6%) - Use null, not ""

**Always P1 (Security):**
- INJECTION_VULNERABILITY
- AUTHENTICATION_BYPASS
- AUTHORIZATION_BYPASS
- XSS_VULNERABILITY
