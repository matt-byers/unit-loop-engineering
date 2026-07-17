# Stage 7 — Mark Complete · Stage 8 — Per-Unit Retro · Feature Complete

## Stage 7 — Mark Complete

**Return artifact (mandatory gate):** the commit SHA and the FR/NFR checkboxes updated — both checkable on disk (`git log -1 --oneline`, the spec file). The orchestrator confirms the commit landed and the checkboxes changed before moving on.

Flip the FR/NFR items this unit satisfies from `- [ ]` to `- [x]` in the Requirements section at the top of the spec file. Do this for every FR/NFR the unit's deliverables cover — a unit may satisfy multiple. If completing this unit finishes the last outstanding FR/NFR, all boxes should be checked. Then commit:

```bash
# Edit spec to mark unit complete, then commit THIS UNIT's files (+ the spec checkbox).
# Stage the unit's files explicitly — do NOT `git add -A`. Unrelated changes that
# accumulated during the session (harness/skill edits, other specs) belong in their
# own commit, so the unit's checkpoint stays scoped to the unit.
git add {unit files} {spec file}
git commit -m "$(cat <<'EOF'
{subject: what changed, in plain language}

{body: what the change does and why, for a human reading git log later}

Co-Authored-By: {assistant identity}
EOF
)"
```

Use the harness's own co-author convention for the `Co-Authored-By` trailer (the harness documents the exact identity and email to use).

If a unit file also contains unrelated unstaged WIP from another session, do not use `git commit -- <that-file>` after partially staging your hunk. Git can commit the pathspec's working-tree content, not only the staged hunk, which silently captures the other session's edits. Instead, first make the same-file WIP explicit: either get a clean same-file boundary before committing, or create a corrective scoped commit and immediately restore the unrelated content as unstaged WIP. Verify both `git diff --cached -- <file>` and `git diff -- <file>` before the commit.

**Write commit messages for a human reading `git log`, not for the loop.** The subject says *what changed* in plain language — `item_remove + item_reorder tools`, not `checkpoint(B1)` or `All gates GREEN`. Keep the project's existing convention prefix if it has one (e.g. `phase6(B1): …`), but the words after it must describe the change, not the loop stage. The body explains what the change does and why it matters — the design decision, the bug it fixes, a caveat the next reader needs — not a restatement that tests passed (the gates are tracked elsewhere). "All gates GREEN" tells a future reader nothing about the code. A good test: could someone who never saw this loop understand the commit from its message alone?

### User smoke-test validation (surface at EVERY unit completion)

The spec's **Smoke Tests** for this unit were written at planning time as user-observable scenarios. The user wants them surfaced at completion so they can confirm the unit actually works — not just trust the green gates. Sort each scenario by how it's covered:

- **Automated & passing** — the TDD stage turned it into an automated UI/unit test (or a Self-Verification command) that passed this run. No user action needed; cite the test/command name.
- **Needs your eyes** — can't be fully automated: a dashboard state, a Console.app log line, a visual/animation check, an external service (error monitoring, the database dashboard, push delivery). Give the exact steps + expected result for the user to run.

Output this block:
```
Unit {n} — {name}: smoke tests for your validation

Automated & passing (no action needed):
  ✓ {scenario} → {test or command name}

Please verify manually:
  ☐ {scenario} — {action} → Expected: {observable outcome}

(If every scenario is automated, say so explicitly — nothing needs your manual validation for this unit.)
```

Do **not** block on the user's manual pass — surface it and continue per the chosen cadence. If they later report a manual smoke test fails, that becomes a new bug unit. Run `/human-verify {unit}` to record the result in the owning spec and convert manual checks into automation over time; the owning spec is the durable status record.

**Persist "needs your eyes" status in the owning spec.** Every smoke-test scenario must retain its steps and expected outcome and declare either `Manual check: Not required — covered by {test/check}` or `Manual check: Required — {reason}` with `Manual status: Pending` and the evidence the agent can inspect. At unit completion, reconcile these fields with what Stage 6 actually verified. Never create a parallel ledger or verification log. Later `/human-verify` runs update the same scenario to `Passed`, `Failed`, or `Blocked`; the spec is the durable record.

Report progress:
```
✓ Unit {n} — {name} complete
  Tests: {X} passed
  Review: clean
  {UX: verified / skipped}
  {Evals: passed / skipped}

Moving to Unit {n+1}...
```

