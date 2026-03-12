# Feature Architecture Guide

This document describes the layered architecture used for features in Freeloader
and explains how to create new features or migrate existing ones to this pattern.
The **secrets** feature is the canonical reference implementation.

---

## Overview

Every feature is a self-contained Python package under `src/freeloader/<feature>/`.
It owns all the code for one coherent capability—domain rules, use cases, storage,
machine API, and CLI—without spilling into other feature packages.

The package is divided into four layers. Each layer has a single responsibility and
is only allowed to depend on layers listed below it in the diagram.

```
ui/               ← Typer CLI commands + presentation view shapes
application/      ← use cases (commands and queries); no I/O
infrastructure/   ← concrete I/O + public facade for other features
domain/           ← pure business objects and abstract repository contracts
```

There is no root-level `models.py` and no `ports/` directory. Application functions
return domain entities or plain Python types directly. Presentation-only shapes
belong in `ui/views.py`. The machine API used by other features lives in
`infrastructure/interface.py` and is re-exported through the package `__init__.py`.

---

## Directory Layout

```
src/freeloader/<feature>/
│
├── __init__.py             # Re-exports: CLI app + public facade
│
├── domain/
│   ├── __init__.py         # Domain-level constants (e.g., DEFAULT_NAMESPACE)
│   ├── entity.py           # Core domain objects (frozen dataclasses)
│   ├── value_object.py     # Typed wrappers for primitive concepts
│   └── repository.py       # Abstract base classes for storage contracts
│
├── application/
│   ├── __init__.py         # (empty or module docstring only)
│   ├── commands.py         # Write operations: create, update, delete
│   └── queries.py          # Read operations: list, get, check
│
├── infrastructure/
│   ├── __init__.py         # Factory functions + re-export of public facade
│   ├── interface.py        # Public facade: the machine API for other features
│   └── <impl>.py           # Concrete repository implementations
│
└── ui/
    ├── __init__.py
    ├── cli.py              # Typer app: commands wired to the application module
    └── views.py            # Presentation-only shapes (optional)
```

---

## Layer Responsibilities

### `domain/`

The innermost layer. Has **no imports from the rest of the project**. It contains:

- **Entities** — frozen dataclasses representing core concepts. They carry identity
  and validate invariants in `__post_init__` when needed.
- **Value objects** — frozen dataclasses wrapping primitives to add type safety
  and semantics (e.g., `Password` instead of `str`).
- **Repository interfaces** — `abc.ABC` classes that declare what storage
  operations the feature needs. They reference only domain types. The concrete
  implementation is provided by the infrastructure layer.
- **Constants** — domain-scoped constants (e.g., default namespaces) placed in
  `__init__.py` so they are importable by all layers without a deeper path.

```
secrets example
───────────────
domain/__init__.py     → DEFAULT_NAMESPACE = "global"
domain/entity.py       → Secret(name, value, namespace)
domain/value_object.py → Password(value)
domain/repository.py   → abstract SecretRepository, abstract SessionRepository
```

### `application/`

The use-case layer. It orchestrates domain objects and storage, but **never talks
directly to files, network, or environment variables**. It does that indirectly
by calling the infrastructure factory to obtain a repository instance.

For pragmatic simplicity (no full DI framework), use-case functions call
`load_X_repository()` from the infrastructure `__init__.py` to get a concrete
repository. This keeps the layer thin while avoiding global state.

`commands.py` — mutating operations. Each function:
- Obtains a repository from the factory.
- Applies domain logic or delegates to the repository.
- Returns a domain entity, a plain type, or `None`. No DTO wrapper classes.

`queries.py` — read-only operations. Each function:
- Obtains a repository from the factory.
- Returns domain entities or plain Python types.

Neither file should contain I/O, rendering logic, or CLI types.

```
secrets example
───────────────
commands.py → write_secret(), write_secrets(), remove_secret(), has_secrets()
queries.py  → list_secrets(), reveal_secrets(), read_secrets()
```

### `infrastructure/`

The concrete I/O layer. It has two responsibilities:

**Storage implementations** — classes that extend the abstract repositories from
`domain/repository.py`. They may use stdlib I/O, third-party libraries, and
`freeloader.shared` utilities. Each implementation file contains one class that
inherits from the corresponding abstract repository and fully implements all
abstract methods.

