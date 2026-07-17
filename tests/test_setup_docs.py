import os
import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
PRESERVED_PREFIX = """Loop engineering is about building autonomous systems that complete work without the need for a human to copilot the process.

This repo provides an autonomous, self-improving, TDD-driven engineering loop based on a focused subset of [UnitWork](https://github.com/ryan-relevanceai/unitwork), created by [Ryan Hay](https://github.com/ryan-relevanceai) and [Michael Zhao](https://github.com/myz96).

## How it works

This skillset is designed to run autonomously after human sign-off at the planning stage, running through implementation, test-based validation, review, and commit without needing human intervention.

The closing of the loop comes at the end of implemention, where the agent reflects on the build process to update the actual skills, agents, and reference docs to ensure each implementation compounds and improves the actual engineering loop.

The loop is instructed to keep the loop skills and supporting docs lean and consolidated to prevent context bloat over time.

NOTE: This skillset is designed to be cloned and added to a project, rather than being installed as a Claude Code plugin. This is so the actual SKILL.md and other supporting files can be tailored to the specific project setup, rather than relying on ever-growing reference docs.
"""
EXPECTED_SKILLS = {
    "compound-learnings",
    "human-verify",
    "implement",
    "multi-review",
    "review-standards",
    "spec-plan",
    "unit-loop",
    "unit-loop-setup",
}
EXPECTED_AGENTS = {
    "spec-plan": {
        "gap-detector",
        "feasibility-validator",
        "utility-pattern-auditor",
    },
    "unit-loop": {
        "test-runner",
        "api-prober",
        "architecture",
        "security",
        "type-safety",
        "patterns-utilities",
        "performance-database",
        "simplicity",
    },
    "implement": set(),
    "multi-review": {
        "architecture",
        "security",
        "type-safety",
        "patterns-utilities",
        "performance-database",
        "simplicity",
        "gap-detector",
    },
    "review-standards": set(),
    "compound-learnings": set(),
    "human-verify": set(),
    "unit-loop-setup": set(),
}


@pytest.fixture(scope="module")
def readme_text():
    return README.read_text(encoding="utf-8")


def install_block(readme_text: str) -> str:
    match = re.search(
        r"^## Install\s*$.*?```bash\n(?P<body>.*?)\n```",
        readme_text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "README Install section needs one Bash block"
    return match.group("body")


def parse_skill_table(readme_text: str) -> dict[str, set[str]]:
    section = readme_text.split("## Skillset\n", 1)[1]
    rows = {}
    for line in section.splitlines():
        if not line.startswith("| `/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        skill = cells[0].strip("`/")
        agents = set(re.findall(r"`([a-z][a-z0-9-]+)`", cells[1]))
        rows[skill] = agents
    return rows


def test_preserves_user_authored_intro_and_how_it_works(readme_text):
    assert readme_text.startswith(PRESERVED_PREFIX)


def test_readme_has_only_requested_sections(readme_text):
    assert re.findall(r"^## (.+)$", readme_text, re.MULTILINE) == [
        "How it works",
        "Install",
        "Skillset",
    ]


def test_readme_install_installs_then_starts_onboarding(readme_text):
    block = install_block(readme_text)
    assert block.splitlines() == [
        'curl -fsSL https://raw.githubusercontent.com/matt-byers/unit-loop-engineering/main/install.sh | bash && claude "/unit-loop-setup"',
    ]


def test_installer_is_valid_bash_and_uses_no_clobber_copy():
    installer = REPO_ROOT / "install.sh"
    assert installer.is_file()
    assert installer.stat().st_mode & 0o111
    result = subprocess.run(["bash", "-n", str(installer)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    text = installer.read_text(encoding="utf-8")
    assert "rsync -a --ignore-existing" in text
    assert "ln -s" not in text


def test_installer_adds_missing_files_without_overwriting_existing_files(tmp_path):
    consumer = tmp_path / "consumer"
    collisions = {
        ".claude/skills/spec-plan/SKILL.md": b"existing skill\n",
        ".claude/agents/review/security.md": b"existing agent\n",
        ".claude/hooks/hooks.json": b'{"existing": true}\n',
    }
    for relative, content in collisions.items():
        path = consumer / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    result = subprocess.run(
        ["bash", str(REPO_ROOT / "install.sh")],
        cwd=consumer,
        env={**os.environ, "UNIT_LOOP_SOURCE_DIR": str(REPO_ROOT)},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    for relative, content in collisions.items():
        assert (consumer / relative).read_bytes() == content
    assert (consumer / ".claude/skills/unit-loop/references/shared/decision-tree.md").is_file()
    assert (consumer / ".claude/skills/unit-loop-setup/SKILL.md").is_file()
    assert (consumer / ".claude/agents/verification/test-runner.md").is_file()
    assert (consumer / ".claude/hooks/gate-file-guard.sh").is_file()
    assert not [path for path in (consumer / ".claude").rglob("*") if path.is_symlink()]
    assert 'claude "/unit-loop-setup"' in result.stdout


def test_skillset_table_covers_every_bundled_skill_and_its_named_agents(readme_text):
    bundled = {path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    assert bundled == EXPECTED_SKILLS
    assert parse_skill_table(readme_text) == EXPECTED_AGENTS


def test_skillset_table_has_no_agents_column(readme_text):
    section = readme_text.split("## Skillset\n", 1)[1]
    assert "| Skill | Description |" in section
    assert "Agents used" not in section


def test_human_verify_description_covers_copilot_log_capture(readme_text):
    section = readme_text.split("## Skillset\n", 1)[1]
    assert "Runs as a copilot during human smoke tests or issue reproduction" in section
    assert "capturing locally generated logs" in section


@pytest.mark.parametrize(
    "forbidden",
    (
        "marketplace add",
        "marketplace update",
        "build_codex_plugin",
        ".codex/",
        ".codex-plugin/",
        "finish these surfaces by hand",
    ),
)
def test_readme_has_no_plugin_packaging_or_codex_instructions(readme_text, forbidden):
    assert forbidden.lower() not in readme_text.lower()
