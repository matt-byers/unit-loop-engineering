# Checkpointing Reference

This document is the single source of truth for checkpoint-related protocols in Unit Work.

## Checkpoint Commit Format

Commit subjects are **plain-language descriptions of what changed** — written for a human reading `git log`, not for the loop. No `checkpoint(N):` prefix, no `Confidence:` trailer, no stage/gate status in the message (the unit-loop's Stage 7 brief owns this rule and explicitly bans loop-status subjects; it wins). Keep the project's existing convention prefix if it has one, but the words after it must describe the change.

```
{subject: what changed, in plain language}

{body: what the change does and why, for a human reading git log later}
```

Example: `handle null email addresses in signup validation`

## When to Checkpoint

See [decision-tree.md](./decision-tree.md) for the shared implementation decision flow.

**Summary:** A checkpoint is required after ANY code change:
- Completing a unit from the spec
- Fixing an issue found during verification
- Implementing user feedback or corrections
- Any code change, no matter how small

**There is no "minor change" exemption.**

## Verification Record

**Under unit-loop, the spec file is the only durable verification record — no parallel ledger or per-checkpoint verification document is created.** Smoke-test status, manual-check status, and verification evidence live in the owning spec (see the unit-loop Stage 7/8 brief and `/human-verify`).

A per-checkpoint verification document (using the template at [templates/verify.md](./templates/verify.md)) applies **only** when a project explicitly opts into standalone `/implement` checkpoint documents outside the unit-loop.

**CRITICAL: Minimize human review.** If you can verify something with 100% certainty (grep, read, test output), verify it yourself and record it as AI-verified. Only surface items for human review that genuinely require human judgment.

## Self-Correcting Review (Fix Checkpoints Only)

See [verification-flow.md](./verification-flow.md#self-correcting-review-fix-checkpoints-only) for the complete self-correcting review protocol including:
- Risk Assessment (when to skip, light review, or full review)
- Selective Agent Invocation (which agents to spawn based on issue type)
- Cycle Handling (max 3 cycles, user options when limit reached)

## Confidence Heuristic

See [verification-flow.md](./verification-flow.md) for the optional confidence heuristic (standalone `/implement` runs only — never a unit-loop gate).
