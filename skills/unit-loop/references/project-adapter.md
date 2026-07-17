# Project Adapter Config

The consuming project maps unit-loop's generic gate slots to concrete commands in `unit-loop.adapter.yaml` at the project's repository root. Stack packs declare which slots they use; the project supplies the commands.

## Format

```yaml
stacks:
  - swift
commands:
  test-scoped: "<command template with a scope placeholder>"
  test-full: "<command>"
gate_file_patterns:
  - '(^|/)Tests/Snapshots/'
```

- `stacks` optionally declares project stacks or pins a default for ambiguous units.
- `commands` maps generic slots to concrete project-owned commands.
- `gate_file_patterns` identifies snapshot baselines, performance baselines, eval scenarios, and other verification artifacts for the Stage 4 audit and optional gate-file hook.

## Slots

| Slot | Maps to |
|---|---|
| `test-scoped` | Run only one unit's test classes or files |
| `test-full` | Run the full deterministic regression suite |
| `lint` | Lint the changed surface |
| `typecheck` | Run static type checks |
| `build` | Build the product target |
| `build-for-testing` | Compile product and test targets without running tests |
| `format` | Check formatting |
| `snapshot` | Run visual regression tests |
| `ui` | Run UI automation or driven-app verification |
| `api-smoke` | Probe changed endpoints |
| `live-run` | Run the live service and capture evidence |
| `perf` | Compare performance against baselines |

## Missing commands

- An unmapped required slot blocks that gate and reports the stack, slot, and expected mapping.
- An unmapped optional slot is skipped and recorded in the unit result.

## Worked example

```yaml
stacks:
  - fastapi
commands:
  test-scoped: ".venv/bin/pytest -q {test_path}"
  test-full: ".venv/bin/pytest -q"
  lint: ".venv/bin/ruff check ."
  typecheck: ".venv/bin/mypy src"
  live-run: "scripts/live-run.sh"
gate_file_patterns:
  - '(^|/)evals/scenarios/'
```

Here `api-smoke` is unmapped and optional for the FastAPI pack, so units skip it and record the skip.
