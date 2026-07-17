# Issue Patterns Reference

50 distinct issue patterns for code review, ordered by frequency. Each pattern includes detection criteria, examples, and fixes. Frequency percentages are informative guidance based on common PR feedback.

## Severity Tiers

Issues are categorized into two tiers that affect priority ranking:

**Tier 1 - Correctness** (Always Higher Priority)
Issues affecting whether code works correctly:
- Security vulnerabilities
- Architecture problems
- Implementation bugs
- Type safety violations
- Functionality gaps

**Tier 2 - Cleanliness** (Lower Priority)
Issues affecting maintainability but not correctness:
- Naming clarity
- File organization
- Code duplication (when not causing bugs)
- Comment quality
- Import/style consistency

At the same P-level, Tier 1 issues should be addressed before Tier 2 issues.

---

## High Frequency Patterns (10%+ of feedback)

### BETTER_IMPLEMENTATION_APPROACH
**Frequency:** ~18% | **Tier:** 1 (Correctness)

**Detection:** Implementing without exploring existing patterns. Complex solutions when simple ones exist. Not leveraging framework features.

**Examples:**
```typescript
// Custom timing with Date.now() when Stopwatch utility exists
const start = Date.now();
// ... work
const elapsed = Date.now() - start;

// Manual JSON parsing when framework handles it
const data = JSON.parse(JSON.stringify(response));

// Custom retry logic when HTTP client has built-in retries
for (let i = 0; i < 3; i++) {
  try { await fetch(url); break; }
  catch { await sleep(1000); }
}
```

**Fix:** Before implementing, search for:
1. Similar functionality in the codebase
2. Framework/library features that handle it
3. Simpler approaches that achieve the same result

---

### TYPE_SAFETY_IMPROVEMENT
**Frequency:** ~12% | **Tier:** 1 (Correctness)

**Detection:** Incomplete type definitions. Using `any`. Type guards that don't validate properties. Nullable fields that should be required.

**Examples:**
```typescript
// Incomplete type guard
typeof x === 'object'  // null is also 'object'!

// Using any
function process(data: any) { ... }

// Optional fields always present after initialization
interface User {
  name?: string;  // Actually required after login
}
```

**Fix:**
- Complete type definitions covering all fields
- Type guards that validate specific properties
- Non-nullable types when values are guaranteed
- Generated types over manual definitions

---

### EXISTING_UTILITY_AVAILABLE
**Frequency:** ~10% | **Tier:** 2 (Cleanliness)

**Detection:** Implementing common functionality without searching for existing utilities.

**Common utility types that often exist:**
- Error message extraction
- Fire-and-forget promise handling
- Parallel execution with concurrency limits
- Precise timing/stopwatch utilities
- String formatting helpers

**Fix:** Always search codebase before implementing common patterns.

---

### CODE_DUPLICATION
**Frequency:** ~8% | **Tier:** 2 (Cleanliness)

**Detection:** Similar functionality in multiple places. Mappings/utilities that exist elsewhere. Copy-paste implementations.

**Examples:**
```ruby
# Creating status display mapping when one exists
STATUS_MAP = { pending: "Pending", done: "Done" }

# Duplicating schema definitions
class OrderSchema  # same as existing InvoiceSchema
```

**Fix:**
- Search for existing implementations first
- Extract repeated patterns into shared utilities
- Share schemas between related features

---

### SEMANTIC_REDUNDANCY
**Tier:** 1 (Correctness) when reimplemented logic should reuse an existing utility; otherwise Tier 2 (Cleanliness)

**Detection:** Duplicated or near-duplicated logic, and reinvented utilities — the same computation, validation, formatting, or control flow expressed two ways, or rebuilt from scratch when the codebase already provides it. This differs from `CODE_DUPLICATION` (literal copy-paste) in that the duplication is *semantic*: structurally different code that does the same thing.

**Why this gets its own pattern:** AI-generated code carries ~1.87x more semantic redundancy than human code (p<0.001), and reviewers have a documented **"reviewer's blind spot"** — surface plausibility makes them feel *more* positive about the redundant code and wave it through. The `patterns-utilities` agent must **actively hunt** for reimplemented existing logic rather than trusting that it looks fine.

