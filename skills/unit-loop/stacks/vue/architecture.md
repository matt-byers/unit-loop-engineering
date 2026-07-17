# Vue Stack — Architecture Guidance

Generalized durable patterns for Vue units. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Core rules

- Prefer computed properties over watchers for anything derivable from existing reactive state — watchers are for side effects that synchronize with external systems.
- Cross-cutting state lives in the project's store (Pinia or equivalent); component state stays local until more than one subtree needs it.
- Props flow down, events flow up: children never mutate props or reach into parent state; use emits with declared payloads.
- Composables own reusable stateful logic; a second copy of an existing composable or utility is a planning miss — find the first one.
- Follow the project's established single-file-component conventions (script setup style, ordering, naming) rather than mixing styles.

## Patterns that recur in Vue units

- **Typed component contracts:** declare prop and emit types so typecheck guards the component boundary; a bare untyped prop pushes the failure to runtime.
- **Reactivity edges:** destructuring reactive objects severs reactivity — pass refs/getters through composable boundaries deliberately.
- **Stable identity for list rendering:** keys come from data identity, never array index, whenever items reorder or mutate.
- **Error capture at deliberate boundaries:** handle errors where a meaningful fallback exists, with a per-region fallback rather than one global catch-all.
- **Accessibility as a contract:** interactive elements are real interactive elements with names/labels tests can select.

## Anti-patterns

- Watcher chains re-deriving state a computed could express.
- Mutating a prop, or mirroring a prop into local state to "cache" it.
- Global event buses for what should be props/emits or the store.
