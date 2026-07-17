# Stack Selection

How unit-loop chooses which stack pack(s) under `stacks/` apply to a unit, and how a mixed unit composes their gates. This file extends `references/stage-routing.md`: stage-to-skill routing lives there and is not repeated here; a stack pack adds stack-specific detection, gates, docs, and skill recommendations on top of that routing, never a replacement for it.

## Selection inputs, in precedence order

1. **Explicit unit context.** If the spec unit names its stack in the unit description, `Apply skills`, or technology implied by its changed files, that wins.
2. **The project's adapter config.** `unit-loop.adapter.yaml` at the project's repository root may declare its stacks or pin a default for ambiguous units; see `references/project-adapter.md`.
3. **Project markers.** Only when neither input above decides, match each stack pack's `detection.markers` against the repository. Narrow multiple candidates by the unit's changed files. A `package.json` with a React or Vue dependency selects that framework pack rather than the Node fallback.

Selection is per unit, not per repository. A repository can hold several stacks while one unit usually touches one.

## Loading a selected stack

Read the stack's `stack.yaml`, then its listed architecture and verification docs when entering implementation and review. Surface its `third_party_skills` recommendations alongside the unit's `Apply skills` list. A missing recommendation uses the bundled `when_missing` guidance and never blocks the loop.

Map slots to concrete commands through the project's `unit-loop.adapter.yaml`. When a required slot has no mapped command, follow the pack's `missing_command_behavior.required_slot`; an unmapped optional slot follows `missing_command_behavior.optional_slot`.

## Mixed frontend/backend units

A unit that genuinely spans frontend and backend runs one loop pass with a composed gate set:

- Union deterministic gates, running each stack's commands against its own files.
- Union and deduplicate review routing.
- Use each stack's behavior verification for its own surface.
- Keep optional gates optional per stack.

If composition pulls in most of two full pipelines, split the unit at the contract boundary during planning.

## Recording the decision

State the selected stacks and deciding evidence when the unit starts. When stack guidance conflicts with a project architecture doc, the project doc wins; record the conflict in the unit result or retro.
