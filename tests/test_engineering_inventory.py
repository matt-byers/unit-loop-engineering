import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
CLAUDE_AGENTS_DIR = REPO_ROOT / "agents"
LOOP_DOCS_DIR = SKILLS_DIR / "unit-loop" / "references" / "shared"
UNIT_LOOP_DIR = SKILLS_DIR / "unit-loop"

INCLUDED_SKILLS = [
    "unit-loop",
    "implement",
    "multi-review",
    "review-standards",
    "compound-learnings",
    "human-verify",
    "spec-plan",
    "unit-loop-setup",
]

REQUIRED_UNIT_LOOP_REFERENCES = [
    "parallel-waves.md",
    "stage-routing.md",
    "stage-1-tdd.md",
    "stage-2-implement.md",
    "stage-3-test-gate.md",
    "stage-4-code-review.md",
]

REQUIRED_LOOP_DOCS = [
    "agent-dispatch.md",
    "checkpointing.md",
    "verification-flow.md",
    "templates/verify.md",
]

REQUIRED_AGENTS = [
    "plan-review/feasibility-validator.md",
    "plan-review/gap-detector.md",
    "plan-review/utility-pattern-auditor.md",
    "review/architecture.md",
    "review/patterns-utilities.md",
    "review/performance-database.md",
    "review/security.md",
    "review/simplicity.md",
    "review/type-safety.md",
    "verification/test-runner.md",
    "verification/api-prober.md",
]

OUT_OF_SCOPE_NAMES = [
    "testagent",
    "agent-behavior-review",
]

