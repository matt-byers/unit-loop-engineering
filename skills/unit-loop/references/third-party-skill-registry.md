# Third-Party Skill Registry

Every workflow phase works with only this skillset installed. Additional skills are optional recommendations: use one when available; otherwise apply the bundled fallback below and continue. Their absence is never a load failure and must never block planning, implementation, review, or verification.

## First-party skills included in this repository

- `/unit-loop`
- `/unit-loop-setup`
- `/spec-plan`
- `/implement`
- `/multi-review`
- `/review-standards`
- `/compound-learnings`
- `/human-verify`

## Recommended external skills

No setup is required. The fallback is part of this skillset.

- `/python-testing-patterns`: follow the selected stack verification doc and existing test conventions.
- `/snapshot-test-setup`: use the project's existing snapshot setup; otherwise use live verification and record the optional snapshot gate as skipped.
- `/tdd-refactor-guard`: confirm behavior coverage using Stage 1 before refactoring.
- `/coding-best-practices`: apply the Swift stack architecture doc and native review agents.
- `/concurrency-patterns`: apply existing project isolation conventions and the Swift architecture checklist.
- `/swiftui-debugging`: use the Swift verification doc's live-session diagnostics.
- `/navigation-patterns`: follow the project's existing navigation feature.
- `/ui-review`: apply the bundled accessibility and UI review checklist.
- `/run-simulator`: use a project-owned UI command or `/human-verify` for irreducibly visual checks.
- `/run-device`: use the available simulator path and record any physical-device limitation.
- `/profiling`: use a project-owned performance gate or record the optional gate as skipped.
- `/fastapi-templates`: follow the FastAPI architecture doc and existing router/service layout.
- `/networking-layer`: follow the project's existing service-client boundary.
- `/error-handling-patterns`: apply the selected stack architecture doc's error rules.
- `/error-monitoring`: follow an existing monitoring boundary or implement a provider-neutral interface from bundled architecture guidance.
- `/langgraph-docs`: follow existing graph contracts and consult official docs for version-sensitive details.
- `/langchain-architecture`: follow existing agent/tool boundaries and the project's architecture docs.
- `/skill-creator`: use existing bundled skills as the format contract.
