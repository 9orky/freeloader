# Architecture Design Guide

## Design Algorithm

When asked to design code, apply these steps in order:

### 1. Package boundary (SOLID — SRP + ISP)
- Define the minimal public API: only expose what callers strictly need.
- Enforce clear ownership — each package owns exactly one concern.
- Treat every package as a black box; internal modules are private by convention.

### 2. Module placement (DRY + SSOT)
- Before creating any module, search the codebase for existing solutions to the same concern.
- If a responsibility is already solved elsewhere, reuse or extend — never duplicate.
- One module orchestrates; others are pure logic units with no cross-calling.

### 3. Module cohesion check (KISS + YAGNI)
- Reject any abstraction that is not required by a concrete, current use case.
- Reject any interface method that has no immediate implementation.
- A module is cohesive when removing any of its symbols breaks a direct caller.

### 4. Output format (non-negotiable)
- Output only: `class`, `def`, and `Protocol`/`ABC` signatures with `...` bodies.
- No comments, no docstrings, no inline explanations, no examples.
- Every module follows identical structure: imports → protocols/ABCs → concrete classes → standalone functions.
- No summaries, no prose outside of code blocks.