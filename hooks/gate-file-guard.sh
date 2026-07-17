#!/usr/bin/env bash
# Gate-file edit guard — PostToolUse hook for Edit|Write|MultiEdit.
#
# Purpose: deterministically record every time the model edits a *verification
# gate* artifact (snapshot reference images, performance baselines, eval
# scenarios). These are the files a reward-hacking implementation could quietly
# edit to make a failing gate pass. The hook does NOT block — editing these is
# legitimate during TDD (Stage 1) and intentional re-baselining. It leaves an
# audit trail the Stage 4 code review reads, and surfaces an inline note so the
# implementing agent knows the edit is gate-sensitive.
#
# Gate-file path patterns (extended regexes) come from, in precedence order:
#   1. GATE_FILE_PATTERNS_FILE — explicit override; a plain-text file, one
#      pattern per line ('#' comments and blank lines ignored).
#   2. gate_file_patterns in unit-loop.adapter.yaml at the project root — the
#      default source (see the unit-loop skill's references/project-adapter.md).
#      Parsed with python3 + PyYAML; when the adapter file exists and parses,
#      its declaration (even an empty one) is authoritative.
# With no declared patterns the hook does nothing — this repository ships no
# product-specific gate paths.
#
# Matched edits are appended to gate-file-edits.log at the project root.
#
# Audit-trail blind spots: this hook only sees Edit/Write/MultiEdit tool calls.
# Edits made through Bash (sed, cp, redirects, git checkout) or through symlink
# aliases of a gate path evade it — the Stage 4 `git diff` remains the
# authoritative per-unit check; this log is a secondary trail only.
#
# Contract: this hook MUST be harmless. It never blocks, never fails the tool
# call. Any internal error → exit 0 silently. Do not change that without thought:
# a PostToolUse hook that errors can disrupt every edit in the repo.

set +e

input="$(cat 2>/dev/null)"
[ -z "$input" ] && exit 0

cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)"
fi
[ -z "$cwd" ] && cwd="$(pwd)"
start="${CLAUDE_PROJECT_DIR:-$cwd}"
repo="$(git -C "$start" rev-parse --show-toplevel 2>/dev/null)"
[ -z "$repo" ] && repo="$start"
repo="$(cd "$repo" 2>/dev/null && pwd -P)" || exit 0
cwd="$(cd "$cwd" 2>/dev/null && pwd -P)" || exit 0

read_pattern_file() {
  [ -f "$1" ] || return 0
  grep -vE '^[[:space:]]*(#|$)' "$1" 2>/dev/null | paste -sd '|' -
}

adapter_patterns() {
  python3 - "$1" <<'PYEOF'
import sys
try:
    import yaml
except ImportError:
    sys.exit(3)
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
except Exception as error:
    print(f"gate-file-guard: malformed unit-loop.adapter.yaml: {error}", file=sys.stderr)
    sys.exit(4)
if not isinstance(data, dict):
    print("gate-file-guard: malformed unit-loop.adapter.yaml: root must be a mapping", file=sys.stderr)
    sys.exit(4)
patterns = data.get("gate_file_patterns") or []
if not isinstance(patterns, list):
    print("gate-file-guard: malformed unit-loop.adapter.yaml: gate_file_patterns must be a list", file=sys.stderr)
    sys.exit(4)
print("|".join(str(p) for p in patterns if str(p).strip()))
PYEOF
}

gate_pattern=""
adapter_file="$repo/unit-loop.adapter.yaml"
if [ -n "${GATE_FILE_PATTERNS_FILE:-}" ]; then
  gate_pattern="$(read_pattern_file "$GATE_FILE_PATTERNS_FILE")"
elif [ -f "$adapter_file" ] && command -v python3 >/dev/null 2>&1; then
  adapter_output="$(adapter_patterns "$adapter_file")"
  adapter_status=$?
  if [ "$adapter_status" -eq 3 ]; then
    printf '%s\n' "gate-file-guard: PyYAML unavailable; gate-file auditing disabled" >&2
  elif [ "$adapter_status" -eq 0 ]; then
    gate_pattern="$adapter_output"
  fi
