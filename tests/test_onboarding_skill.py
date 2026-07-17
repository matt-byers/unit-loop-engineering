from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills/unit-loop-setup/SKILL.md"


def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_onboarding_asks_for_existing_docs_before_fallback_scan():
    text = skill_text()
    assert text.index("Ask First") < text.index("Fallback Scan")
    assert "Do not scan before the user has had this opportunity" in text


def test_fallback_scan_requires_confirmation_before_edits():
    text = skill_text().lower()
    assert "ask the user to confirm or correct every proposed area-to-path match" in text
    assert "do not edit anything until the user confirms the mapping" in text


def test_onboarding_edits_project_owned_sources_with_exact_paths():
    text = skill_text()
    assert ".claude/skills/**/*.md" in text
    assert ".claude/agents/**/*.md" in text
    assert "exact confirmed repository-relative paths" in text


def test_onboarding_does_not_generate_docs_or_configure_commands():
    text = skill_text()
    assert "Never create or generate an architecture document" in text
    assert "Never discover, configure, or change build, test, lint, run, or verification commands" in text
    assert "Never create a mapping file, adapter, manifest, or other configuration format" in text
    assert "stop without editing" in text
