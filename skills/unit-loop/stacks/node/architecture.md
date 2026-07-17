# Node Stack — Architecture Guidance

Generalized durable patterns for Node.js service units. The consuming project's own architecture doc always wins on conflict; record the conflict in the unit result.

## Core rules

- Identity is established at the HTTP boundary: auth middleware validates the credential and downstream code derives the user identity from that trusted context, never from a request body.
- Configuration is read once at startup into a validated config object; modules receive config, they do not read the environment ad hoc.
- Shared clients (database pools, HTTP clients, queues) come from single factories with explicit lifecycle ownership, not per-call-site construction.
- Every async path has an owner for its failure: no floating promises, no swallowed rejections; route errors to the framework's error middleware or a deliberate handler.
- Redaction of secrets happens at one central choke point reused by every log and telemetry sink — never per call site.

## Patterns that recur in Node units

- **Layered ownership:** routes/controllers parse and validate, services own business rules, repositories own persistence — a route that queries the database directly is a boundary violation.
- **Validate at the edge:** request bodies and external responses pass through a schema validator at the boundary so interior code works with typed, trusted shapes.
- **Parameterized queries always:** never interpolate a client-supplied value into SQL or a shell command.
- **Graceful shutdown:** servers close listeners, drain in-flight work, and release pools on termination signals; background loops respect an abort signal.
- **Server-fetch of user-supplied URLs is an SSRF boundary:** validate scheme, reject private address resolutions, revalidate redirects, and cap response bytes.

## Anti-patterns

- Business logic in route handlers that belongs in a service layer.
- Reading environment variables deep inside modules instead of the validated config object.
- A second copy of an existing utility, client wrapper, or middleware — find the first one.
