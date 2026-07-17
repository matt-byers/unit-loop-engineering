import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
UNIT_LOOP_DIR = REPO_ROOT / "skills" / "unit-loop"
STACKS_DIR = UNIT_LOOP_DIR / "stacks"
SCHEMA_PATH = STACKS_DIR / "stack.schema.json"
REFERENCES_DIR = UNIT_LOOP_DIR / "references"
STACK_SELECTION = REFERENCES_DIR / "stack-selection.md"
SKILL_REGISTRY = REFERENCES_DIR / "third-party-skill-registry.md"
STAGE_ROUTING = REFERENCES_DIR / "stage-routing.md"
SKILLS_DIR = REPO_ROOT / "skills"

EXPECTED_STACKS = ["swift", "react", "vue", "fastapi", "node"]

SLOT_NAMES = {
    "test-scoped",
    "test-full",
    "lint",
    "typecheck",
    "build",
    "build-for-testing",
    "format",
    "snapshot",
    "ui",
    "api-smoke",
    "live-run",
    "perf",
}

PROJECT_ADAPTER_DOC = REFERENCES_DIR / "project-adapter.md"

REQUIRED_STACK_KEYS = {
    "name",
    "description",
    "detection",
    "adapter_slots",
    "gates",
    "routing",
    "third_party_skills",
    "docs",
    "missing_command_behavior",
}

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


def _string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _validate_detection(detection, errors):
    if not isinstance(detection, dict) or not isinstance(detection.get("markers"), list):
        errors.append("detection must be a mapping with a markers list")
        return
    if not detection["markers"]:
        errors.append("detection.markers must not be empty")
    for marker in detection["markers"]:
        if not isinstance(marker, dict):
            errors.append(f"detection marker must be a mapping: {marker!r}")
            continue
        if not ({"file", "glob", "manifest"} & marker.keys()):
            errors.append(f"detection marker needs file, glob, or manifest: {marker!r}")
        if "dependency" in marker and "manifest" not in marker:
            errors.append(f"detection marker dependency requires a manifest: {marker!r}")
        for value in marker.values():
            if not isinstance(value, str) or not value:
                errors.append(f"detection marker values must be non-empty strings: {marker!r}")


def _validate_slot_list(values, field, errors):
    if not _string_list(values):
        errors.append(f"{field} must be a list of strings")
        return []
    for value in values:
        if value not in SLOT_NAMES:
            if " " in value or "/" in value:
                errors.append(
                    f"{field} entry {value!r} looks like a concrete command; "
                    "stack packs declare generic slot names and project adapters own commands"
                )
            else:
                errors.append(f"{field} entry {value!r} is not a generic adapter slot name")
    return values


def _validate_adapter_slots(adapter_slots, errors):
    if not isinstance(adapter_slots, dict):
        errors.append("adapter_slots must be a mapping with required and optional lists")
        return set()
    declared = set()
    required = adapter_slots.get("required")
    if not required:
        errors.append("adapter_slots.required must be a non-empty list")
    else:
        declared.update(_validate_slot_list(required, "adapter_slots.required", errors))
    declared.update(
        _validate_slot_list(adapter_slots.get("optional", []), "adapter_slots.optional", errors)
    )
    return declared


def _validate_gates(gates, declared_slots, errors):
    if not isinstance(gates, dict):
        errors.append("gates must be a mapping with deterministic and optional lists")
        return
    deterministic = gates.get("deterministic")
    if not deterministic or not _string_list(deterministic):
        errors.append("gates.deterministic must be a non-empty list of gate categories")
        return
    if not {"test-scoped", "test-full"} <= set(deterministic):
        errors.append("gates.deterministic must include the test-scoped and test-full gates")
    for gate in deterministic + list(gates.get("optional", [])):
        _validate_slot_list([gate], "gates", errors)
        if gate in SLOT_NAMES and gate not in declared_slots:
            errors.append(f"gate {gate!r} is not a declared adapter slot")


def _validate_routing(routing, errors):
    if not isinstance(routing, dict):
        errors.append("routing must be a mapping with review and verification lists")
        return
    for field in ("review", "verification"):
        entries = routing.get(field)
        if not entries or not _string_list(entries):
            errors.append(f"routing.{field} must be a non-empty list of strings")
            continue
        for entry in entries:
            if not (entry.startswith("agent:") or entry.startswith("/")):
                errors.append(
                    f"routing.{field} entry {entry!r} must reference agent:<name> or /<skill>"
                )


