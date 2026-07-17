# Unit Loop Stage Routing

This file is the source of truth for which skills, project agents, supporting docs, and gates are used at each unit-loop phase. `unit-loop/SKILL.md` owns the stage order; this file owns routing.

## Stage Routing

| Stage | Main skill or role | Supporting skills and docs | GREEN gate | RED | BLOCKED |
|---|---|---|---|---|---|
| Plan | `/spec-plan` | `/review-standards`, living architecture docs for touched areas, unit-type best-practice skills below, external framework docs only when project guidance is insufficient | Spec has units with `Apply skills`, dependencies, self-verification, and no verified P1/P2 review gaps | Revise and re-review verified gaps | User decision or external setup needed |
| Tests first | Stage 1 brief | Bundled TDD guidance; use `/python-testing-patterns`, `/snapshot-test-setup`, or `/tdd-refactor-guard` when available | Test files changed only; cheapest credible RED artifact is captured | Test does not fail for the intended reason | It is unclear what observable behavior to test |
| Implement | Stage 2 brief plus generic subagent | Unit `Apply skills` when installed, otherwise the registry fallback; project architecture docs; selected stack docs; prior retros | Changed files match the unit and focused verification output is present | Implementation errored or missed the contract | Missing runtime dependency, credential, environment, or incompatible unit boundaries |
| Test gate | Stage 3 brief plus `agent:test-runner` where delegated | Stack verification docs; `/run-simulator`, `/run-device`, or `/profiling` only when the unit needs them | Scoped gate passes; full regression gate passes at the required point | Any test/build/check failure | Test infrastructure is broken or required runtime is unavailable |
| Code review | Stage 4 brief plus review agents | `/multi-review`, `/review-standards`, unit `Apply skills` verbatim, stack review skill where applicable | No BLOCKING/HIGH findings | HIGH finding gets one scoped fix and reviewer rerun | BLOCKING finding or repeat HIGH |
| Behavior verify | Stage 5 brief | Frontend/UI: the stack's UI/snapshot verification gate, `/run-simulator`, `/run-device`, `/ui-review`, `/human-verify` when needed. Backend: live-run transcript, API smoke | Behavior artifact proves the changed path works | Observable regression | Simulator/device/model/API key unavailable |
| Eval gate | Stage 6 brief | the project's eval harness skill and eval docs, tracing-service docs when the project uses one | Held-in and required held-out scores meet baseline | Score regression | Eval service, scenarios, or credentials unavailable |
| Mark complete | Stage 7 brief | Git, checkpointing docs | Commit SHA recorded and spec checkbox flipped | Commit or verification mismatch | Merge/conflict/user decision needed |
| Retro | Stage 8 brief | `/compound-learnings`; stack docs only if the lesson belongs there | Required loop improvement applied or explicitly skipped as clean | Patch failed validation | Lesson needs user/product decision |

## Unit-Type Routing

`/spec-plan` records the applicable best-practice skills in each unit's `Apply skills` field. `/unit-loop` must pass that list verbatim into implementation and review briefs. If a spec omits `Apply skills`, derive the list from this table before dispatching Stage 1 or Stage 2.

| Unit type | Planning and implementation skills | Verify | Review |
|---|---|---|---|
| Swift/iOS UI, SwiftUI, TCA, gestures | `/coding-best-practices`, `/concurrency-patterns`, `/swiftui-debugging`, `/navigation-patterns`, `/ui-review` | `agent:test-runner` plus the stack's UI/snapshot verification gate when behavior or visuals changed | `agent:architecture`, `agent:security`, stack review skill where available |
| Swift/iOS services, networking, dependencies | `/coding-best-practices`, `/concurrency-patterns`, `/networking-layer`, `/error-handling-patterns`, `/error-monitoring` | `agent:test-runner`; API/client smoke when applicable | `agent:architecture`, `agent:security`, stack review skill where available |
| FastAPI or Python backend | `/fastapi-templates`, `/python-testing-patterns`, `/error-handling-patterns`, `/error-monitoring` | `agent:test-runner`, `agent:api-prober` for endpoints | `agent:architecture`, `agent:security`, `agent:type-safety`, `agent:patterns-utilities`, `agent:performance-database`, `agent:simplicity` as tier/surface requires |
| LangGraph, LangChain, agent tools, prompts | `/langgraph-docs`, `/langchain-architecture`, `/python-testing-patterns`, `/error-handling-patterns`, tracing skill when the project uses one | `agent:test-runner`, live-run transcript for observable behavior | backend review set plus `agent:patterns-utilities` for prompt/tool contract drift |
| Database migrations | the database provider's best-practice skills, `/error-handling-patterns` | migration/schema tests; never run production migrations automatically | `agent:architecture`, `agent:security`, `agent:performance-database` |
| Agent evals and eval harnesses | the project's eval harness skill, `/python-testing-patterns`, `/error-handling-patterns`, tracing skill when experiments are involved | eval fixture and comparison gates | `agent:architecture`, `agent:patterns-utilities` |
| Documentation, skill, or harness changes | `/skill-creator`, `/python-testing-patterns`, `/error-handling-patterns`, `/review-standards` | harness verifier and relevant script tests | `agent:architecture`, `agent:simplicity`, `agent:security` when hooks/config/permissions change |

## Continuity Rule

The unit's `Apply skills` list is the portable handoff from planning into the rest of the loop. Every generated implementation, review, and retry brief includes installed entries unchanged. For absent external entries, include the registry's bundled fallback instead and continue; dropping both the recommendation and fallback is a loop bug.

When stack-specific guidance conflicts with a project architecture doc, the project architecture doc wins. Record the conflict in the unit result or retro instead of silently following generic guidance.
