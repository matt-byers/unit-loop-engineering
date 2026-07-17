# Stage 5 — Behavior Verify (conditional) · Stage 6 — Eval Gate (conditional)

Stage 5 is the "did it actually work when run for real" gate, and it has **two arms by unit type**: frontend/UI units verify through the stack's UI/snapshot verification gate; **backend/agent units verify by driving a real live run of the changed path, not a UI path.** A backend change is proven by watching the system do the thing in a real run — never by exercising it indirectly through the frontend.

## Stage 5 (backend) — Behavior verify via a live run

**Apply if** the unit changes externally observable behavior: tools, prompts, graph/route wiring, persistence the runtime path reads, or anything that changes what the system *does* in a request/turn. **Skip if** the change has no behavioral surface (a pure logging tweak, a helper nothing triggers yet, an internal refactor with identical behavior) — the hermetic test gate (Stage 3) already covers those.

**Why a live run, not the UI:** backend behavior (calls made, self-healing, state writes, prompt effects) is observable directly by running the service/graph against its real dependencies; routing it through the frontend adds nothing and hides the actual trajectory. Use the project's live-run command (defined by the project/stack adapter) that exercises the system in-process and captures a transcript or log artifact — that artifact is the gate.

**Return artifact (mandatory gate):** the captured transcript/log file from this run, showing the expected behavior actually happened (the right calls fired, the change's effect is visible, no error/crash line). Gate on the artifact, not a prose "seems to work".

Drive it non-interactively with the unit's smoke scenario where the adapter supports it (pipe the scripted inputs, capture the artifact, then read the artifact back).

**GREEN**: the artifact shows the expected behavior for the unit's smoke scenario and no error/crash line.
**RED**: the artifact shows the bug reproducing, a crash, or the expected behavior absent → fix and re-run.
**BLOCKED**: a required credential (model provider key, service credential) is not set → the live run can't reach its dependency. Skip with a note that behavior-verify needs the credential, and lean on Stage 3's hermetic tests until it can be run.

**Caveats — this is a demonstration gate, not a deterministic one.** When the live run involves a real LLM or external service it costs money and is non-deterministic, so one clean run *demonstrates* the behavior, it doesn't *prove* it the way mocked tests do. Keep the deterministic assertions in Stage 3 (hermetic, mocked dependencies); use the live run to confirm the whole thing holds together for real. **Scale to the calibrated tier (Step 0.5):** Tier 1 → one scenario, one interaction or two; Tier 3 → several scenarios (and the Stage 6 eval gate on top, where the project has one). Don't burn many real live runs on a small fix.

## Stage 5 (frontend) — UI/UX Gate (conditional)

**Skip if** the unit does not touch any of: views/components, UI state, gestures, navigation, or animations.

**Apply if** the unit description or changed files include the stack's view/feature/component paths.

**Return artifact (mandatory gate):** the stack's UI verification gate's structured result — test pass/fail counts and the snapshot-diff list (empty = no diffs). The orchestrator gates on that, never on a prose "UI looks fine". Do not pipe raw build logs into context; only the pre-parsed summary.

Run the stack's UI/snapshot verification gate (the project adapter names the command or skill).

**GREEN**: All tests pass, no snapshot diffs, no reported regressions.
**RED**: Test failures or snapshot diffs reported. Stop — surface to user as BLOCKED because UI regressions need human eyes to triage.
**BLOCKED**: the app/session won't start, build fails, test target not found.

**Translucency/blur/gradient-heavy units:** snapshot harnesses commonly UNDER-DETECT these — a synchronous renderer can flat-render material effects, so a real restyle can leave baselines nearly identical. Do not read "few/no snapshot diffs" as "no visual change". The authoritative visual gate is a live screenshot pass in BOTH light and dark appearance on the running app — confirm the actual effect and theme-safety live, then re-record whatever snapshots the live state proves changed. Snapshots gate layout STABILITY; live screenshots gate visual CORRECTNESS. (Some rendering effects record fully blank in snapshot harnesses — check the stack's architecture doc for known gotchas.)

**Default flow for a RUN of effect/async-content-dominated visual units (e.g. a card/drawer/sheet redesign spanning several units): build once, hot-reload the rest.** Do not run a separate cold build/snapshot-record cycle per unit when the units are visually chained (same screen, same session) and their spec already names the visual gate as live-session (see `unit-loop/SKILL.md` "Right-size verification" tactic 5). Sequence:
1. Build and launch the live app session ONCE at the start of the run — this is also the compile gate for the first unit.
2. For each subsequent unit's view changes, rely on the stack's hot reload — edit the view file, it hot-swaps into the still-running session in seconds. No rebuild between units. The current adapter and setup contract lives in the project's stack architecture doc.
3. Screenshot the live state after each unit's change lands — this is the unit's real visual gate, shown to the user, not narrated.
4. Snapshot baselines are re-recorded ONCE at feature-end (folded into the tactic-2 full-regression pass), not per-unit — and only for cases that will assert something real; exclude anything that records blank.
This turns a chain of N cold builds (minutes each) into 1 build + N cheap hot-reload+screenshot cycles (seconds each). Reserve the full per-unit test+snapshot cycle for units whose gate genuinely needs it (new gesture/interaction logic covered by an end-to-end UI test, or a unit outside a visual-redesign run).

**Reaching content-dependent states for the live screenshot.** An effect change often only shows over real content, and a fresh launch lands on an EMPTY screen. Don't conclude "can't verify live" from the empty state — drive to a populated state first using the project's mock/fixture launch mode (a launch argument or env flag that binds mock data sources), navigate to the populated screen, then screenshot. Note that appearance toggles can background or relaunch the app in some stacks — relaunch with the mock-mode flag afterward. States NOT live-drivable (streaming transitions that need the real backend, flows gated behind hardware gestures, accessibility settings the tooling can't toggle) are legitimately human-verify: mark those scenarios `Manual check: Required` in the owning spec rather than creating a separate log or burning cycles trying to automate them.

---

## Stage 6 — Eval Gate (conditional)

**Apply only if the project defines an eval harness** (scored scenario runs for agent/LLM behavior). **Skip if** the unit does not touch model-facing behavior: tools, prompts, memory, graph wiring, or system prompt rendering.

**Return artifact (mandatory gate):** the eval scenario scores (from the project's eval runner and/or its tracing service), compared against the prior baseline. The orchestrator gates on the numeric scores, never on a narrative.

Check whether matching eval scenarios exist in the project's eval directory; if they do, run them with the project's eval runner command and capture the score output.

**GREEN**: All scenario scores at or above prior baseline. No BLOCKING judge findings.
**RED**: Score regression beyond the project's threshold (default: > 5%) vs the prior run. Escalate.
**BLOCKED**: no eval harness/scenarios exist, or the tracing/eval service is unreachable — skip this stage with a note.