def _validate_third_party_skills(skills, errors):
    if not isinstance(skills, list) or not skills:
        errors.append("third_party_skills must be a non-empty list of recommendations")
        return
    for skill in skills:
        if not isinstance(skill, dict):
            errors.append(f"third_party_skills entry must be a mapping: {skill!r}")
            continue
        for field in ("name", "purpose", "when_missing"):
            if not isinstance(skill.get(field), str) or not skill.get(field):
                errors.append(
                    f"third_party_skills entry {skill.get('name', skill)!r} "
                    f"needs a non-empty {field} (missing skills produce setup guidance, "
                    "never a load failure)"
                )


def _validate_docs(docs, errors):
    if not _string_list(docs) or not docs:
        errors.append("docs must be a non-empty list of relative markdown paths")
        return
    for doc in docs:
        if Path(doc).is_absolute() or not doc.endswith(".md"):
            errors.append(f"docs entry {doc!r} must be a relative .md path")


def _validate_missing_command_behavior(behavior, errors):
    if not isinstance(behavior, dict):
        errors.append("missing_command_behavior must be a mapping")
        return
    for field in ("required_slot", "optional_slot"):
        if not isinstance(behavior.get(field), str) or not behavior.get(field):
            errors.append(f"missing_command_behavior.{field} must be a non-empty string")


def validate_stack(data):
    errors = []
    if not isinstance(data, dict):
        return ["stack definition must be a mapping"]
    missing = REQUIRED_STACK_KEYS - data.keys()
    if missing:
        errors.append(f"missing required keys: {sorted(missing)}")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_PATTERN.match(name or ""):
        errors.append(f"name must match {NAME_PATTERN.pattern}: {name!r}")
    if not isinstance(data.get("description"), str) or not data.get("description"):
        errors.append("description must be a non-empty string")
    if "detection" in data:
        _validate_detection(data["detection"], errors)
    declared_slots = set()
    if "adapter_slots" in data:
        declared_slots = _validate_adapter_slots(data["adapter_slots"], errors)
    if "gates" in data:
        _validate_gates(data["gates"], declared_slots, errors)
    if "routing" in data:
        _validate_routing(data["routing"], errors)
    if "third_party_skills" in data:
        _validate_third_party_skills(data["third_party_skills"], errors)
    if "docs" in data:
        _validate_docs(data["docs"], errors)
    if "missing_command_behavior" in data:
        _validate_missing_command_behavior(data["missing_command_behavior"], errors)
    if "fallback" in data and not isinstance(data["fallback"], bool):
        errors.append("fallback must be a boolean")
    return errors


