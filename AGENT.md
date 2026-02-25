# Freeloader — Agent Context

> Read this file first. It provides everything needed to orient, design, and implement in this codebase.

---

## 1. Project Scan

**What it is:** `freeloader` is a CLI pipeline composer for indie developers (`fl` entrypoint).  
**Runtime:** Python ≥ 3.12. Package manager: `uv`. Entry: `src/freeloader/cli.py`.

### Top-level layout

| Path | Role |
|---|---|
| `src/freeloader/` | All application source code |
| `tests/` | Pytest test suite |
| `test_projects/` | Fixture projects used by integration tests |
| `docs/` | Documentation artifacts (not code) |
| `pyproject.toml` | Canonical dependency list and build config |
| `Makefile` | Common dev tasks |

### Source tree

| Package | Concern |
|---|---|
| `auth/` | Authentication with external service providers |
| `blocks/` | Reusable file/config block templates (per provider) |
| `hosts/` | Host scanning, registration, and lifecycle |
| `project/` | Core aggregate — project initialization, provisioning, teardown |
| `secrets/` | Encrypted secret storage and retrieval |
| `service_providers/` | Adapter registry for AWS, Coolify, Docker, Git, GitHub, GitLab |
| `shared/` | Cross-cutting utilities (CLI helpers, console, IO, runtime, Terraform, tech detection) |

### Block providers

`blocks/` is provider-keyed. Each provider subdirectory contains resource-type subdirectories with Jinja2 templates or static files — no Python logic lives there.

```
blocks/
  aws/ec2/
  coolify/{app,project,service}/
  docker/{dockerfile,dockerignore}/
  git/{gitignore,local_repo}/
  github/{actions_ci,repo}/
  gitlab/registry/
```

### Service provider adapters

`service_providers/` follows the registry pattern: `base.py` defines the abstract interface, `registry.py` owns the adapter map, `facade.py` is the single entry point callers use. Each provider subdirectory (`aws/`, `coolify/`, etc.) contains exactly one `provider.py`.

---

## 2. Feature Anatomy

Every feature follows this layout. Deviations are bugs.

```
feature/
  domain.py          # Aggregate + nested events (eventsourcing) — stateful features only
  application.py     # Application service — wraps aggregate, persists via save()
  usecases/
    __init__.py      # re-exports every public usecase function
    <verb_phrase>.py # one function per file; filename == function name
    _storage.py      # shared setup helpers (underscore = internal, not a usecase)
  ports/
    cli.py           # Click group + commands — terminal port
    interface.py     # Plain functions — machine port for other features
  storage/           # only when feature owns non-event-sourced persistent state
    models.py
    vault.py / session.py / ...
```

### Event sourcing (stateful features)

- Aggregate subclasses `Aggregate` from `eventsourcing.domain`.
- Each state change is a nested `Aggregate.Event` or `Aggregate.Created`.
- Event names: `PascalCase` past-tense verb phrase (`Registered`, `TechStackDetected`, `Discarded`).
- `application.py` exposes one method per command; never bypasses the aggregate.

### Usecases

- One `def` per file; filename is the exact snake_case copy of the function name.
- Functions are imperative verb phrases: `list_all`, `write_secret`, `remove_secret`.
- Usecases call ports/storage — never call other usecases.
- `__init__.py` re-exports every public usecase; callers import from the package, not the file.

### `ports/cli.py` — terminal port

- One `@click.group(name="<feature>")` per feature.
- Command names: short imperative verbs (`ls`, `add`, `remove`, `reveal`).
- Commands call **usecases only** — no business logic inside.
- All prompts and `click.echo` calls stay inside this file.
- Decorated with `@handle_cli_error`.

### `ports/interface.py` — machine port

- Exposes the minimal surface other features strictly need.
- All parameters and return types are primitives (`str`, `list[str]`, `dict[str, str]`, `bool`).
- No Click, no output, no side-effects beyond storage reads/writes.

### Concrete example — `secrets` feature

**Usecases**