**Examples:**
```swift
// Hand-rolled price formatting when formatPrice(_:currency:) already exists
let display = "\(currency) \(String(format: "%.2f", price))"

// A second URL-allowlist check inline, when validate_url already enforces it

// Re-deriving a value the reducer/state already holds, computed a different way
```

**Fix:** Search the codebase for an existing utility or pattern before accepting the logic. If reimplemented logic duplicates an existing utility, route it to that utility (Tier 1). If it's genuinely new but duplicated within the change, extract one shared implementation (Tier 2). Treat agent refactors with extra scrutiny — never accept "looks equivalent" without proving behaviour preservation against tests.

---

### NULL_HANDLING
**Frequency:** ~6% | **Tier:** 1 (Correctness)

**Detection:** Empty strings as fallbacks. Optional fields that should be required. Default values masking absence.

**Examples:**
```typescript
// Empty string hides absence
const name = user.name ?? "";

// Zero masks missing value
const count = data.count ?? 0;  // when zero is valid

// Optional when always present
interface Config {
  apiKey?: string;  // Actually required
}
```

**Fix:** Use `null` to represent absence. Handle nullable values explicitly.

---

### MAKE_SELF_DOCUMENTING
**Frequency:** ~6% | **Tier:** 2 (Cleanliness)

**Detection:** Unusual patterns, hardcoded/magic values, non-obvious inheritance, or workarounds that are hard to read at a glance.

**Examples:**
```typescript
const timeout = 120000;        // magic number — meaning unclear
obj.__proto__ = null;          // non-obvious workaround
```

**Fix:** Make the code self-explanatory — extract a well-named constant (`const AGENT_REQUEST_TIMEOUT_MS = 120_000`), rename, or restructure. Do **not** add an explanatory comment: this project does not use code comments (see `SUPERFLUOUS_COMMENT`). The only residual case for a one-line note is a genuinely non-obvious gotcha that no name can capture — and even then prefer a linked issue.

---

## Medium Frequency Patterns (5-10%)

### NAMING_CLARITY
**Frequency:** ~5.5% | **Tier:** 2 (Cleanliness)

**Detection:** Names conflicting with domain terms. Abbreviations in APIs. Inconsistent terminology.

**Examples:**
```typescript
// 'config' when "Config" is a domain concept
const config = { ... };  // Conflicts with Config entity

// Inconsistent terminology
user.state vs user.status  // Pick one

// Abbreviations in public API
getUserAcct()  // Use getAccount
```

**Fix:** Avoid domain-specific terms for unrelated concepts. Use full words in APIs.

---

### FILE_ORGANIZATION
**Frequency:** ~5% | **Tier:** 2 (Cleanliness)

**Detection:** Barrel files. Code in wrong directories. Utils files instead of domain placement.

**Examples:**
```typescript
// Barrel file (index.ts re-exports)
export { UserService } from './user-service';
export { AuthService } from './auth-service';

// Auth code moved out of auth module
// utils/auth-helpers.ts  // Should be auth/helpers.ts

// Generic utils file
// utils.py with unrelated functions
```

**Fix:** No barrel files. Code lives near its domain context.

---

### REDUNDANT_LOGIC
**Frequency:** ~5% | **Tier:** 2 (Cleanliness)

**Detection:** Checks that constraints already enforce. Constants in return types. Async without await. Duplicate validation.

**Examples:**
```typescript
// Null check when column has NOT NULL constraint
if (user.email != null) { ... }  // DB guarantees non-null

// Including type field that's always the same
return items.filter(i => i.type === 'order')
  .map(i => ({ type: i.type, ...rest }));  // type is always 'order'

// Async but never awaiting
async function getData() {
  return cachedValue;  // No await needed
}
```

**Fix:** Understand what's enforced by schemas, database, upstream validation.

---

### UNNECESSARY_CAST
**Frequency:** ~5% | **Tier:** 1 (Correctness)

