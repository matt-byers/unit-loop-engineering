---
name: review-standards
description: "This skill should be used when reviewing code or running /multi-review. It contains 50 issue patterns with severity tiers, team standards to enforce, and implementation checklists shared by the project's review agents (architecture, security, type-safety, patterns-utilities, performance-database, simplicity)."
---

# Review Standards

This skill contains the review taxonomy, team standards, and implementation checklists used by the project's review agents.

## Contents

- [Issue Patterns](./references/issue-patterns.md) - 50 distinct patterns with detection criteria and fixes
- [Review Standards](./references/review-standards.md) - Language-agnostic best practices
- [Checklists](./references/checklists.md) - Before, during, and after implementation

## Severity Tiers

Issues are categorized into two tiers:

**Tier 1 - Correctness** (Always Higher Priority)
- Security vulnerabilities
- Architecture problems
- Implementation bugs
- Type safety violations
- Functionality gaps

**Tier 2 - Cleanliness** (Lower Priority)
- Naming clarity
- File organization
- Code duplication (when not causing bugs)
- Comment quality
- Import/style consistency

At the same P-level, Tier 1 issues should be addressed before Tier 2 issues.

## Severity-Tier Mapping

Stack review skills and `multi-review` share one severity vocabulary. Reviewers that emit BLOCKING/HIGH/MEDIUM/LOW and reviewers that emit P1/P2/P3 map onto each other as:

| Reviewer severity | P-level | Meaning |
|---|---|---|
| BLOCKING | P1 | Must be fixed before merge — RED gate |
| HIGH | P2 | Should be fixed before merge |
| MEDIUM / LOW | P3 | Cleanup; address when convenient |

Use this table to normalise findings across review agents before ranking them.

## Plan Convergence Checklist

Stage 1 plan-review self-approves only when **every** item below is TRUE. This is the machine-readable gate — record its state in the spec's `## Plan Review` section:

- [ ] **No verified P1/P2 findings remain.** Every P1/P2 finding raised by a plan-review agent has been resolved or refuted (Tier-1 issues count here per the Severity-Tier Mapping above; P3 findings do not block convergence).
- [ ] **All plan-review agents reported.** Each expected plan-review agent ran to completion and returned findings (none errored or were skipped).

Both TRUE → converged, self-approve. Any FALSE → not converged: revise and re-review (escalate to the user after 5 rounds, or when a verified ambiguity needs a product/design decision).

## Top 5 Patterns by Frequency

1. **BETTER_IMPLEMENTATION_APPROACH** (18%) - Search first, leverage framework features
2. **TYPE_SAFETY_IMPROVEMENT** (12%) - No casting, complete type guards
3. **EXISTING_UTILITY_AVAILABLE** (10%) - Search codebase before implementing
4. **CODE_DUPLICATION** (8%) - Check for existing implementations
5. **NULL_HANDLING** (6%) - Use null, not empty strings

## Always P1 (Critical)

- Any injection vulnerability
- Authentication/authorization bypass
- XSS in user content
- Security boundary violations
- [ ] **Verify model-capability limits from current docs before flagging as BLOCKING.** Before raising a context window size, output-token ceiling, or any other model-capability limit as a security violation, look it up in Context7 or Anthropic docs — model specs change and training data may be stale.

## Zero-Tolerance Items

These should never appear in PRs:
- Type casting to access properties (`as SomeType`)
- Barrel files (index.ts re-exports)
- Debug code (console.log, print)
- Services that swallow errors
- Empty strings as null fallbacks

## Usage

When conducting code review, reference the detailed patterns in [issue-patterns.md](./references/issue-patterns.md) for detection criteria and fix guidance.

Before implementing features, run through the checklists in [checklists.md](./references/checklists.md).
