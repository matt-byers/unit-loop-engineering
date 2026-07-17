Loop engineering is about building autonomous systems that complete work without the need for a human to copilot the process.

This repo provides an autonomous, self-improving, TDD-driven engineering loop based on a focused subset of [UnitWork](https://github.com/ryan-relevanceai/unitwork), created by [Ryan Hay](https://github.com/ryan-relevanceai) and [Michael Zhao](https://github.com/myz96).

## How it works

This skillset is designed to run autonomously after human sign-off at the planning stage, running through implementation, test-based validation, review, and commit without needing human intervention.

The closing of the loop comes at the end of implemention, where the agent reflects on the build process to update the actual skills, agents, and reference docs to ensure each implementation compounds and improves the actual engineering loop.

The loop is instructed to keep the loop skills and supporting docs lean and consolidated to prevent context bloat over time.

NOTE: This skillset is designed to be cloned and added to a project, rather than being installed as a Claude Code plugin. This is so the actual SKILL.md and other supporting files can be tailored to the specific project setup, rather than relying on ever-growing reference docs.

## Install

Run this from the root of the project you want to add the skillset to. Existing files under `.claude/` are left unchanged.

```bash
curl -fsSL https://raw.githubusercontent.com/matt-byers/unit-loop-engineering/main/install.sh | bash && claude "/unit-loop-setup"
```

## Skillset

| Skill | Description |
|---|---|
| `/unit-loop-setup` | Connects the installed skills and agents to the project's existing architecture documents. |
| `/spec-plan` | Captures user requirements and creates a reviewable, unit-based implementation plan. Leverages plan-review agents to catch planning edge cases.<br><br>Agents:<ul><li>`gap-detector`</li><li>`feasibility-validator`</li><li>`utility-pattern-auditor`</li></ul> |
| `/unit-loop` | Runs each approved unit through tests, implementation, verification, review, commit, and retrospective stages.<br><br>Agents:<ul><li>`test-runner`</li><li>`api-prober`</li><li>`architecture`</li><li>`security`</li><li>`type-safety`</li><li>`patterns-utilities`</li><li>`performance-database`</li><li>`simplicity`</li></ul> |
| `/implement` | Implements one approved unit against its tests and project guidance. |
| `/multi-review` | Reviews a change in parallel across correctness, architecture, security, performance, and simplicity.<br><br>Agents:<ul><li>`architecture`</li><li>`security`</li><li>`type-safety`</li><li>`patterns-utilities`</li><li>`performance-database`</li><li>`simplicity`</li><li>`gap-detector`</li></ul> |
| `/review-standards` | Supplies the shared issue taxonomy and implementation review checklists. |
| `/compound-learnings` | Updates the skills, agents, and references with durable lessons from completed work. |
| `/human-verify` | Runs as a copilot during human smoke tests or issue reproduction, capturing locally generated logs alongside the user's observations. |
