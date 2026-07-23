from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DOC = REPO_ROOT / "skills" / "unit-loop" / "references" / "test-tooling-discovery.md"
SPEC_PLAN_SKILL = REPO_ROOT / "skills" / "spec-plan" / "SKILL.md"
STAGE_1_TDD = REPO_ROOT / "skills" / "unit-loop" / "references" / "stage-1-tdd.md"
PROJECT_ADAPTER = REPO_ROOT / "skills" / "unit-loop" / "references" / "project-adapter.md"


def test_discovery_doc_exists():
    assert DISCOVERY_DOC.is_file(), "references/test-tooling-discovery.md is missing"


def test_discovery_doc_is_stack_agnostic():
    text = DISCOVERY_DOC.read_text(encoding="utf-8").lower()
    assert "stack-agnostic" in text


def test_discovery_doc_covers_core_signals():
    text = DISCOVERY_DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "package.json",
        "ci workflow",
        "playwright.config",
        "cypress.config",
        "lockfile",
        "monorepo",
    ):
        assert phrase in text, f"test-tooling-discovery.md does not cover {phrase!r}"


def test_discovery_doc_does_not_prescribe_one_browser_tool():
    text = DISCOVERY_DOC.read_text(encoding="utf-8")
    assert "playwright.config" in text and "cypress.config" in text
    assert "do not introduce a second browser-testing tool" in text.lower()


def test_discovery_doc_covers_no_tooling_gap():
    text = DISCOVERY_DOC.read_text(encoding="utf-8").lower()
    assert "genuine gap" in text
    assert "not something to silently fill in" in text


def test_spec_plan_references_discovery_doc():
    text = SPEC_PLAN_SKILL.read_text(encoding="utf-8")
    assert "../unit-loop/references/test-tooling-discovery.md" in text
    referenced = (SPEC_PLAN_SKILL.parent / "../unit-loop/references/test-tooling-discovery.md").resolve()
    assert referenced == DISCOVERY_DOC


def test_stage_1_tdd_references_discovery_doc():
    text = STAGE_1_TDD.read_text(encoding="utf-8")
    assert "test-tooling-discovery.md" in text


def test_project_adapter_references_discovery_doc():
    text = PROJECT_ADAPTER.read_text(encoding="utf-8")
    assert "test-tooling-discovery.md" in text
