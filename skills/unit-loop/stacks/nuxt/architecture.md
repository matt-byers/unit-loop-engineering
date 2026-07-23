# Nuxt Stack — Architecture Guidance

Generalized durable patterns for Nuxt units. Nuxt is Vue's full-stack meta-framework — the Vue component rules below still apply to every `.vue` file; the sections after them are Nuxt-only surface. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Vue component rules (inherited)

- Prefer computed properties over watchers for anything derivable from existing reactive state — watchers are for side effects that synchronize with external systems.
- Props flow down, events flow up: children never mutate props or reach into parent state; use emits with declared payloads.
- Composables own reusable stateful logic; a second copy of an existing composable or utility is a planning miss — find the first one before writing a new one. Nuxt auto-imports from `composables/`, which makes an accidental duplicate especially easy to introduce.
- Stable identity for list rendering: keys come from data identity, never array index, whenever items reorder or mutate.

## Nuxt-only patterns

- **Auto-imports are implicit dependencies.** Components, composables, and utilities under their respective directories are auto-imported — there's no import line marking the dependency. Grep the directory before adding a "new" composable; a second `useX` with a different implementation is a silent duplicate, not a new feature.
- **Universal rendering boundary.** Code in `<script setup>` runs on both server and client during SSR; anything that only makes sense in a browser (`window`, `document`, `localStorage`) must be guarded with `import.meta.client`, run inside `onMounted`, or isolated behind `<ClientOnly>` — an unguarded browser API reference is a server-side crash, not a lint nit.
- **`useFetch`/`useAsyncData` own server-then-client data fetching.** They dedupe the server-rendered payload into the client hydration payload; a raw `fetch` call inside `setup()` re-fetches on the client and diverges from what the server already rendered — treat that divergence as a hydration bug, not a timing fluke.
- **Server routes live in `server/api` / `server/routes`, on Nitro.** They're a distinct runtime (no browser globals, no Vue reactivity) with their own `defineEventHandler` contract; keep request validation and error responses there, not lifted from the Vue component layer.
- **File-based routing is a contract, not a convenience.** A page's behavior is partly determined by its path under `pages/` (route params, catch-alls, layouts) — moving or renaming a file changes routing, so treat that move with the same scrutiny as an explicit route-table edit.
- **`useRuntimeConfig` is the only sanctioned env boundary.** Its `public` keys are client-visible; anything server-only (secrets, internal URLs) belongs in the private half — a value read from `process.env` directly in a component is a boundary violation, not a shortcut.
- **Middleware and plugins run on every relevant request/app-init.** Route middleware under `middleware/` runs before every matching navigation; plugins under `plugins/` run once per app instantiation (server and client separately). A unit that adds either changes a cross-cutting concern — verify it doesn't fire for routes/components it wasn't meant to touch.

## Anti-patterns

- Watcher chains re-deriving state a computed could express.
- Mutating a prop, or mirroring a prop into local state to "cache" it.
- A raw browser-global reference outside a client-only guard.
- Reading `process.env` directly in application code instead of through `useRuntimeConfig`.
- A second composable/component doing what an existing auto-imported one already does.