**Public facade** (`interface.py`) — a single class that exposes the machine API
used by other features. The facade:
- Holds enough context to scope calls (e.g., a namespace string).
- Delegates every operation to the application layer (`commands` / `queries`).
- Normalizes inputs (e.g., strips and lowercases key names) so callers don't need
  to know about internal conventions.
- Provides `@classmethod` constructors for common configurations (e.g.,
  `for_default_namespace()`).

The facade contains no business logic of its own. It is a thin adapter between the
calling feature and this feature's application layer.

`__init__.py` exposes the factory function(s) that construct and wire together the
concrete implementations, and re-exports the public facade class so it is reachable
from the package root.

```
secrets example
───────────────
infrastructure/__init__.py  → load_secret_repository() wires SecretSession + SecretVault
                              re-exports Secrets
infrastructure/interface.py → Secrets(namespace)
                               .read_secrets(names)       delegates to queries.read_secrets()
                               .write_secret(name, value)  delegates to commands.write_secret()
                               .write_secrets(values)      delegates to commands.write_secrets()
                               .has_secrets(names)         delegates to commands.has_secrets()
                               .for_default_namespace()    classmethod constructor
infrastructure/vault.py     → SecretVault(SecretRepository) — encrypted file storage
infrastructure/session.py   → SecretSession(SessionRepository) — password cache file
```

### `ui/`

The CLI layer. It wires Typer commands to the application layer. It has **no
business logic** of its own—that goes in the application layer.

`cli.py` — defines a `typer.Typer()` instance named `<feature>_app`. Each command:
- Parses arguments and options using Typer's declarative API.
- Calls `application.<function>(...)` for all work.
- Uses `freeloader.shared.console` for output (`typer.echo`, `console.ok`, etc.).
- Is decorated with `@console.handle_errors` for consistent error formatting.

`cli.py` imports the **`application` module as a whole**, not its sub-modules
(`commands`, `queries`) individually. This makes the CLI easily testable: tests
monkeypatch `secrets_cli.application.write_secret` rather than patching a
sub-module path.

`views.py` — optional. Contains Pydantic dataclasses for data shapes that exist
only for structured rendering in the CLI (e.g., multi-column table rows). Do not
add views if plain text output suffices.

```
secrets example
───────────────
ui/cli.py    → secrets_app (Typer)
               ls, reveal, add, remove commands
               each calls application.list_secrets(), application.write_secret(), etc.
ui/views.py  → SecretView(name, value, namespace)
```

---

## `__init__.py`

The public face of the feature package. It re-exports:
- The CLI Typer instance (mounted in `freeloader/cli.py`).
- The public facade class from `infrastructure/interface.py` (used by other features).

Keep it minimal. Do not re-export internal types or implementation details.

```python
# secrets example
from .ui.cli import secrets_app
from .infrastructure import Secrets

__all__ = ["secrets_app", "Secrets"]
```

---

## Dependency Rules Summary

| Layer             | May import from                                              |
|-------------------|--------------------------------------------------------------|
| `domain/`         | stdlib only                                                  |
| `application/`    | `domain/`, `infrastructure/__init__` (factory only)         |
| `infrastructure/` | `domain/`, `application/` (facade only), `freeloader.shared`, third-party libs |
| `ui/`             | `application/` (as a module), `freeloader.shared.console`   |

**Forbidden:** `domain/` importing from any other layer. `application/` importing
from `ui/`. `ui/` importing directly from `domain/` or `infrastructure/`.

The one intentional exception: `infrastructure/interface.py` imports from
`application/` — this is the only approved upward reference, limited to the facade.

---

## Creating a New Feature

1. **Define the domain.** Start with `domain/entity.py` and `domain/value_object.py`.
   Write plain frozen dataclasses. No I/O, no imports from outside the domain.

2. **Define the repository contract.** In `domain/repository.py`, write an abstract
   base class for each storage boundary the feature needs. Declare only the methods
   the use cases will call.

3. **Write the use cases.** In `application/commands.py` and `application/queries.py`,
   implement the feature's behavior as plain functions. Each function obtains a
   repository from the infrastructure factory and performs exactly one action.
   Return domain entities or plain types — no wrapper DTOs.

