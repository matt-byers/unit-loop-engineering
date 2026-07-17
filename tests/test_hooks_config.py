import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT_NAMES = {
    "gate-file-guard.sh",
    "guard-xcodebuild-scope.sh",
}
PROJECT_SCRIPT = re.compile(
    r"\$\{CLAUDE_PROJECT_DIR\}/\.claude/(hooks/[A-Za-z0-9_.-]+\.sh)"
)
FORBIDDEN_CONFIG_FRAGMENTS = (
    "/Users/",
    "/home/",
    "~/.claude",
    "$HOME/.claude",
    "CLAUDE_PROJECT_DIR}/scripts",
    "scripts/agent-hooks",
    ".claude/settings.json",
)


@pytest.fixture
def installed_plugin(tmp_path):
    destination = tmp_path / "installed-project" / ".claude"
    destination.mkdir(parents=True)
    for entry in ("skills", "agents", "hooks"):
        source = REPO_ROOT / entry
        if source.is_dir():
            shutil.copytree(source, destination / entry)
        elif source.is_file():
            shutil.copy2(source, destination / entry)
    return destination


def load_hooks(installed_plugin: Path) -> dict:
    path = installed_plugin / "hooks" / "hooks.json"
    assert path.is_file(), "native hooks/hooks.json is missing"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        pytest.fail(f"hooks/hooks.json is invalid JSON: {error}")
    assert isinstance(value, dict), "hooks/hooks.json must contain a JSON object"
    hooks = value.get("hooks")
    assert isinstance(hooks, dict) and hooks, "hooks/hooks.json must declare hooks"
    return hooks


def command_hooks(hooks: dict):
    for event, groups in hooks.items():
        assert isinstance(groups, list), f"hook event {event} must contain a list"
        for group in groups:
            assert isinstance(group, dict), f"hook group for {event} must be an object"
            entries = group.get("hooks")
            assert isinstance(entries, list), f"hook group for {event} must declare hooks"
            for hook in entries:
                assert hook.get("type") == "command", f"{event} hook must be a command hook"
                command = hook.get("command")
                assert isinstance(command, str) and command.strip(), (
                    f"{event} hook command must be a non-empty string"
                )
                yield event, command


def tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_hook_config_uses_only_project_relative_commands(installed_plugin):
    hooks = load_hooks(installed_plugin)
    commands = list(command_hooks(hooks))
    assert commands, "hooks/hooks.json declares no executable hooks"
    referenced = set()
    for event, command in commands:
        matches = PROJECT_SCRIPT.findall(command)
        assert len(matches) == 1, (
            f"{event} command must reference exactly one copied project script through "
            f"${{CLAUDE_PROJECT_DIR}}/.claude: {command}"
        )
        referenced.add(Path(matches[0]).name)
        for fragment in FORBIDDEN_CONFIG_FRAGMENTS:
            assert fragment not in command, f"{event} command contains forbidden path {fragment}"
    assert referenced == HOOK_SCRIPT_NAMES


@pytest.mark.parametrize("script_name", sorted(HOOK_SCRIPT_NAMES))
def test_relocated_hook_script_exists_is_executable_and_has_valid_bash(installed_plugin, script_name):
    script = installed_plugin / "hooks" / script_name
    assert script.is_file(), f"missing plugin hook script: {script_name}"
    assert script.stat().st_mode & 0o111, f"plugin hook script is not executable: {script_name}"
    result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed for {script_name}: {result.stderr}"


def test_hook_installation_and_execution_do_not_mutate_claude_trust_state(installed_plugin, tmp_path):
    hooks = load_hooks(installed_plugin)
    isolated_home = tmp_path / "home"
    claude_config = isolated_home / ".claude"
    consumer = installed_plugin.parent
    claude_config.mkdir(parents=True)
    marker = claude_config / "existing-state.json"
    marker.write_text('{"trusted": false}\n', encoding="utf-8")
    before = tree_snapshot(isolated_home)
    env = {
        **os.environ,
        "HOME": str(isolated_home),
        "CLAUDE_CONFIG_DIR": str(claude_config),
        "CLAUDE_PROJECT_DIR": str(consumer),
    }
    for _, command in command_hooks(hooks):
        result = subprocess.run(
            ["bash", "-lc", command],
            input="{}",
            capture_output=True,
            text=True,
            cwd=consumer,
            env=env,
        )
        assert result.returncode == 0, (
            f"plugin hook failed safely on an empty payload:\nstdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    assert tree_snapshot(isolated_home) == before, (
        "project hooks must not create or mutate Claude configuration or trust state"
    )


def test_hook_sources_do_not_contain_config_or_trust_installers(installed_plugin):
    hooks_root = installed_plugin / "hooks"
    offenders = []
    for path in hooks_root.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="strict")
        for fragment in FORBIDDEN_CONFIG_FRAGMENTS:
            if fragment in content:
                offenders.append(f"{path.relative_to(installed_plugin)}: {fragment}")
    assert not offenders, "hook package contains config mutation paths:\n" + "\n".join(offenders)


