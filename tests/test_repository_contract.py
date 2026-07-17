import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"

FORBIDDEN_PRODUCT_STRINGS = [
    "testsim",
    "testapp",
]

OUT_OF_SCOPE_SKILLS = [
    "agent-self-improvement",
    "copilot-engineering",
    "eval-agent",
    "eval-compound-learnings",
    "agent-behavior-review",
    "ui-eval",
    "triage-bug",
    "diagnose",
]

MARKETPLACE_PUBLISH_PATTERNS = [
    "npm publish",
    "pip upload",
    "twine upload",
    "gh release create",
    "marketplace publish",
    "claude plugin publish",
    "codex plugin publish",
]

GLOBAL_CONFIG_PATTERNS = [
    "~/.claude",
    "~/.codex",
    "$HOME/.claude",
    "$HOME/.codex",
    "${HOME}/.claude",
    "${HOME}/.codex",
]

CLAUDE_ONLY_FORBIDDEN_PATHS = [
    ".codex",
    ".codex-plugin",
    "plugin",
    "scripts/agent-config",
    "scripts/packaging",
]


PRUNED_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}


def iter_repo_files(exclude_tests=False):
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in PRUNED_DIR_NAMES]
        if Path(dirpath) == REPO_ROOT / "plugin" and "build" in dirnames:
            dirnames.remove("build")
        for name in filenames:
            path = Path(dirpath) / name
            if exclude_tests and TESTS_DIR in path.parents:
                continue
            yield path


def read_text_or_none(path):
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def iter_text_files(exclude_tests=False):
    for path in iter_repo_files(exclude_tests):
        text = read_text_or_none(path)
        if text is not None:
            yield path, text


class TestRepositorySkeleton:
    def test_readme_exists(self):
        assert (REPO_ROOT / "README.md").is_file(), "README.md is missing"

    def test_gitignore_exists(self):
        assert (REPO_ROOT / ".gitignore").is_file(), ".gitignore is missing"

    def test_mit_license_and_third_party_notice_exist(self):
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        notices_text = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        assert license_text.startswith("MIT License\n")
        assert "Copyright (c) 2026 Matt Byers" in license_text
        assert "https://github.com/ryan-relevanceai/unitwork" in notices_text
        assert "Copyright (c) 2026" in notices_text
        assert "Permission is hereby granted" in notices_text

    def test_tests_directory_exists(self):
        assert TESTS_DIR.is_dir(), "tests/ directory is missing"


class TestScopeBoundary:
    def test_repo_tree_excludes_out_of_scope_skills(self):
        violations = []
        for path in iter_repo_files(exclude_tests=True):
            relative = path.relative_to(REPO_ROOT)
            for skill in OUT_OF_SCOPE_SKILLS:
                if skill in relative.parts or skill in {p.stem for p in map(Path, relative.parts)}:
                    violations.append((skill, str(relative)))
        assert not violations, f"out-of-scope skill files present in the repo tree: {violations}"

    @pytest.mark.parametrize("relative", CLAUDE_ONLY_FORBIDDEN_PATHS)
    def test_repo_has_no_codex_or_generated_packaging_surface(self, relative):
        assert not (REPO_ROOT / relative).exists(), f"Claude-only repo still contains {relative}"

    def test_repository_contains_no_symlinks(self):
        symlinks = [
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("*")
            if ".git" not in path.parts and path.is_symlink()
        ]
        assert not symlinks, f"skill repository must contain physical files only: {symlinks}"


class TestForbiddenProductStrings:
    @pytest.mark.parametrize("forbidden", FORBIDDEN_PRODUCT_STRINGS)
    def test_reusable_content_has_no_product_strings(self, forbidden):
        offenders = []
        for path, text in iter_text_files(exclude_tests=True):
            if forbidden in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        assert not offenders, f"forbidden product string {forbidden!r} found in: {offenders}"


class TestNoGlobalMutationOrPublication:
    @staticmethod
    def scripts_files():
        scripts_dir = REPO_ROOT / "scripts"
        return [(p, t) for p, t in iter_text_files() if scripts_dir in p.parents]

    @pytest.mark.parametrize("pattern", MARKETPLACE_PUBLISH_PATTERNS)
    def test_scripts_do_not_publish_to_marketplaces(self, pattern):
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path, text in self.scripts_files()
            if pattern in text
        ]
        assert not offenders, f"marketplace publication command {pattern!r} found in: {offenders}"

    @pytest.mark.parametrize("pattern", GLOBAL_CONFIG_PATTERNS)
    def test_scripts_do_not_mutate_global_user_config(self, pattern):
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path, text in self.scripts_files()
            if pattern in text
        ]
        assert not offenders, f"global user config path {pattern!r} found in scripts: {offenders}"