REPO_ROOT_TOKEN = re.compile(r"repo-root:([\w./-]+)")
AGENT_TOKEN = re.compile(r"(?<![\w<-])agent:([a-z][a-z0-9-]+)")
RELATIVE_REFERENCE = re.compile(r"(?<!/)references/[\w.-]+\.md")


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        pytest.fail(f"{path.relative_to(REPO_ROOT)} does not start with YAML frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        pytest.fail(f"{path.relative_to(REPO_ROOT)} frontmatter is not closed with '---'")
    block = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as error:
        pytest.fail(f"{path.relative_to(REPO_ROOT)} frontmatter does not parse as YAML: {error}")
    if not isinstance(data, dict):
        pytest.fail(f"{path.relative_to(REPO_ROOT)} frontmatter is not a YAML mapping")
    return data


def markdown_files(root):
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.md"))


def scanned_markdown_files():
    return markdown_files(SKILLS_DIR) + markdown_files(LOOP_DOCS_DIR)


def claude_agent_files():
    if not CLAUDE_AGENTS_DIR.is_dir():
        return []
    return sorted(CLAUDE_AGENTS_DIR.rglob("*.md"))


class TestIncludedSkills:
    @pytest.mark.parametrize("skill", INCLUDED_SKILLS)
    def test_skill_md_exists(self, skill):
        path = SKILLS_DIR / skill / "SKILL.md"
        assert path.is_file(), f"missing skill file: {path.relative_to(REPO_ROOT)}"

    @pytest.mark.parametrize("skill", INCLUDED_SKILLS)
    def test_skill_frontmatter_has_name_and_description(self, skill):
        path = SKILLS_DIR / skill / "SKILL.md"
        if not path.is_file():
            pytest.fail(f"missing skill file: {path.relative_to(REPO_ROOT)}")
        frontmatter = parse_frontmatter(path)
        assert frontmatter.get("name"), f"{skill} SKILL.md frontmatter lacks name:"
        assert frontmatter.get("description"), f"{skill} SKILL.md frontmatter lacks description:"


class TestRequiredReferenceFiles:
    @pytest.mark.parametrize("reference", REQUIRED_UNIT_LOOP_REFERENCES)
    def test_unit_loop_reference_exists(self, reference):
        path = UNIT_LOOP_DIR / "references" / reference
        assert path.is_file(), f"missing unit-loop reference: {path.relative_to(REPO_ROOT)}"

    def test_review_standards_issue_patterns_exists(self):
        path = SKILLS_DIR / "review-standards" / "references" / "issue-patterns.md"
        assert path.is_file(), f"missing reference: {path.relative_to(REPO_ROOT)}"


class TestLoopDocs:
    @pytest.mark.parametrize("doc", REQUIRED_LOOP_DOCS)
    def test_loop_doc_exists(self, doc):
        path = LOOP_DOCS_DIR / doc
        assert path.is_file(), f"missing loop doc: {path.relative_to(REPO_ROOT)}"


class TestReferenceResolution:
    def test_repo_root_tokens_resolve(self):
        unresolved = []
        for path in scanned_markdown_files():
            text = path.read_text(encoding="utf-8")
            for token in REPO_ROOT_TOKEN.findall(text):
                if not (REPO_ROOT / token).exists():
                    unresolved.append((str(path.relative_to(REPO_ROOT)), token))
        assert not unresolved, f"repo-root tokens do not resolve: {unresolved}"

    def test_agent_tokens_resolve_to_one_native_agent(self):
        unresolved = []
        for path in scanned_markdown_files():
            text = path.read_text(encoding="utf-8")
            for name in AGENT_TOKEN.findall(text):
                claude_matches = (
                    list(CLAUDE_AGENTS_DIR.rglob(f"{name}.md")) if CLAUDE_AGENTS_DIR.is_dir() else []
                )
                if len(claude_matches) != 1:
                    unresolved.append(
                        (
                            str(path.relative_to(REPO_ROOT)),
                            name,
                            len(claude_matches),
                        )
                    )
        assert not unresolved, (
            "agent tokens without exactly one native Claude agent "
            f"(file, agent, claude_count): {unresolved}"
        )

    def test_unit_loop_skill_relative_references_resolve(self):
        skill_md = UNIT_LOOP_DIR / "SKILL.md"
        if not skill_md.is_file():
            pytest.fail(f"missing skill file: {skill_md.relative_to(REPO_ROOT)}")
        text = skill_md.read_text(encoding="utf-8")
        unresolved = [
            reference
            for reference in RELATIVE_REFERENCE.findall(text)
            if not (UNIT_LOOP_DIR / reference).is_file()
        ]
        assert not unresolved, f"unit-loop SKILL.md references do not resolve: {unresolved}"


class TestNativeAgentInventory:
    def test_no_duplicate_claude_agent_stems(self):
        stems = [path.stem for path in claude_agent_files()]
        duplicates = sorted({stem for stem in stems if stems.count(stem) > 1})
        assert not duplicates, f"duplicate Claude agent stems: {duplicates}"


class TestClaudeAgentFrontmatter:
    def test_agents_have_name_and_description_matching_stem(self):
        problems = []
        for path in claude_agent_files():
            frontmatter = parse_frontmatter(path)
            relative = str(path.relative_to(REPO_ROOT))
            if not frontmatter.get("name"):
                problems.append((relative, "missing name"))
            elif frontmatter["name"] != path.stem:
                problems.append((relative, f"name {frontmatter['name']!r} != stem {path.stem!r}"))
            if not frontmatter.get("description"):
                problems.append((relative, "missing description"))
        assert not problems, f"Claude agent frontmatter problems: {problems}"


class TestRequiredAgents:
    @pytest.mark.parametrize("agent", REQUIRED_AGENTS)
    def test_required_claude_agent_exists(self, agent):
        path = CLAUDE_AGENTS_DIR / agent
        assert path.is_file(), f"missing required agent: {path.relative_to(REPO_ROOT)}"

class TestScopeExclusions:
    @pytest.mark.parametrize("name", OUT_OF_SCOPE_NAMES)
    def test_no_out_of_scope_path_segments(self, name):
        violations = []
        for root in (SKILLS_DIR, CLAUDE_AGENTS_DIR):
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                relative = path.relative_to(REPO_ROOT)
                segments = set(relative.parts) | {Path(part).stem for part in relative.parts}
                if name in segments:
                    violations.append(str(relative))
        assert not violations, f"out-of-scope name {name!r} present in inventory paths: {violations}"