def run_scope_guard(script: Path, command: str, env=None):
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run(
        ["/bin/bash", str(script)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.parametrize(
    "command",
    (
        "xcodebuild test -scheme App",
        r"xcodebuild te\st -scheme App",
        r"xcodebu\ild test -scheme App",
        "/usr/bin/env xcodebuild test -scheme App",
        "/usr/bin/env -u DEVELOPER_DIR xcodebuild test -scheme App",
        "xcrun xcodebuild test -scheme App",
        "xcrun --sdk iphonesimulator xcodebuild test -scheme App",
        'bash -c "xcodebuild test -scheme App"',
        'bash -lc "xcodebuild test -scheme App"',
        'xcodebuild "$TEST_ACTION" -scheme App',
        "xcodebuild $(printf test) -scheme App",
        "scripts/test.sh",
    ),
)
def test_relocated_scope_guard_denies_unscoped_or_ambiguous_tests(installed_plugin, command):
    script = installed_plugin / "hooks" / "guard-xcodebuild-scope.sh"
    result = run_scope_guard(script, command)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "command",
    (
        "xcodebuild build -scheme App",
        "xcodebuild test -scheme App -only-testing:AppTests/FeatureTests",
        "pytest -q tests/test_feature.py",
        "echo 'xcodebuild test is guarded'",
    ),
)
def test_relocated_scope_guard_allows_scoped_builds_and_unrelated_commands(
    installed_plugin, command
):
    script = installed_plugin / "hooks" / "guard-xcodebuild-scope.sh"
    result = run_scope_guard(script, command)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_relocated_scope_guard_denies_without_jq(installed_plugin, tmp_path):
    script = installed_plugin / "hooks" / "guard-xcodebuild-scope.sh"
    isolated_bin = tmp_path / "bin"
    isolated_bin.mkdir()
    (isolated_bin / "python3").symlink_to(shutil.which("python3"))
    env = {**os.environ, "PATH": str(isolated_bin)}
    result = run_scope_guard(script, "xcodebuild test -scheme App", env=env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_relocated_gate_file_guard_fails_open_on_malformed_input(installed_plugin, tmp_path):
    script = installed_plugin / "hooks" / "gate-file-guard.sh"
    result = subprocess.run(
        ["bash", str(script)],
        input="not json",
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0


def test_gate_file_guard_never_appends_through_project_log_symlink(installed_plugin, tmp_path):
    script = installed_plugin / "hooks" / "gate-file-guard.sh"
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    patterns = tmp_path / "patterns.txt"
    patterns.write_text(r"^tests/.*\.snap$" + "\n", encoding="utf-8")
    external = tmp_path / "external.log"
    external.write_text("unchanged\n", encoding="utf-8")
    (consumer / "gate-file-edits.log").symlink_to(external)
    payload = json.dumps(
        {"cwd": str(consumer), "tool_input": {"file_path": "tests/view.snap"}}
    )
    env = {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(consumer),
        "GATE_FILE_PATTERNS_FILE": str(patterns),
    }
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=consumer,
        env=env,
    )
    assert result.returncode == 0
    assert external.read_text(encoding="utf-8") == "unchanged\n"
    assert "refusing unsafe audit log" in result.stderr


def test_gate_file_guard_ignores_custom_log_destination(installed_plugin, tmp_path):
    script = installed_plugin / "hooks" / "gate-file-guard.sh"
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    patterns = tmp_path / "patterns.txt"
    patterns.write_text(r"^tests/.*\.snap$" + "\n", encoding="utf-8")
    external = tmp_path / "external.log"
    payload = json.dumps(
        {"cwd": str(consumer), "tool_input": {"file_path": "tests/view.snap"}}
    )
    env = {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(consumer),
        "GATE_FILE_PATTERNS_FILE": str(patterns),
        "GATE_FILE_EDITS_LOG": str(external),
    }
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=consumer,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert not external.exists()
    assert "tests/view.snap" in (consumer / "gate-file-edits.log").read_text(encoding="utf-8")


def test_gate_file_guard_warns_and_fails_open_for_malformed_adapter(installed_plugin, tmp_path):
    script = installed_plugin / "hooks" / "gate-file-guard.sh"
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    (consumer / "unit-loop.adapter.yaml").write_text(
        "gate_file_patterns: [\n", encoding="utf-8"
    )
    payload = json.dumps(
        {"cwd": str(consumer), "tool_input": {"file_path": "tests/view.snap"}}
    )
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(consumer)}
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=consumer,
        env=env,
    )
    assert result.returncode == 0
    assert "malformed unit-loop.adapter.yaml" in result.stderr
    assert not (consumer / "gate-file-edits.log").exists()