elif [ -f "$adapter_file" ]; then
  printf '%s\n' "gate-file-guard: python3 unavailable; gate-file auditing disabled" >&2
fi
[ -z "$gate_pattern" ] && exit 0

file_path=""
patch_command=""
if command -v jq >/dev/null 2>&1; then
  file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
  patch_command="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)"
fi
if [ -z "$file_path" ]; then
  file_path="$(printf '%s' "$input" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')"
fi

raw_paths="$({
  [ -n "$file_path" ] && printf '%s\n' "$file_path"
  [ -n "$patch_command" ] && printf '%s\n' "$patch_command" | sed -nE 's/^\*\*\* (Add|Update|Delete) File: (.*)$/\2/p; s/^\*\*\* Move to: (.*)$/\1/p'
})"

normalize_path() {
  local path="$1" absolute part normalized
  local -a stack=()
  case "$path" in
    /*) absolute="$path" ;;
    *) absolute="$cwd/$path" ;;
  esac
  local old_ifs="$IFS"
  IFS='/'
  read -ra parts <<< "$absolute"
  IFS="$old_ifs"
  for part in "${parts[@]}"; do
    case "$part" in
      ''|.) ;;
      ..)
        [ "${#stack[@]}" -gt 0 ] || return 1
        unset 'stack[${#stack[@]}-1]'
        ;;
      *) stack+=("$part") ;;
    esac
  done
  normalized="/$(IFS=/; printf '%s' "${stack[*]}")"
  case "$normalized" in
    "$repo") return 1 ;;
    "$repo"/*) printf '%s\n' "${normalized#"$repo"/}" ;;
    *) return 1 ;;
  esac
}

paths="$(while IFS= read -r path; do
  [ -n "$path" ] && normalize_path "$path"
done <<EOF
$raw_paths
EOF
)"
paths="$(printf '%s\n' "$paths" | awk 'NF && !seen[$0]++')"

gate_paths="$(printf '%s\n' "$paths" | grep -E -e "$gate_pattern" 2>/dev/null)"
[ -z "$gate_paths" ] && exit 0

timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "gate-file-guard: python3 unavailable; audit log not written" >&2
  exit 0
fi

GATE_PATHS="$gate_paths" python3 - "$repo" "$timestamp" <<'PYEOF'
import os
import stat
import sys

repo = os.path.realpath(sys.argv[1])
timestamp = sys.argv[2]
paths = os.environ.get("GATE_PATHS", "").splitlines()
log_name = "gate-file-edits.log"
log_path = os.path.join(repo, log_name)

if os.path.islink(log_path):
    print("gate-file-guard: refusing unsafe audit log symlink", file=sys.stderr)
    sys.exit(0)

repo_fd = None
log_fd = None
try:
    repo_fd = os.open(repo, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    log_fd = os.open(log_name, flags, 0o600, dir_fd=repo_fd)
    if not stat.S_ISREG(os.fstat(log_fd).st_mode):
        print("gate-file-guard: refusing unsafe audit log destination", file=sys.stderr)
        sys.exit(0)
    payload = "".join(f"{timestamp}\t{path}\n" for path in paths if path).encode()
    if payload:
        os.write(log_fd, payload)
except OSError as error:
    print(f"gate-file-guard: refusing unsafe audit log: {error}", file=sys.stderr)
finally:
    if log_fd is not None:
        os.close(log_fd)
    if repo_fd is not None:
        os.close(repo_fd)
PYEOF

note="Edited verification gate files: $(printf '%s' "$gate_paths" | tr '\n' ' '). Stage 4 must explicitly justify each change. Never edit a snapshot, baseline, or eval gate solely to make a failing check pass."
if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$note" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}' 2>/dev/null
fi

exit 0
