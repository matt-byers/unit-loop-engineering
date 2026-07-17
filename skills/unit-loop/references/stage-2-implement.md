# Stage 2 — Implement

Use Claude Code's built-in `general-purpose` subagent for the unit. This is a disposable runtime subagent, not a repository-owned agent file.

Before dispatching, select every stack touched by the unit using `references/stack-selection.md`. A mixed frontend/backend unit may use more than one stack.

```text
role: general-purpose
task: Invoke the project `/implement` skill for one approved unit. If skill invocation is unavailable inside the subagent, read and follow `.claude/skills/implement/SKILL.md` directly.

Canonical spec: {spec_path}
Unit: {unit name}

Relevant project architecture documents: {resolved project docs}
Selected bundled stack references: {selected stack docs}
Apply skills from the unit, unchanged: {unit Apply skills list}
Relevant prior-retro learnings: {learnings from Step 1}

Do not commit. Return the artifact required by `/implement`.
mode: sequential
```

**GREEN:** the declared implementation exists within scope and focused checks support advancing to Stage 3.

**RED:** implementation or a focused check fails. Retry once with the concrete error and changed-file evidence.

**BLOCKED:** the second attempt fails, a required external dependency is unavailable, or implementation requires a decision outside the approved unit.
