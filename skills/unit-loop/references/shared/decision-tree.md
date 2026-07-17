# Implementation Decision Tree (shared)

The single source of truth for "should the agent decide this autonomously, or stop and escalate?" Used identically by `unit-loop`, `implement`, and `multi-review`. Do not restate this tree inline in any skill — point here instead.

Walk the questions top to bottom; the **first** one that matches decides the outcome.

| Question | Answer → action |
|---|---|
| Is this decision covered by the spec? | YES → follow the spec, proceed. No further questions. |
| Is this a pure implementation detail? | YES → decide autonomously, follow codebase conventions, note the choice in the commit/checkpoint. |
| Does this affect architecture, UX, or security? | YES → STOP. Escalate as BLOCKED (in the loop) / ask the user (inline). |
| Could this decision be wrong and hard to reverse? | YES → STOP. Escalate as BLOCKED / ask the user. NO → decide autonomously, note in commit. |
| Is a required runtime dependency unavailable (API key, package, env var, service)? | YES → STOP. Escalate as BLOCKED. Missing optional skills use the bundled fallback instead. |

**Notes:**
- "Escalate as BLOCKED" is the loop's term; "ask the user" is the inline-implement term — same boundary, different surfaces.
- The boundary is deliberately conservative: autonomy is the default for everything the spec covers or that is purely local and reversible. Anything that is irreversible, or that moves architecture/UX/security, crosses the line to a human decision.
