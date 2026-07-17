# Swift Stack — Architecture Guidance

Generalized durable patterns for Swift/SwiftUI units. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Core rules

- State that affects behavior lives in the state-management layer (reducer, observable model), never in view-local `@State`/`@GestureState`.
- External services sit behind dependency clients with live and test implementations; views and reducers never construct SDK objects inline.
- No magic numbers or raw style literals — use the project's design-token layer.
- Generated project files (an XcodeGen/Tuist manifest, generated plists) are edited at their source manifest, never by hand in the generated output.
- Logging goes through the project's shared logger, which owns subsystems, categories, and redaction; never construct ad-hoc loggers at call sites.

## Patterns that recur in Swift units

- **Pure seam + thin adapter** for wrapping SDK/OS-callback APIs: put logic in a pure, SDK-free, unit-tested core; keep SDK contact in a thin adapter. Review the adapter specifically — it is untested by design, so confirm the seam is actually called, the entry point is reached at launch, and threading matches the SDK's real callback queue.
- **Effect cancellation is effect-owned:** use a feature-local cancel ID and cancel-in-flight when a new effect supersedes an old one.
- **Accessibility labels are a public contract:** UI tests select controls by label, so renames must update every test selector in the same change.
- **Gestures that move their own view must measure in a stable coordinate space** (global, not local) — the local space moves with the view and forms a position feedback loop.
- **Exhaustive store tests by default:** assert received actions and state mutations; relax exhaustivity only for deliberately integration-style tests.

## Anti-patterns

- Hand-editing generated project files.
- Duplicating an existing component, token, or client — a second copy is a planning miss; find the first one.
- Business or gesture state in the view layer when it affects the feature contract.
