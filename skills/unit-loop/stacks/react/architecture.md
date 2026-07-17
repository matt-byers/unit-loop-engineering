# React Stack — Architecture Guidance

Generalized durable patterns for React units. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Core rules

- Server state and client state are different problems: keep fetched data in the project's data-fetching layer (query cache, loader) and reserve component state for genuinely local UI state.
- Derive, don't duplicate: values computable from props or existing state are computed during render, not mirrored into extra state that can drift.
- Effects are for synchronizing with external systems, not for transforming data or reacting to state you already own — most effect-shaped bugs are derivation problems.
- Components stay presentational where the project separates concerns; side effects and business rules live in hooks, stores, or route loaders the project already established.
- Follow the project's existing component, hook, and directory conventions rather than inventing a parallel structure.

## Patterns that recur in React units

- **Colocate state at the lowest common owner** — lift only as far as the nearest shared parent, and reach for the project's store only when the state is genuinely cross-cutting.
- **Stable identity for list rendering:** keys come from data identity, never array index, whenever items reorder or mutate.
- **Error boundaries around independently failing regions**, with a deliberate fallback per region rather than one page-level catch-all.
- **Accessibility as a contract:** interactive elements are real interactive elements (button, link, input) with names/labels tests can select; div-with-onClick fails both users and test selectors.

## Anti-patterns

- Mirroring props into state to "cache" them.
- useEffect chains that re-derive state reachable synchronously.
- A second copy of an existing hook, utility, or component variant — find the first one.
