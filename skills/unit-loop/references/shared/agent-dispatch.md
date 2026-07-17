# Agent Dispatch Contract

Shared workflows identify a repository project agent with `agent:<name>`. The token is a reference convention, not an executable dispatch language.

## Project Agents

`agent:<name>` resolves only when exactly one native Claude Markdown agent bundled by this skillset declares that logical name. Treat unknown, duplicate, or ambiguous names as a workflow configuration error.

Delegate an `agent:<name>` reference through Claude Code's native named-agent mechanism.

Generic runtime children such as exploration and general execution are runtime capabilities, not named plugin-agent tokens.

## Dispatch Semantics

- **Parallel:** submit independent children in one batch, limited by remaining runtime capacity.
- **Wait:** do not cross the workflow gate until every required child has reached a terminal result.
- **Follow up:** send additional task context to the same child identity when the logical task continues.
- **Interrupt:** stop a child only when its result is no longer needed or its work conflicts with newer instructions.
- **Nested:** a child may dispatch one further level when the workflow assigns it an end-to-end unit. The configured maximum depth is two below the root.

Capacity includes the root session. With `max_threads = 10`, at most nine descendants may run concurrently. Split larger fan-outs into deterministic batches and wait for a batch before starting the next. Preserve result ordering by logical task, not completion time.

## Workflow Form

Shared skills describe the requested `agent:<name>`, its complete task, required return artifact, and whether work is parallel or sequential in ordinary prose. Dispatch through Claude's native named-agent mechanism without embedding consumer-repository paths or a separate dispatch DSL.