**Detection:** `as` assertions to access properties. Bypassing TypeScript. Casting already-typed values.

**Examples:**
```typescript
// Casting to access properties
const id = (value as SomeType).property;

// Casting to avoid fixing types
const data = response as unknown as ExpectedType;

// Already typed value cast again
const user: User = data as User;  // data is already typed
```

**Fix:** Never cast to access properties. Fix underlying types. Use runtime validation.

---

### ARCHITECTURAL_CONCERN
**Frequency:** ~5% | **Tier:** 1 (Correctness)

**Detection:** Adding use-case-specific fields to shared infrastructure. Rigid abstractions. Missing extensibility.

**Examples:**
```typescript
// Feature-specific fields in generic notification context
interface NotificationContext {
  userId: string;
  agentId: string;  // Only used by agents feature
}

// Service that immediately needs customization
class EmailService {
  send() { /* One-size-fits-all */ }
}
```

**Fix:** Keep shared infrastructure generic. Design for extensibility.

---

### ERROR_HANDLING_NEEDED
**Frequency:** ~4% | **Tier:** 1 (Correctness)

**Detection:** Missing fallbacks for external services. Silently caught errors. Undefined limit behavior.

**Examples:**
```typescript
// Catching and logging instead of throwing
try {
  await externalApi.call();
} catch (e) {
  console.error(e);  // Caller doesn't know it failed
}

// No graceful degradation
const result = await thirdPartyService.fetch();  // What if it fails?

// Limits without defined behavior
if (items.length > MAX_ITEMS) { /* ??? */ }
```

**Fix:** Let errors propagate. Implement graceful degradation. Define limit behavior.

---

### ACCESS_CONTROL_ENTRY_POINTS
**Frequency:** ~3% | **Tier:** 1 (Security — often P1/BLOCKING)

**Detection:** A resource keyed by a client-supplied id (conversation/thread/document/checkpoint) is reachable by MORE THAN ONE code path, but the ownership/authorization gate guards only the primary one. Smell: an `if <alternate-mode>: ... return` branch (resume, replay, retry, webhook, batch, export, an alternate HTTP verb) that runs *before* or *instead of* the gate the main path has. The gate was added where the feature was first written, and a sibling entry point to the same resource was overlooked.

**Examples:**
```python
async def handler(user_id, body, mode=None):
    config = {"thread_id": body.conversation_id}   # client-supplied key
    if mode is not None:
        async for e in resume(config): yield e      # <-- reads the resource, NO ownership check
        return
    if not owns(body.conversation_id, user_id): reject()   # gate only on the main path
    async for e in run(config): yield e
```
The resume branch lets any authenticated user read another user's resource by supplying its id. (A real observed IDOR: a chat resume path read another user's checkpoint — their saved state + last reply.)