| File | Function |
|---|---|
| `list_all.py` | `list_all(namespace)` |
| `reveal_secrets.py` | `reveal_secrets(namespace)` |
| `write_secret.py` | `write_secret(key, value, namespace)` |
| `remove_secret.py` | `remove_secret(key, namespace)` |
| `_storage.py` | `load_storage()`, `ensure_unlocked(storage)` |

**`ports/cli.py` commands**

| Command | Option |
|---|---|
| `ls` | `--namespace / -n` |
| `reveal` | `--namespace / -n` |
| `add KEY` | `--namespace / -n` |
| `remove KEY` | `--namespace / -n` |

**`ports/interface.py` functions**

| Function | Parameters | Return |
|---|---|---|
| `read_secrets` | `namespace: str, secret_names: list[str]` | `dict[str, str]` |
| `write_secret` | `namespace: str, secret_name: str, secret_value: str` | `None` |
| `has_secrets` | `namespace: str, secret_names: list[str]` | `bool` |

### Naming conventions

| Symbol | Convention | Example |
|---|---|---|
| Feature package | `snake_case` noun | `secrets`, `project`, `hosts` |
| Aggregate | `PascalCase` noun | `Project` |
| Aggregate event | `PascalCase` past-tense | `Registered`, `TechStackDetected` |
| Application class | `{Feature}Application` | `ProjectApplication` |
| Usecase file | `snake_case` verb phrase | `write_secret.py` |
| Usecase function | identical to filename | `def write_secret(...)` |
| Internal helper | `_snake_case` prefix | `_storage.py` |
| CLI group name | `snake_case` feature noun | `"secrets"` |
| CLI command name | short imperative verb | `ls`, `add`, `remove`, `reveal` |
| Interface function | `snake_case`, caller-semantic | `read_secrets`, `has_secrets` |

---

## 3. Design Algorithm

Apply these steps in order before writing any module.

### Step 1 — Package boundary (SRP + ISP)

- Define the minimal public API: expose only what callers strictly need.
- Each package owns exactly one concern.
- Internal modules are private by convention; treat every package as a black box.

### Step 2 — Module placement (DRY + SSOT)

- Search the codebase for an existing solution before creating anything.
- If a responsibility is already solved, reuse or extend — never duplicate.
- One module orchestrates; others are pure logic units with no cross-calling.

### Step 3 — Cohesion check (KISS + YAGNI)

- Reject any abstraction not required by a concrete, current use case.
- Reject any interface method that has no immediate implementation.
- A module is cohesive when removing any of its symbols breaks a direct caller.

### Step 4 — Output format

- Output only: `class`, `def`, and `Protocol`/`ABC` signatures with `...` bodies.
- Structure: imports → protocols/ABCs → concrete classes → standalone functions.
- No comments, no docstrings, no inline explanations.

---

## 4. Coding Constraints

### Pre-flight (run before writing any code)

1. Read `pyproject.toml` — use only libraries already listed; match exact versions.
2. Search the codebase for an existing solution to the same problem.

### Output format

Code only. No comments, no docstrings, no explanations, no prose. Non-Python text is forbidden.

### Principles (enforced strictly)

| Principle | Rule |
|---|---|
| **DRY** | Every piece of logic has exactly one authoritative location. Refactor to a shared module — never copy. |
| **SSOT** | Constants, configuration, and shared state live in one place. Never mirror or re-derive values owned by another module. |
| **YAGNI** | Implement only what a current, concrete use case requires. No speculative parameters, no optional hooks, no future-proofing abstractions. |
| **KISS** | Prefer a flat function over a class hierarchy. Prefer a class over a framework. The simplest solution is correct. |
| **SRP** | Each class/module has one reason to change. |
| **OCP** | Extend behavior via new implementations, not by modifying existing ones. |
| **LSP** | Subtypes must be fully substitutable for their base type. |
| **ISP** | Expose narrow interfaces; callers must not depend on methods they do not use. |
| **DIP** | High-level modules depend on abstractions (`Protocol`/`ABC`), never on concrete implementations. |

### Typing

`Any` is forbidden. Use concrete types, `TypeVar`, `Generic`, `Protocol`, or `TypeAlias`.

### Validation

Input is validated once, at the system boundary. Downstream code assumes valid data — no guard clauses, no re-checks.

### Tooling

`uv` for all package management and script execution.
