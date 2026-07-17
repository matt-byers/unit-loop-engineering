---
name: unit-loop-setup
description: Configure an installed unit-loop skillset to use a project's existing architecture documents. Use immediately after installation or when those documents move.
---

# Unit Loop Setup

Connect the installed, project-owned unit-loop skills and agents to the repository's existing architecture documents.

## Boundaries

- Work from the consuming repository root and edit only installed files under `.claude/skills/` and `.claude/agents/`.
- Use existing architecture documents only. Never create or generate an architecture document.
- Never discover, configure, or change build, test, lint, run, or verification commands.
- Never create a mapping file, adapter, manifest, or other configuration format. Put exact document paths directly into the skills and agents that consume them.
- Do not edit application code, tests, hooks, repository manuals, or the architecture documents themselves.

## 1. Ask First

Ask the user which existing architecture documents govern the repository. Request a repository-relative path and the area governed by each document, such as frontend, backend, mobile, data, infrastructure, or a cross-cutting system.

Do not scan before the user has had this opportunity. When the user supplies paths:

1. verify that every path exists inside the repository and is a regular file;
2. read enough of each document to confirm that its stated area is credible;
3. normalize paths to repository-relative form; and
4. show the resulting area-to-path mapping and ask the user to confirm or correct it.

Do not edit anything until the user confirms the mapping.

## 2. Fallback Scan

Only when the user cannot provide the document paths, scan the repository for likely existing architecture sources.

1. Read repository manuals such as `CLAUDE.md`, `AGENTS.md`, and the root README for explicit architecture links.
2. Use `rg --files` to find likely files under documentation directories and filenames containing terms such as `architecture`, `design`, `decisions`, `system`, or `technical`.
3. Inspect candidate titles and relevant sections. Use the repository's actual source layout only to understand which areas need governing documents.
4. Present the credible candidates, the area each appears to govern, and the evidence for the match.
5. Ask the user to confirm or correct every proposed area-to-path match.

Do not edit anything until the user confirms the mapping. If the scan finds no credible existing document, ask the user to provide its path later and stop without editing. Do not offer to create a default.

## 3. Update Installed Sources

After confirmation, inspect `.claude/skills/**/*.md` and `.claude/agents/**/*.md` for instructions that read, apply, review against, or update project architecture guidance.

- Replace ambiguous project-architecture references with the exact confirmed repository-relative paths relevant to that file's role.
- Update every workflow consumer that needs the mapping, including planning, implementation, review, verification, and compounding instructions where applicable.
- Update agent roles whose scope depends on project architecture, especially architecture and area-specific reviewers.
- Keep generic bundled stack guidance generic. Project documents override stack guidance but do not replace it.
- If a file applies to several confirmed areas, add a short in-file list of those exact paths and state when each is used.
- Preserve existing behavior and wording outside the architecture-source references.
- Do not add indirection: the installed Markdown files themselves are the source of truth.

## 4. Verify

Before finishing:

1. verify every inserted path still resolves to a regular file inside the repository;
2. search the edited skills and agents for each exact path and confirm every relevant workflow stage can reach the correct document;
3. inspect the diff to confirm no commands, adapters, architecture documents, or non-`.claude` files changed; and
4. report the confirmed area-to-path mapping and changed files.