**Fix:** Enumerate EVERY path that reaches the resource and gate all of them — lift the authorization check above the entry-point branch. Use a **read-only** ownership assertion for read/replay paths (don't reuse a create-on-missing gate that would also mutate). Add a regression test per alternate path (e.g. resume-of-unowned → forbidden, no resource read). When reviewing any auth gate, ask: "what else reaches this resource?"

---

## Medium-Low Frequency Patterns (2-5%)

### REMOVE_UNUSED_CODE
**Frequency:** ~4% | **Tier:** 2 (Cleanliness)

**Detection:** Fields added "for the future". Code unnecessary after refactoring. Unused interface properties.

**Fix:** Only add fields/code with immediate use. Remove what becomes unnecessary.

---

### CONSOLIDATE_LOGIC
**Frequency:** ~4% | **Tier:** 2 (Cleanliness)

**Detection:** Split conditionals. Separate classes that could be methods. Overlapping indexes.

**Fix:** Review control flow for consolidation. Question if new classes are needed.

---

### NIT_MINOR_ISSUE
**Frequency:** ~4% | **Tier:** 2 (Cleanliness)

**Detection:** Style inconsistencies. Minor naming issues. Non-idiomatic code.

**Fix:** Follow existing patterns in the codebase.

---

### NAMING_CONVENTION
**Frequency:** ~3% | **Tier:** 2 (Cleanliness)

**Detection:** Wrong casing. Non-idiomatic names. Abbreviations.

**Fix:** Python uses snake_case. JavaScript/TypeScript uses camelCase. Avoid abbreviations. Follow conventions.

---

### TESTING_VERIFICATION
**Frequency:** ~3% | **Tier:** 1 (Correctness)

**Detection:** Tests not matching names. Missing test updates. Unverified queries.

**Fix:** Test names describe what's tested. Update tests with implementation. EXPLAIN ANALYZE queries.

---

### TEST_SELECTOR_ZERO_MATCH
**Tier:** 1 (Correctness) | **Default severity:** HIGH

**Detection:** A test/CI selector or filter that matches by **path/directory/glob** rather than by **test identity** (the runner's `Target/ClassName[/method]` form), and that **passes when zero tests match**. The trap: it looks correct and is green today precisely because nothing matches yet — it silently breaks the moment a real test is added. Examples: `xcodebuild -only-testing:Target/<Directory>` (the middle segment must be an XCTest class, not a folder); `pytest <dir-that's-empty>`; a `-k`/grep filter derived from a path; a test-plan name that doesn't exist.

**Why HIGH:** zero-match-passes hides the defect through every green run until the first real test turns it into a CI failure — the cost lands far from the cause.

**Fix:** Select by real test identity. Derive the actual class/test names from the test files (e.g. parse `class X: XCTestCase`) and build one valid selector per discovered test; exit cleanly when none exist. Verify the selector resolves to ≥1 real test before trusting it. Applies to any runner whose selector can be satisfied by an empty match set.

---

### EXTRACT_TO_HELPER
**Frequency:** ~3% | **Tier:** 2 (Cleanliness)

**Detection:** Same authorization pattern copied. Repeated filtering. Useful inline types.

**Fix:** Extract patterns that will be reused. Shared type utilities.

---

### CONFIGURATION_VERIFICATION
**Frequency:** ~3% | **Tier:** 1 (Correctness)

**Detection:** Missing config updates. Terraform conflicts. Wrong retention periods.

**Fix:** Update all related configs. Verify values make sense.

---

### USE_CONSTANT
**Frequency:** ~3% | **Tier:** 2 (Cleanliness)

**Detection:** Hardcoded durations. Magic strings. Environment-specific URLs hardcoded. Hardcoded fallback values.

**Examples:**
```typescript
// Hardcoded duration
setTimeout(fn, 120000);

// Hardcoded fallback
const locale = userLocale ?? "en";

// Magic string
if (status === "pending_review") { ... }
```

**Fix:** Extract hardcoded strings to named constants. Use `DEFAULT_*` or `FALLBACK_*` naming.

---

### WRONG_LOCATION
**Frequency:** ~3% | **Tier:** 2 (Cleanliness)

**Detection:** Timing in wrong lifecycle. Tests at wrong layer. Config in service classes.

**Fix:** Tests at appropriate level. Config in config. Domain logic in domain modules.

---

### DATABASE_INDEX_MISSING
**Frequency:** ~2.5% | **Tier:** 1 (Correctness)

**Detection:** Queries filtering columns without indexes. Changed query columns.

**Fix:** Verify indexes exist. EXPLAIN ANALYZE before deploying.

---

### PERFORMANCE_OPTIMIZATION
**Frequency:** ~2.5% | **Tier:** 1 (Correctness)

**Detection:** Over-fetching across parallel queries. Memory loading for streaming. Re-validating data.

**Fix:** Calculate actual needs. Stream large data. Skip validation for already-validated data.

---

### FUNCTION_SIGNATURE_REFACTOR
**Frequency:** ~2% | **Tier:** 2 (Cleanliness)

**Detection:** Many parameters. Same-typed parameters that could be swapped.

**Fix:** Single args object for 4+ parameters.

---

### SCOPE_REDUCTION
**Frequency:** ~2% | **Tier:** 2 (Cleanliness)

**Detection:** Including too much. Generated files not ignored.

**Fix:** Filter to only what's needed.

---

### SCOPE_CREEP
**Frequency:** ~2% | **Tier:** 2 (Cleanliness)

**Detection:** Unrelated changes in feature PRs. Mixed concerns.

**Fix:** Keep PRs focused. Separate concerns into separate PRs.

---

### FRAGILE_IMPLEMENTATION
**Frequency:** ~2% | **Tier:** 1 (Correctness)

**Detection:** Relying on `__str__`. Using `getattr` with defaults. Non-deterministic LLM instructions.

**Fix:** Explicit property access. Code-side deterministic logic.

---

### RUNTIME_VALIDATION
**Frequency:** ~2% | **Tier:** 1 (Correctness)

**Detection:** Missing runtime checks at boundaries. Trusting external data.

**Fix:** Validate at system boundaries.

---

### REMOVE_DEBUG_CODE
**Frequency:** ~2% | **Tier:** 2 (Cleanliness)

**Detection:** Print statements. Console.log. Test infrastructure in production code.

**Fix:** Remove before PR. Use proper logging.

---

### IMPORT_STYLE_CONSISTENCY
**Frequency:** ~2% | **Tier:** 2 (Cleanliness)

**Detection:** Dynamic imports in tests. Mixed relative/absolute. Different packages for same thing.

**Fix:** Follow established patterns. Use absolute imports.

---

### DUPLICATE_SERIALIZATION
**Frequency:** ~2% | **Tier:** 1 (Correctness — silent divergence risk)

**Detection:** Serialization logic that converts a model type to a dictionary or wire format appears at more than one call site instead of as a method on the model type. Flag inline `map { record in ["field": record.field, ...] }` blocks that construct the same shape more than once across the codebase.

**Why it matters:** Two independent serialization paths for the same type will diverge silently — a field rename or format change in one copy produces mismatched output (e.g. a debug HTTP endpoint and a disk-persistence path disagree) with no compile-time signal.

**Fix:** Place the serialization as a method on the model type itself. Any second call site that constructs the same shape inline is the signal that the method was missing from the model.

**Severity:** HIGH when two or more live code paths serialize the same type differently; MEDIUM when the paths are identical today but structurally fragile.

---

## Lower Frequency Patterns (<2%)

### DATABASE_QUERY_OPTIMIZATION
**Frequency:** ~1.5% | **Tier:** 1 (Correctness)

Regex vs ILIKE. Missing indexed columns. Raw SQL vs query builder.

---

### PARALLELIZATION_OPPORTUNITY
**Frequency:** ~1.5% | **Tier:** 1 (Correctness)

Sequential independent queries. Sequential API calls that could be parallel.

---

### MAGIC_NUMBER
**Frequency:** ~1.5% | **Tier:** 2 (Cleanliness)

Unexplained numeric constants. Array slices without context.

---

### ERROR_MESSAGE_CLARITY
**Frequency:** ~1.5% | **Tier:** 1 (Correctness)

Status codes without response text. Missing operation context.

---

### AI_GENERATED_CODE_CONCERN
**Frequency:** ~1.5% | **Tier:** 2 (Cleanliness)

Unnecessary reorganization. Non-standard comments. Unusual patterns.

---

### REMOVE_COMMENT
**Frequency:** ~1.5% | **Tier:** 2 (Cleanliness)

Unnecessary comments. Commented-out code.

---

### SUPERFLUOUS_COMMENT
**Tier:** 3 (Cleanliness) | **Default severity:** P3 — escalate to P2 when the comment introduces a doc/logic discrepancy (comment says X, code does Y)

**Detection:** Comments that restate what the code already says. Coding agents over-produce these — they help the next LLM edit the code more than they help a human reader, and they drift out of sync with the code, creating doc/logic discrepancies that surface-level review misses.

**Examples:**
```swift
// Increment the counter
counter += 1

// MARK: - Helpers   (section-divider noise with one function under it)

// Returns a String
func title() -> String { ... }   // restated type signature

// Set isLoading to true
state.isLoading = true
```

This project does not use code comments. Flag *any* comment — what-narration, why-narration, doc comments (`///`), and section dividers. Prefer fixing the underlying cause (rename, extract a named constant, restructure) over the comment so the explanation isn't needed. The only thing to leave is a single short line for a genuinely non-obvious gotcha that no name can capture — rare.

**Fix:** Remove the comment. When a comment contradicts the code it documents, treat it as P2 — resolve the discrepancy (fix code or remove the stale comment), don't leave the two out of sync.

---

### BREAKING_CHANGE_CONCERN
**Frequency:** ~1% | **Tier:** 1 (Correctness)

Frontend-breaking API changes. Schema changes without migration.

---

### SECURITY_PERMISSIONS
**Frequency:** ~1% | **Tier:** 1 (Correctness)

Too permissive authorization. Unsanitized HTML. Logging PII.

---

### LIMIT_BOUNDARY_CONCERN
**Frequency:** ~1% | **Tier:** 1 (Correctness)

Undefined behavior at limits. Missing rate limiting.

---

### SCHEMA_VALIDATION_MISSING
**Frequency:** ~1% | **Tier:** 1 (Correctness)

Missing `required`. Missing `additionalProperties: false`.

---

### ENVIRONMENT_CONFIGURATION
**Frequency:** ~1% | **Tier:** 1 (Correctness)

Wrong defaults. Missing environment awareness.

---

### TYPE_CHOICE_QUESTION
**Frequency:** ~1% | **Tier:** 2 (Cleanliness)

Why Mapping vs dict? Why this cast?

---

### VERIFY_DOCUMENTATION_ACCURACY
**Frequency:** ~1% | **Tier:** 2 (Cleanliness)

Outdated references. Wrong links.

---

### RATE_LIMITING_NEEDED
**Frequency:** <1% | **Tier:** 1 (Correctness)

Expensive endpoints without limits.

---

### REVERT_UNRELATED_CHANGES
**Frequency:** <1% | **Tier:** 2 (Cleanliness)

Changes outside PR scope.

---

### RECENT_CHANGE_CONFUSION
**Frequency:** <1% | **Tier:** 1 (Correctness)

Contradicting recent changes.

---

## Agent Backend Patterns

### ASYNC_MIDDLEWARE_INCOMPATIBILITY
**Frequency:** rare | **Tier:** 1 (Correctness) | **Severity:** BLOCKING when agent runtime is async

**Detection:** A function decorated with `@wrap_model_call` is defined as `def` (sync) rather than `async def`. LangGraph always runs `astream`/`ainvoke`, which calls `awrap_model_call`. A sync-decorated function never registers `awrap_model_call`, so every agent invocation raises `NotImplementedError` at runtime.

```python
# WRONG — @wrap_model_call on a sync def does not register awrap_model_call
@wrap_model_call
def trim_context(request, handler):
    ...
    return handler(request.override(messages=trimmed))  # sync call

# CORRECT — async def registers both wrap_model_call and awrap_model_call
@wrap_model_call
async def trim_context(request, handler):
    ...
    return await handler(request.override(messages=trimmed))
```

**Why BLOCKING:** LangGraph's graph execution always goes through `astream`/`ainvoke`. A sync middleware silently blocks every conversation — the failure only appears at runtime, not at graph-build time.

**Verification:**
```python
from src.graphs.trim_context import trim_context
assert hasattr(trim_context, "awrap_model_call"), "missing awrap_model_call — decorate an async def"
```

**Fix:** Change `def` → `async def` and `handler(...)` → `await handler(...)`. If the middleware itself does no async work, `await` still required — the contract is async end-to-end.

---

## Security-Specific Patterns (Always P1)

### INJECTION_VULNERABILITY
**Tier:** 1 (Correctness) | **Severity:** Always P1

SQL injection, command injection, LDAP injection. Any unsanitized user input in queries or commands.

---

### AUTHENTICATION_BYPASS
**Tier:** 1 (Correctness) | **Severity:** Always P1

Weak token generation, session not invalidated, missing auth checks.

---

### AUTHORIZATION_BYPASS
**Tier:** 1 (Correctness) | **Severity:** Always P1

Missing ownership checks, IDOR vulnerabilities, permission escalation.

---

### SENSITIVE_DATA_EXPOSURE
**Tier:** 1 (Correctness) | **Severity:** P1/P2

Logging passwords, exposing internal IDs, credentials in code.

---

### XSS_VULNERABILITY
**Tier:** 1 (Correctness) | **Severity:** Always P1

Unescaped user input in HTML, innerHTML with user data.

---

### GATE_FILE_MODIFICATION
**Tier:** 1 (Correctness) | **Severity:** Always P1 (BLOCKING)

**Detection:** The implement subagent satisfies a verification gate by editing the gate itself rather than the code under test. This is reward-hacking: deleting or regenerating snapshot baselines, relaxing or rewriting test assertions written in Stage 1 (Tests-first), editing perf baselines, or altering eval scenarios — anything that moves the bar instead of clearing it. Frontier models do this by default, and prompt-level "don't cheat" instructions barely help, so this is enforced structurally.

**Detection signal:** an implement-stage `git diff` that touches the project's test directories or any of its declared gate-file path patterns (snapshot baselines, performance baselines, eval scenarios — from `gate_file_patterns` in the project's `unit-loop.adapter.yaml`; see the project-adapter guidance bundled with the `unit-loop` skill) **without explicit justification** in the unit brief. If the project has not declared gate-file patterns, say so explicitly rather than reporting a clean check.

```bash
git diff --name-only | grep -E '{the project's declared gate-file path patterns}|{the project's test-directory pattern for the stack's source-file extensions}'
```

**Why BLOCKING:** the gate is the source of truth for whether the unit works. An unjustified gate-file edit invalidates every green result that follows it — the cost lands far from the cause, in production.

**Fix:** Re-baselining (regenerating snapshots, updating perf/eval baselines) is an **orchestrator-level action only**, never performed inside an implement subagent. Revert the gate-file edit and make the code satisfy the existing gate. A genuine intentional baseline change must be scoped by the owning verification skill and committed with a message explaining why.

---

## Holistic Patterns

### ARCHITECTURAL_DIRECTION
**Tier:** Informational (not actionable by review system)

**Detection:** The PR's fundamental approach is wrong — not individual code issues, but the direction itself. Every line may be well-written but the whole thing is solving the problem incorrectly.

**Signal patterns:**
- Building a new service/module when an existing one should be extended
- Logic in the wrong layer (e.g., business rules in frontend, validation client-side when it belongs server-side)
- Creating a new abstraction when the work belongs in an existing one
- Solving the symptom instead of the root cause
- Reimplementing a flow that already exists elsewhere in the codebase

**NOT this pattern:**
- Individual files in the wrong location → WRONG_LOCATION
- Tight coupling between modules → ARCHITECTURAL_CONCERN
- Code that works but could be structured better → FILE_ORGANIZATION
- Scope creep (unrelated changes in the PR) → SCOPE_CREEP

**High bar:** Most PRs have a sound approach with imperfect execution. Only flag when the direction itself is wrong — when fixing individual issues would be wasted effort because the foundation needs rethinking.

**Output:** Informational observation in the review document. Not a P1/P2/P3 finding. Does not enter the fix loop. The developer decides what to do with it.

---

## Quick Reference

**Top 5 by frequency:**
1. BETTER_IMPLEMENTATION_APPROACH (18%) - Search first, leverage framework features
2. TYPE_SAFETY_IMPROVEMENT (12%) - No casting, complete type guards
3. EXISTING_UTILITY_AVAILABLE (10%) - Search codebase before implementing
4. CODE_DUPLICATION (8%) - Check for existing implementations
5. NULL_HANDLING (6%) - Use null, not empty strings

**Always P1 (Critical):**
- Any injection vulnerability
- Authentication/authorization bypass
- XSS in user content
- Security boundary violations
