# Test Tooling Discovery

How to find what test and verification tooling a repository already uses, before writing new tests or mapping `unit-loop.adapter.yaml` (see `project-adapter.md`). This is deliberately stack-agnostic — it applies the same whether the repo is a Vue/Nuxt frontend, a Swift app, or a Python service. Use it during `/spec-plan`'s "Inspect before asking" step and before Stage 1 TDD writes a unit's first test.

## Why discover instead of assume

A stack pack's docs describe how tests *should* work in general; they never name a concrete tool, because the project may already have chosen a different one than the stack's typical default. Assuming a toolchain instead of confirming it produces tests that don't run through the project's actual gate, or a second competing test setup alongside the one already in use. Confirm before writing.

## Signals, cheapest first

1. **Repository manuals.** `CLAUDE.md`, `AGENTS.md`, or the README's contributing/testing section often name the exact commands directly — read these first.
2. **Package manifest scripts.** `package.json` `scripts` (`test`, `test:unit`, `test:e2e`, `test:watch`, `lint`, `typecheck`, `build`), or the equivalent for the ecosystem (`pyproject.toml` `[tool.poetry.scripts]`, a `Makefile`, `Taskfile.yml`, `justfile`). These are usually the canonical entry points other tooling (CI, this skillset's adapter) should reuse rather than re-derive.
3. **CI workflow files.** `.github/workflows/*.yml` (or equivalent CI config) show the commands actually exercised on every change — treat these as ground truth over a possibly stale README when they disagree.
4. **Config files present in the repo root or a package's root** — their mere presence identifies the tool in use, no need to guess:
   - Unit/component runner: `vitest.config.*`, `jest.config.*`, `karma.conf.*`, `.mocharc*`, `pytest.ini` / `pyproject.toml` `[tool.pytest...]`, a `Package.swift` test target.
   - Browser/e2e runner: `playwright.config.*`, `cypress.config.*`, a `cypress/`, `e2e/`, or `tests/e2e/` directory. Treat whichever is already configured as canonical — do not introduce a second browser-testing tool to satisfy a new gate.
   - Lint/format/typecheck: `.eslintrc*` / `eslint.config.*`, `.prettierrc*`, `tsconfig.json`, `ruff.toml` / `[tool.ruff]`, `mypy.ini`.
5. **Existing test files' own conventions.** Where they live (co-located `*.spec.ts` next to source, a top-level `tests/`, `__tests__/`, or a per-target test directory) and how they're named — new tests follow the existing layout, never a parallel one, even if a different layout is more familiar.
6. **Lockfile / package manager.** `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock` determines the command prefix (`npm run`, `pnpm`, `yarn`) — a command that's right in spelling but wrong in package-manager prefix can silently resolve to the wrong binary or fail in a workspace.
7. **Monorepo/workspace nuances.** A root-level script may proxy to per-package scripts (Turborepo, Nx, npm/pnpm workspaces) — confirm whether the relevant command must run from the repo root or from the specific package/app directory, and whether it needs a workspace filter flag.

## From discovery to adapter mapping

Once the concrete commands are known, map them to the generic slots in `project-adapter.md`'s table (`test-scoped`, `test-full`, `lint`, `typecheck`, `build`, `ui`, `api-smoke`, etc.) inside the project's `unit-loop.adapter.yaml`. This doc only covers finding the commands — writing the adapter file itself follows `project-adapter.md`'s format and the project's own confirmation, not this doc.

## When nothing exists

A repository (or a newly-scaffolded frontend/backend split) with no test tooling yet is a genuine gap, not something to silently fill in. Report it plainly — which slot has no discoverable command — and let the user pick a tool rather than defaulting to whatever a stack pack happens to mention as an example. Introducing a test framework is a project decision, not an autonomous one.

## Anti-patterns

- Assuming a stack's typical default tool (e.g. Vitest for a Vue project) without checking for a config file or script that says otherwise.
- Picking a `package.json` script by name alone (`test`) without opening it — some `test` scripts also seed data, run migrations, or start a server as a side effect, which changes what "run tests" actually does to the environment.
- Introducing a second browser-automation tool because it's more familiar, when the repo already has one configured.
- Treating a stale README's documented command as more authoritative than what CI actually runs.
