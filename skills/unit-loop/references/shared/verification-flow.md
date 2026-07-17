# Verification Flow

This document is the single source of truth for verification-related protocols in Unit Work, including which subagents to use, confidence calculation, and self-correcting review.

## Which Verification Subagent to Use

Load `agent-dispatch.md` before dispatching verification roles.

**When changes span multiple categories, launch all applicable logical roles in one capacity-aware parallel batch.**

```text
role: agent:test-runner
task: Run the tests selected for {change type}. Return verbatim pass/fail counts and file:line diagnostics; do not mutate production data.
mode: parallel
```

| Change Type | Subagents | Safety Flags |
|-------------|-----------|--------------|
| Test files | `agent:test-runner` | None |
| API endpoints | `agent:test-runner` + `agent:api-prober` + available browser automation | API Prober: read-only without permission, mutating requires user confirmation |
| UI components | `agent:test-runner` + available browser automation | Flag layout changes for human review |
| Database schema/migrations | `agent:test-runner` only | NEVER run migrations automatically; Flag for human verification |
| Configuration/environment | No automated verification | Document changes; Flag for human review |

## Browser-Automation for All Change Types

Browser-automation is NOT limited to UI changes. Use it when:
- Verifying API endpoints through the app UI
- Testing end-to-end flows that involve backend changes
- Validating that frontend correctly displays data from backend
- Any change that affects user-visible behavior

**Setup for backend testing:**
1. Determine the frontend URL to test against (ask the user, or check project configuration for staging/development URLs)
2. Ensure the local backend is running
3. Point the frontend at the local backend using the project's own mechanism (env var, dev-server proxy, or config setting — the project adapter names it)

## Confidence Heuristic (optional — standalone /implement runs only)

**This heuristic is never a gate the unit-loop uses.** Under unit-loop, GREEN/RED decisions come from the checkable artifacts each stage brief names — never from a numeric confidence score. A project may optionally use a rough confidence heuristic in standalone `/implement` runs to decide when to pause for human review: high confidence (fully verified, no untested edge cases, no risky surface) → continue automatically; anything less → pause and present what was verified, what needs human judgment, and specific items to check.

## Self-Correcting Review (Fix Checkpoints Only)

**This section ONLY applies to fix checkpoints** — commits that fix an issue found during verification or review of an earlier checkpoint. Skip this for regular unit checkpoints.

When you create a fix checkpoint, the fix itself may introduce new issues. Before continuing, assess whether the fix needs re-review.

### Risk Assessment (Fast - No Agent Spawning)

Analyze the fix diff to determine review intensity:

**No Review Needed** - ALL conditions must be true:
- <=3 lines changed
- File matches low-risk patterns: `*.test.*, *.spec.*, *.md, *.json, *.yaml, *.yml, *.config.*`
- Pure additions (no deletions)

**Light Review** - ANY condition true:
- 4-30 lines changed
- Single file in `src/` or main code directory
- Changes with <5 deletions

**Full Review** - ANY condition true:
- >30 lines changed
- >3 files modified
- >10 lines deleted
- Security-related file patterns (auth, crypto, permissions)

### Selective Agent Invocation

Based on the type of issue being fixed, spawn only the relevant review agent(s):

| Original Issue Type | Re-Review Agent |
|---------------------|-----------------|
| Type safety issue | `agent:type-safety` |
| Pattern/utility issue | `agent:patterns-utilities` |
| Performance issue | `agent:performance-database` |
| Architecture issue | `agent:architecture` |
| Security issue | `agent:security` |
| Simplicity issue | `agent:simplicity` |

**For mixed fix types** (fix addresses multiple categories): Spawn ALL relevant agents.

**Scope-guard for review agents:** When spawning agents to review a fix, include this context:

> "You are reviewing a FIX to a specific issue. DO NOT suggest additional refactoring beyond the fix. DO NOT expand scope. Only verify the fix addresses the original issue without introducing new problems."

### Cycle Handling

**If re-review finds no new issues:** Continue to next unit/step.

**If re-review finds new issues:** Present to user via AskUserQuestion:
- **Fix the new issue** - Implement fix and create another fix checkpoint (triggers another cycle)
- **Accept and continue** - Break cycle, proceed with current state
- **Revert fix** - Execute `git reset --soft HEAD~1` to unstage, let user review

**Hard limit: 3 cycles maximum.** After 3 fix-review cycles on the same original issue:

```
Fix-review cycle limit reached (3 iterations).

**Attempts made:**
1. {first fix attempt and result}
2. {second fix attempt and result}
3. {third fix attempt and result}

**Recommendation:** {continue manually | accept current state | revert to pre-fix}

What would you like to do?
```

Use AskUserQuestion with options:
- **Continue manually** - User takes over fixing
- **Accept current state** - Proceed with existing fixes
- **Revert all fixes** - Execute `git reset --soft HEAD~{n}` to revert fix attempts
