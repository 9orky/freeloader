# Freeloader Agent Guide

Read this file before making changes. Its job is to keep humans and LLMs aligned on how to work well in this repository.

## Project Facts

- `freeloader` is a Python 3.12+ CLI for composing infrastructure and deployment building blocks.
- The CLI entrypoint is `src/freeloader/cli.py` and is exposed as `fl`.
- Source code lives under `src/freeloader`; tests live under `tests`.
- Use `uv` for running commands and managing dependencies.
- Available validation tools include `pytest` and `ruff`.

## Primary Goal

Make the smallest correct change that fully solves the task, fits the existing architecture, and preserves current behavior unless the task explicitly requires a behavior change.

## How To Work

### 1. Read Before You Write

- Start from the user request, then inspect the affected modules, adjacent tests, and relevant interfaces.
- Search for an existing implementation before adding a new function, class, or module.
- Read `pyproject.toml` before introducing any dependency or tool usage.

### 2. Respect Existing Boundaries

- Keep concerns separated: CLI code wires commands, use cases orchestrate behavior, adapters talk to external systems, and shared modules hold cross-cutting utilities.
- Reuse existing abstractions when they fit. Do not add layers, protocols, or helper modules without a concrete need.
- Keep public APIs stable unless the requested change requires a breaking change.
- Do not move or rename files purely for taste.

### 3. Prefer Simple, Maintainable Code

- Favor clear names, direct control flow, and small units with one clear responsibility.
- Fix the root cause instead of layering workarounds on top.
- Avoid speculative hooks, extension points, configuration flags, and abstractions.
- Do not duplicate logic, constants, parsing rules, or schema knowledge.
- Use comments and docstrings only when they add real clarity.

### 4. Match Repo Conventions

- Follow the local style of nearby code instead of importing a new pattern.
- Keep typing explicit and useful. Avoid `Any` unless it is genuinely unavoidable.
- Prefer standard library and existing project dependencies over adding new packages.
- Preserve concise, testable functions and classes.

### 5. Handle Errors Deliberately

- Validate input at the correct boundary, not repeatedly at every layer.
- Raise or return actionable errors that help the caller recover or report the problem.
- Do not silently swallow exceptions unless the behavior is explicitly intentional and safe.

### 6. Test What You Change

- Add or update tests when behavior changes, a bug is fixed, or new branching logic is introduced.
- Tests validate behavior and architecture; they must not drive production structure or imports.
- Run targeted validation first, then broader checks if the change is cross-cutting.
- Use the repository toolchain: `uv run pytest` and `uv run ruff check`.
- If you cannot run validation, state that clearly.

### 7. Keep Changes Focused

- Do not mix unrelated refactors into a functional change.
- Avoid mass formatting or broad renames unless they are part of the requested work.
- Update documentation only when behavior, workflow, or public usage actually changed.

## Repo-Specific Guidance

- Treat block definitions and their Terraform assets as coupled units. If a block contract changes, keep `block.yml`, `main.tf`, and templates aligned.
- When changing orchestration or provisioning behavior, check both implementation flow and the tests that cover CLI or block resolution behavior.
- Prefer extending existing block, project, hosts, secrets, and shared packages over creating parallel structures.

## Output Expectations For LLMs

- Implement working code when the task calls for code. Do not respond with signatures, pseudocode, or design-only output unless explicitly asked.
- Be concise, but include assumptions, validation status, and any important risk that remains.
- If context is missing, inspect the repository before proposing a solution.
- Do not invent APIs, dependencies, or requirements that are not grounded in the codebase or the task.

## Quick Checklist

Before finishing, confirm all of the following:

1. The relevant code and tests were read first.
2. No existing implementation already solved the problem.
3. The change is minimal, coherent, and consistent with neighboring code.
4. Tests or validation were added or updated when needed.
5. Relevant checks were run, or the lack of validation was stated explicitly.