def load_stack(stack_name):
    path = STACKS_DIR / stack_name / "stack.yaml"
    if not path.is_file():
        pytest.fail(f"missing stack definition: {path.relative_to(REPO_ROOT)}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestStackLayout:
    def test_schema_file_exists_and_parses(self):
        assert SCHEMA_PATH.is_file(), "stacks/stack.schema.json is missing"
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_stack_pack_files_exist(self, stack_name):
        stack_dir = STACKS_DIR / stack_name
        for filename in ("stack.yaml", "architecture.md", "verification.md"):
            assert (stack_dir / filename).is_file(), f"missing {stack_name}/{filename}"

    def test_stack_selection_reference_exists(self):
        assert STACK_SELECTION.is_file(), "references/stack-selection.md is missing"

    def test_skill_registry_reference_exists(self):
        assert SKILL_REGISTRY.is_file(), "references/third-party-skill-registry.md is missing"


class TestSchemaValidatorAgreement:
    def test_schema_required_keys_match_validator(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert set(schema.get("required", [])) == REQUIRED_STACK_KEYS

    def test_schema_slot_vocabulary_matches_validator(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert set(schema["$defs"]["slot"]["enum"]) == SLOT_NAMES

    def test_schema_declares_optional_fallback_boolean(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        fallback = schema["properties"].get("fallback")
        assert isinstance(fallback, dict) and fallback.get("type") == "boolean"
        assert "fallback" not in schema.get("required", [])

    def test_project_adapter_doc_slot_table_matches_schema_enum(self):
        assert PROJECT_ADAPTER_DOC.is_file(), "references/project-adapter.md is missing"
        text = PROJECT_ADAPTER_DOC.read_text(encoding="utf-8")
        documented = re.findall(r"^\| `([a-z-]+)` \|", text, flags=re.MULTILINE)
        assert len(documented) == len(set(documented)), "duplicate slot rows in project-adapter.md"
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        assert set(documented) == set(schema["$defs"]["slot"]["enum"]), (
            "project-adapter.md slot table drifted from the stack.schema.json slot enum"
        )


class TestStackValidation:
    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_stack_validates_against_schema_rules(self, stack_name):
        errors = validate_stack(load_stack(stack_name))
        assert not errors, f"{stack_name} stack invalid: {errors}"

    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_stack_name_matches_directory(self, stack_name):
        assert load_stack(stack_name)["name"] == stack_name

    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_stack_docs_resolve_inside_stack_pack(self, stack_name):
        data = load_stack(stack_name)
        stack_dir = STACKS_DIR / stack_name
        for doc in data["docs"]:
            assert (stack_dir / doc).is_file(), f"{stack_name} docs entry does not resolve: {doc}"


class TestDetectionHints:
    def _markers(self, stack_name):
        return load_stack(stack_name)["detection"]["markers"]

    def test_swift_detects_package_and_xcode_projects(self):
        markers = self._markers("swift")
        files = {m.get("file") for m in markers}
        globs = {m.get("glob") for m in markers}
        assert "Package.swift" in files
        assert any("xcodeproj" in (g or "") for g in globs)

    def test_react_detects_package_json_with_react_dependency(self):
        markers = self._markers("react")
        assert any(
            m.get("manifest") == "package.json" and m.get("dependency") == "react"
            for m in markers
        )

    def test_vue_detects_vue_dependency_and_vue_vite_plugin(self):
        markers = self._markers("vue")
        assert any(
            m.get("manifest") == "package.json" and m.get("dependency") == "vue"
            for m in markers
        )
        assert any(m.get("dependency") == "@vitejs/plugin-vue" for m in markers)
        assert not any(
            m.get("dependency") == "vite" for m in markers
        ), "bare vite is framework-agnostic and must not mark the vue stack"

    def test_fastapi_detects_pyproject_with_fastapi_dependency(self):
        markers = self._markers("fastapi")
        assert any(
            m.get("manifest") in ("pyproject.toml", "requirements.txt")
            and m.get("dependency") == "fastapi"
            for m in markers
        )

    def test_node_detects_package_json(self):
        markers = self._markers("node")
        assert any(m.get("file") == "package.json" or m.get("manifest") == "package.json" for m in markers)

    def test_node_is_the_only_declared_fallback_stack(self):
        assert load_stack("node").get("fallback") is True
        for stack_name in EXPECTED_STACKS:
            if stack_name != "node":
                assert not load_stack(stack_name).get("fallback", False)


class TestGateCoverage:
    def test_swift_has_build_test_and_optional_ui_snapshot_gates(self):
        data = load_stack("swift")
        deterministic = set(data["gates"]["deterministic"])
        optional = set(data["gates"].get("optional", []))
        assert {"build", "test-scoped", "test-full"} <= deterministic
        assert {"snapshot", "ui"} <= optional | deterministic
        slots = set(data["adapter_slots"]["required"]) | set(
            data["adapter_slots"].get("optional", [])
        )
        assert "build-for-testing" in slots

    @pytest.mark.parametrize("stack_name", ["react", "vue"])
    def test_frontend_stacks_cover_core_slots(self, stack_name):
        data = load_stack(stack_name)
        slots = set(data["adapter_slots"]["required"]) | set(
            data["adapter_slots"].get("optional", [])
        )
        assert {"test-scoped", "test-full", "lint", "typecheck", "build"} <= slots

    @pytest.mark.parametrize("stack_name", ["fastapi", "node"])
    def test_backend_stacks_expose_api_smoke_slot(self, stack_name):
        data = load_stack(stack_name)
        slots = set(data["adapter_slots"]["required"]) | set(
            data["adapter_slots"].get("optional", [])
        )
        assert "api-smoke" in slots

    def test_fastapi_exposes_live_run_slot(self):
        data = load_stack("fastapi")
        slots = set(data["adapter_slots"]["required"]) | set(
            data["adapter_slots"].get("optional", [])
        )
        assert "live-run" in slots

    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_every_stack_recommends_third_party_skills(self, stack_name):
        skills = load_stack(stack_name)["third_party_skills"]
        assert skills, f"{stack_name} recommends no third-party skills"


class TestNegativeFixtures:
    @staticmethod
    def _valid_fixture():
        return {
            "name": "fixture",
            "description": "Fixture stack for negative validation tests.",
            "detection": {"markers": [{"file": "fixture.config"}]},
            "adapter_slots": {
                "required": ["test-scoped", "test-full", "build"],
                "optional": ["lint"],
            },
            "gates": {
                "deterministic": ["test-scoped", "test-full", "build"],
                "optional": ["lint"],
            },
            "routing": {"review": ["agent:architecture"], "verification": ["agent:test-runner"]},
            "third_party_skills": [
                {
                    "name": "example-skill",
                    "purpose": "Example guidance.",
                    "when_missing": "Install it from its upstream source, or continue without it.",
                }
            ],
            "docs": ["architecture.md"],
            "missing_command_behavior": {
                "required_slot": "Block the gate and ask the project to map the slot.",
                "optional_slot": "Skip the gate and record the skip in the unit result.",
            },
        }

    def test_valid_fixture_passes(self):
        assert validate_stack(self._valid_fixture()) == []

    def test_missing_gate_categories_rejected(self):
        fixture = self._valid_fixture()
        fixture["gates"] = {"deterministic": []}
        errors = validate_stack(fixture)
        assert any("deterministic" in error for error in errors)

    def test_absent_gates_key_rejected(self):
        fixture = self._valid_fixture()
        del fixture["gates"]
        errors = validate_stack(fixture)
        assert any("gates" in error for error in errors)

    def test_missing_third_party_skill_mapping_rejected(self):
        fixture = self._valid_fixture()
        fixture["third_party_skills"] = [{"name": "example-skill"}]
        errors = validate_stack(fixture)
        assert any("when_missing" in error for error in errors)

    def test_empty_third_party_skills_rejected(self):
        fixture = self._valid_fixture()
        fixture["third_party_skills"] = []
        errors = validate_stack(fixture)
        assert any("third_party_skills" in error for error in errors)

    def test_hardcoded_command_in_slots_rejected(self):
        fixture = self._valid_fixture()
        fixture["adapter_slots"]["required"] = ["bash scripts/product-test.sh"]
        errors = validate_stack(fixture)
        assert any("concrete command" in error for error in errors)

    def test_hardcoded_command_in_gates_rejected(self):
        fixture = self._valid_fixture()
        fixture["gates"]["deterministic"] = ["test-scoped", "test-full", "npm run product:check"]
        errors = validate_stack(fixture)
        assert any("concrete command" in error for error in errors)

    def test_non_boolean_fallback_rejected(self):
        fixture = self._valid_fixture()
        fixture["fallback"] = "yes"
        errors = validate_stack(fixture)
        assert any("fallback" in error for error in errors)

    def test_unknown_slot_name_rejected(self):
        fixture = self._valid_fixture()
        fixture["adapter_slots"]["optional"] = ["telemetry"]
        errors = validate_stack(fixture)
        assert any("telemetry" in error for error in errors)


class TestStackSelectionReference:
    def _text(self):
        return STACK_SELECTION.read_text(encoding="utf-8")

    def test_covers_selection_inputs(self):
        text = self._text().lower()
        for phrase in ("unit context", "project marker", "adapter config"):
            assert phrase in text, f"stack-selection.md does not cover {phrase!r}"

    def test_explains_mixed_unit_gate_composition(self):
        text = self._text().lower()
        assert "compose" in text
        assert "frontend" in text and "backend" in text

    def test_extends_stage_routing_without_recreating_it(self):
        text = self._text()
        assert "stage-routing.md" in text
        assert "| Stage | Main skill or role |" not in text


class TestThirdPartySkillRegistry:
    def _registry_text(self):
        return SKILL_REGISTRY.read_text(encoding="utf-8")

    def _routing_skill_names(self):
        text = STAGE_ROUTING.read_text(encoding="utf-8")
        return sorted(set(re.findall(r"`/([a-z][a-z0-9-]*)`", text)))

    def _first_party_skills(self):
        return {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}

    def test_registry_covers_every_stage_routing_skill(self):
        registry = self._registry_text()
        missing = [
            name for name in self._routing_skill_names() if f"`/{name}`" not in registry
        ]
        assert not missing, f"stage-routing.md skills absent from registry: {missing}"

    def test_registry_separates_first_party_from_external(self):
        text = self._registry_text().lower()
        assert "first-party" in text
        assert "external" in text

    def test_registry_marks_first_party_skills_correctly(self):
        registry = self._registry_text()
        first_party_section = registry.lower().split("external")[0]
        for name in self._first_party_skills():
            assert f"`/{name}`" in registry, f"first-party skill /{name} missing from registry"
            assert f"`/{name}`" in first_party_section, (
                f"first-party skill /{name} not listed before the external section"
            )

    def test_registry_gives_setup_guidance_for_missing_skills(self):
        text = self._registry_text().lower()
        assert "setup" in text or "install" in text
        assert "load failure" in text or "never fail" in text or "does not fail" in text

    @pytest.mark.parametrize("stack_name", EXPECTED_STACKS)
    def test_stack_recommendations_resolve_in_registry(self, stack_name):
        registry = self._registry_text()
        for skill in load_stack(stack_name)["third_party_skills"]:
            assert f"`/{skill['name']}`" in registry, (
                f"{stack_name} recommends /{skill['name']} but the registry does not list it"
            )
