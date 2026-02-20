# Coding Rules

## Output
Code only. No comments, no docstrings, no explanations, no prose. Non-Python text is forbidden.

## Pre-flight (do before writing any code)
1. Read `pyproject.toml` — use only libraries already listed; match exact versions.
2. Search the codebase for an existing solution to the same problem before creating anything new.

## Principles (enforced strictly)

### DRY — Don't Repeat Yourself
Every piece of logic has exactly one authoritative location. If equivalent logic exists elsewhere, refactor to a shared module — never copy.

### SSOT — Single Source of Truth
Constants, configuration, and shared state live in one place. When none exists, create it. Never mirror or re-derive values that are already owned by another module.

### YAGNI — You Aren't Gonna Need It
Implement only what a current, concrete use case requires. No speculative parameters, no optional extension hooks, no future-proofing abstractions.

### KISS — Keep It Simple
Prefer a flat function over a class hierarchy. Prefer a class over a framework. The simplest solution that satisfies the requirement is correct.

### SOLID
- **SRP:** Each class/module has one reason to change.
- **OCP:** Extend behavior via new implementations, not by modifying existing ones.
- **LSP:** Subtypes must be fully substitutable for their base type.
- **ISP:** Expose narrow interfaces; callers must not depend on methods they do not use.
- **DIP:** High-level modules depend on abstractions (Protocol/ABC), never on concrete implementations.

## Typing
`Any` is forbidden. Use concrete types, `TypeVar`, `Generic`, `Protocol`, or `TypeAlias`.

## Validation
Input is validated once, at the system boundary. Downstream code assumes valid data — no guard clauses, no re-checks.

## Tooling
`uv` for all package management and script execution.