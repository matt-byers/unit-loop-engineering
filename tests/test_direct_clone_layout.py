import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("skills", "agents", "hooks")
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
FORBIDDEN_PATHS = (
    ".claude-plugin",
    ".codex",
    ".codex-plugin",
    "plugin",
    "scripts/agent-config",
    "scripts/packaging",
)


def test_repository_exposes_complete_physical_claude_surfaces():
    bundled = {path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")}
    assert bundled == EXPECTED_SKILLS
    assert len(list((REPO_ROOT / "agents").rglob("*.md"))) == 11
    assert (REPO_ROOT / "hooks/hooks.json").is_file()
    assert (REPO_ROOT / "install.sh").is_file()
    assert (REPO_ROOT / "skills/unit-loop/references/shared/agent-dispatch.md").is_file()
    assert not [path for path in REPO_ROOT.rglob("*") if ".git" not in path.parts and path.is_symlink()]


def test_repository_has_no_provider_packaging_surface():
    for relative in FORBIDDEN_PATHS:
        assert not (REPO_ROOT / relative).exists(), relative


def test_physical_copy_is_self_contained_and_editable_without_mutating_source(tmp_path):
    installed = tmp_path / "project" / ".claude"
    installed.mkdir(parents=True)
    for surface in SURFACES:
        shutil.copytree(REPO_ROOT / surface, installed / surface)

    copied_reference = installed / "skills/unit-loop/references/shared/decision-tree.md"
    source_reference = REPO_ROOT / "skills/unit-loop/references/shared/decision-tree.md"
    source_before = source_reference.read_bytes()
    copied_reference.write_text("project-owned change\n", encoding="utf-8")

    assert source_reference.read_bytes() == source_before
    assert (installed / "skills/compound-learnings/SKILL.md").is_file()
    assert (installed / "skills/unit-loop-setup/SKILL.md").is_file()
    assert (installed / "agents/plan-review/gap-detector.md").is_file()
    assert (installed / "agents/plan-review/feasibility-validator.md").is_file()
    assert (installed / "agents/plan-review/utility-pattern-auditor.md").is_file()
    assert (installed / "hooks/guard-xcodebuild-scope.sh").is_file()
    assert not [path for path in installed.rglob("*") if path.is_symlink()]