---

## Stage 8 — Per-Unit Retro

**Run the skill only when the unit earned it.** A full `compound-learnings` invocation on a unit that ran straight to green is mostly cost for no signal. Decide by trigger:

- **Triggered** — the unit had a **RED→fix retry**, a **HIGH/BLOCKING review finding**, or a **Stage-H guidance-gap signal**: the `compound-learnings` skill **must be invoked** (via the Skill tool) and its result recorded as a `loop:` commit applying the patches it produced (or, if the pass genuinely finds nothing, an explicit "ran clean" line). A hand-written retro file or inline narration does NOT substitute for the skill — its harness-improvement pass is the point.
- **Not triggered** — straight to green, no retries/findings/signals: **skip the skill.** Record a one-line "Unit N — ran clean, no retro" and move on. Do not spawn the skill subagent for a clean unit.

**Return artifact (mandatory gate):** *if triggered* — proof the skill was invoked + its committed output (the `loop:` patch commit or explicit ran-clean). *If not triggered* — the one-line ran-clean note. Gate on the skill invocation when triggered, never on a file's mere existence. (The skill-required wording exists because a prior phase hand-wrote retros and silently skipped the skill, losing the patches until the user caught it. The trigger gate exists because the same phase showed a full per-clean-unit invocation is wasted.)

When triggered, after the unit is committed run the **unit-scoped** retrospective: `Invoke Skill: compound-learnings` with the unit name as the arg. This is NOT the whole-feature retro — it reflects on just this unit's loop and complements Stage H (which only fires on explicit guidance-gap signals). Ask, for this unit:

- **Plan**: did the spec unit hold up, or did reality diverge (e.g. a spec-vs-code mismatch, a deliverable that needed deferring)? → patch the spec/`/spec-plan`.
- **Speed to green**: how many RED→fix retries, and why? Did the `implement`/fix brief lack context it should have had? → patch the brief/skill.
- **What needed a human**: any smoke test surfaced as "needs your eyes" — can it become a test/agent check next time? → wire it in or note why not.
- **Repeated finding types**: a review finding that's the same *class* as a prior unit → a missing `review-standards`/stack-review rule.

Apply improvements as concrete file edits now (it never reverts/redoes the current unit). If the triggered pass genuinely finds nothing worth changing, say "ran clean" and move on — but a unit that earned a retro (retries/HIGH findings/guidance-gap) usually yields at least one patch; an empty pass on a triggered unit deserves a second look at whether the friction really left no lesson.

Then loop back to Stage 1 for the next uncompleted unit.

---

## Feature Complete

When all units are checked off, before declaring the feature done:

**Manual smoke-test gate.** Read every smoke-test scenario in the spec. Every scenario marked `Manual check: Required` must have `Manual status: Passed`. `Pending`, `Failed`, or `Blocked` prevents the feature-complete declaration: invoke `/human-verify {unit}` for pending checks, route failures through the appropriate fix loop, and surface missing external setup as `LOOP BLOCKED`. If a check is intentionally deferred, change the spec's requirements/out-of-scope boundary explicitly; do not treat an unverified requirement as complete.

**Clean warning sweep (warning-policy enforcement).** For compiled stacks, run a single CLEAN build that recompiles everything, because per-unit incremental builds cache and hide compiler warnings (see the note under Stage 3). This is the one place the multi-minute full-rebuild cost is worth paying — it's once per phase, not once per unit. Use the project's clean-build command and filter its output to compiler warnings only.
Expected: empty (zero code warnings — concurrency, deprecations, always-true casts). Any warning here is an NFR1 violation that the per-unit gates missed: fix it (a focused subagent) before the feature is marked complete. Narrate that this build is intentionally slow so it doesn't read as a hang.

Then run the **whole-feature** retro (broader than the per-unit Stage 8 passes): `Invoke Skill: compound-learnings` with the feature name. It looks across all units — plan quality overall, git churn/reverts, the human-dependency trend (before → after), and patterns only visible across the whole phase.

```
Feature complete: {feature name}

Units completed:
✓ Unit 1 — {name}
✓ Unit 2 — {name}
...

Whole-feature retro: {summary of cross-unit improvements applied}
```
