# FastAPI Stack — Architecture Guidance

Generalized durable patterns for FastAPI units. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Core rules

- Identity is established at the HTTP boundary: auth middleware validates the credential and downstream code derives the user identity from that trusted context, never from a request body or model output.
- Privileged database credentials that bypass row-level security mean every data helper must scope user-owned rows and their parent relationships explicitly — the row filter, not the credential, is the tenancy boundary.
- HTTP middleware handles HTTP concerns only (auth, rate limiting, CORS, headers); domain or model-execution concerns live with the code they wrap, so the domain stays usable offline and in tests.
- Configuration and shared clients come from single factories, not per-call-site construction.
- Redaction of secrets happens at one central choke point reused by every log, crash, and telemetry sink — never per call site.

## Patterns that recur in FastAPI units

- **Harden deterministic contracts before prompts/config:** when behavior is flaky at a boundary, first make the typed contract smaller and more forgiving — consistent parameter names, shared normalizers, canonical ID resolution, explicit error payloads.
- **Fail-closed hydration:** paths that rebuild state from the database surface errors instead of silently falling back to an empty state; empty is valid only when the query genuinely returns no rows.
- **Parameterized queries always:** filters and values are passed as encoded parameters; never interpolate a client-supplied value into SQL or a REST filter string.
- **Server-fetch of user/model-supplied URLs is an SSRF boundary:** validate scheme, reject private/link-local address resolutions, revalidate redirects, cap response bytes, and wrap fetched text in an explicit untrusted-data boundary.
- **Wire contracts are frozen deliberately:** streaming/event schemas and their ordering guarantees are documented contracts; adding an event type means checking resume/replay behavior, not just emission.

## Anti-patterns

- Emitting client events from inside domain handlers instead of deriving them from committed state.
- Multiple writers for one keyed document/state slot — preserve single ownership or do an explicit read-merge-write.
- A second copy of an existing helper, normalizer, or client — find the first one.