4. **Implement the infrastructure.** In `infrastructure/<impl>.py`, write a concrete
   class that extends the abstract repository. In `infrastructure/__init__.py`, write
   the factory function(s) that construct and return the correct implementation.

5. **Expose the machine API.** In `infrastructure/interface.py`, write the facade
   class used by other features. One method per application function. Normalize
   inputs. Delegate to the application module. Re-export the facade from
   `infrastructure/__init__.py`.

6. **Wire the CLI.** In `ui/cli.py`, create the Typer app. Each command imports and
   calls `application.<function>()`. Decorate with `@console.handle_errors`. Add
   `ui/views.py` only if structured presentation shapes are needed.

7. **Wire the package.** In `__init__.py`, re-export the Typer app and the facade.
   Mount the Typer app in `freeloader/cli.py`.

8. **Test each layer independently.** Write tests in `tests/test_<feature>.py`.
   Unit-test application functions by monkeypatching the infrastructure factory.
   Unit-test the facade by monkeypatching application functions on the module object.
   Integration-test the CLI using `typer.testing.CliRunner`.

---

## Migrating an Existing Feature

Features using the older flat layout (`application.py`, `models.py`, `cli.py`,
`adapters/`, `usecases/`) should be migrated in this sequence to minimize breakage:

1. **Add `domain/`.** Extract entity dataclasses from `models.py` into
   `domain/entity.py`. Extract abstract repository contracts (if any exist in
   adapters) into `domain/repository.py`. Keep the rest of `models.py` intact
   for now.

2. **Rename `usecases/` to `application/`.** Split the use-case functions into
   `commands.py` (writes) and `queries.py` (reads). Adjust imports.

3. **Rename `adapters/` to `infrastructure/`.** For each adapter, identify which
   domain repository interface it satisfies. Make it explicitly extend the abstract
   class. Add a factory function in `infrastructure/__init__.py`.

4. **Remove `models.py`.** Move domain entities into `domain/`. Move any
   presentation shapes into `ui/views.py`. Delete the file. Update all imports.

5. **Add `infrastructure/interface.py`.** If other features import from this
   feature's `application.py` directly, introduce the facade here and redirect
   those imports to the package root (which re-exports it from `__init__.py`).

6. **Add `ui/` directory.** Move `cli.py` into `ui/cli.py`. Update it to import
   the `application` module as a whole, not `commands`/`queries` individually.
   Move any presentation models into `ui/views.py`.

7. **Update `__init__.py`.** Re-export only the Typer app and the facade.

8. **Update tests.** Patch `<feature>_cli.application.<function>` instead of
   internal sub-modules. Update import paths for any moved types.

Do this one feature at a time. Do not restructure multiple features in one commit.

---

## Testing Conventions

- **Application layer** — patch `infrastructure.__init__.load_X_repository` to inject
  a mock. Assert that the function calls the repository correctly and returns the
  expected value.
- **Infrastructure facade** — patch `application.<function>` directly on the module
  object. Test normalization logic (e.g., name stripping/lowercasing).
- **CLI** — use `typer.testing.CliRunner`. Patch `<module>.application.<function>` on
  the cli module to avoid touching real storage. Assert on exit code and captured
  output.
- **Infrastructure storage** — test with a real filesystem using `tmp_path` fixtures.
  Do not mock I/O inside these tests; exercise the actual file operations.

---

## Naming Conventions

| Concept              | Convention                                      | Example                  |
|----------------------|-------------------------------------------------|--------------------------|
| Feature package      | singular noun                                   | `secrets`, `project`     |
| Domain entity        | singular noun, PascalCase                       | `Secret`, `Project`      |
| Repository interface | `<Entity>Repository` (abstract)                 | `SecretRepository`       |
| Infrastructure class | `<Entity><Backend>` (concrete)                  | `SecretVault`            |
| Public facade        | feature noun, PascalCase                        | `Secrets`                |
| View shape (CLI)     | `<Entity>View`                                  | `SecretView`             |
| Typer instance       | `<feature>_app`                                 | `secrets_app`            |
| Factory function     | `load_<entity>_repository()`                    | `load_secret_repository` |
