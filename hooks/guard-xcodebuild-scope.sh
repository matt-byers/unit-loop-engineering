#!/usr/bin/env bash

input="$(</dev/stdin)"
reason="BLOCKED: full test suite is not allowed in unit-loop stages (Gate A). Scope with -only-testing:YourTestTarget/YourTestClass. For a legitimate Gate B regression run, append '# GATE_B' to that test command."

if command -v python3 >/dev/null 2>&1; then
  HOOK_INPUT="$input" SCOPE_GUARD_REASON="$reason" python3 <<'PYEOF'
import json
import os
import re
import shlex


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


try:
    payload = json.loads(os.environ.get("HOOK_INPUT", ""))
    command = payload.get("tool_input", {}).get("command", "")
except (AttributeError, json.JSONDecodeError):
    command = ""

if not isinstance(command, str) or not command:
    raise SystemExit(0)
if re.search(r"#\s*GATE_B\s*$", command):
    raise SystemExit(0)
normalized_command = command.replace("\\", "")
if "scripts/test.sh" not in normalized_command and "xcodebuild" not in normalized_command:
    raise SystemExit(0)

try:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)
except ValueError:
    deny(os.environ["SCOPE_GUARD_REASON"])
    raise SystemExit(0)

operators = {";", "&", "&&", "|", "||"}
segments = []
segment = []
for token in tokens:
    if token in operators:
        if segment:
            segments.append(segment)
        segment = []
    else:
        segment.append(token)
if segment:
    segments.append(segment)

def denies_segment(segment):
    index = 0
    while index < len(segment) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", segment[index]):
        index += 1
    if index >= len(segment):
        return False
    executable_path = segment[index]
    executable = executable_path.rsplit("/", 1)[-1]
    arguments = segment[index + 1:]
    if executable in {"bash", "sh", "zsh"}:
        command_flags = [value for value in arguments if value.startswith("-") and "c" in value[1:]]
        if command_flags:
            command_index = arguments.index(command_flags[0]) + 1
            if command_index < len(arguments) and command_is_denied(arguments[command_index]):
                return True
        script_arguments = [value for value in arguments if not value.startswith("-")]
        if script_arguments and script_arguments[0].endswith("scripts/test.sh"):
            return True
        return False
    wrapped_xcodebuild = next(
        (
            position
            for position, value in enumerate(segment[index + 1:], start=index + 1)
            if value.rsplit("/", 1)[-1] == "xcodebuild"
        ),
        None,
    )
    if wrapped_xcodebuild is not None:
        return denies_segment(segment[wrapped_xcodebuild:])
    if executable_path.endswith("scripts/test.sh"):
        return True
    if executable != "xcodebuild":
        return False
    scoped = any(value.startswith("-only-testing:") for value in arguments)
    ambiguous = any("$" in value or "`" in value for value in arguments)
    test_like = any(value == "test" or value.startswith("test-") for value in arguments)
    return ambiguous or (test_like and not scoped)


def command_is_denied(value):
    try:
        nested_lexer = shlex.shlex(value, posix=True, punctuation_chars=";&|")
        nested_lexer.whitespace_split = True
        nested_lexer.commenters = ""
        nested_tokens = list(nested_lexer)
    except ValueError:
        return True
    nested_segment = []
    for token in nested_tokens + [";"]:
        if token in operators:
            if nested_segment and denies_segment(nested_segment):
                return True
            nested_segment = []
        else:
            nested_segment.append(token)
    return False


for segment in segments:
    if denies_segment(segment):
        deny(os.environ["SCOPE_GUARD_REASON"])
        raise SystemExit(0)
PYEOF
  exit 0
fi

case "$input" in
  *xcodebuild*|*scripts/test.sh*)
    escaped_reason="${reason//\\/\\\\}"
    escaped_reason="${escaped_reason//\"/\\\"}"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$escaped_reason"
    ;;
esac

exit 0
