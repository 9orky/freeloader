# Feature Structure

## Layers

```
feature/
  domain.py          # Aggregate + nested events (eventsourcing)
  application.py     # Application service — wraps aggregate, persists via save()
  usecases/
    __init__.py      # re-exports all usecase functions
    <verb_phrase>.py # one function per file, filename == function name
    _storage.py      # shared setup helpers (not a usecase)
  ports/
    cli.py           # Click group + commands — user-facing terminal port
    interface.py     # Plain functions — machine port for other features
  storage/           # only when feature owns persistent state (non-event-sourced)
    models.py
    vault.py / session.py / ...
```

## Event Sourcing (stateful features)

- Aggregate subclasses `Aggregate` from `eventsourcing.domain`.
- Each state change is a nested `Aggregate.Event` or `Aggregate.Created` class.
- Event names: `PascalCase`, past-tense verb phrase (`Registered`, `TechStackDetected`, `Discarded`).
- `application.py` exposes one method per command; never bypasses the aggregate.

## Usecases (all features)

- One `def` per file; filename is an exact snake_case copy of the function name.
- Functions are imperative verb phrases: `list_all`, `write_secret`, `remove_secret`, `reveal_secrets`.
- Usecases call ports/storage — never call other usecases.
- `_storage.py` (underscore prefix) is internal setup, not a usecase.
- `__init__.py` re-exports every public usecase function — callers import from the package.

## Ports

### `ports/cli.py` — terminal port

- One `@click.group(name="<feature>")` per feature.
- Command names: short imperative verbs (`ls`, `add`, `remove`, `reveal`).
- Commands call **usecases only** — no business logic inside.
- Prompt interactions (`click.prompt`, `click.echo`) stay inside this file.
- Decorated with `@handle_cli_error`.

### `ports/interface.py` — feature-to-feature port

- Exposes the **minimal surface** other features strictly need.
- All parameters and return types are primitives (`str`, `list[str]`, `dict[str, str]`, `bool`).
- No Click, no output, no side-effects beyond storage reads/writes.
- Function names mirror usecase names or collapse to the caller's semantic (`read_secrets`, `write_secret`, `has_secrets`).

## Secrets Feature — concrete inventory

### Usecases
| File | Function |
|---|---|
| `list_all.py` | `list_all(namespace)` |
| `reveal_secrets.py` | `reveal_secrets(namespace)` |
| `write_secret.py` | `write_secret(key, value, namespace)` |
| `remove_secret.py` | `remove_secret(key, namespace)` |
| `_storage.py` | `load_storage()`, `ensure_unlocked(storage)` |

### `ports/cli.py`
| Command | Signature |
|---|---|
| `ls` | `--namespace / -n` |
| `reveal` | `--namespace / -n` |
| `add` | `KEY --namespace / -n` |
| `remove` | `KEY --namespace / -n` |

### `ports/interface.py`
| Function | Parameters | Return |
|---|---|---|
| `read_secrets` | `namespace: str, secret_names: list[str]` | `dict[str, str]` |
| `write_secret` | `namespace: str, secret_name: str, secret_value: str` | `None` |
| `has_secrets` | `namespace: str, secret_names: list[str]` | `bool` |

## Naming Rules

| Symbol | Convention | Example |
|---|---|---|
| Feature package | `snake_case` noun | `secrets`, `project`, `hosts` |
| Aggregate | `PascalCase` noun | `Project` |
| Aggregate event | `PascalCase` past-tense | `Registered`, `TechStackDetected` |
| Application class | `{Feature}Application` | `ProjectApplication` |
| Usecase file | `snake_case` verb phrase | `write_secret.py` |
| Usecase function | identical to filename | `def write_secret(...)` |
| Internal helper | `_snake_case` (underscore prefix) | `_storage.py` |
| CLI group name | `snake_case` feature noun | `"secrets"` |
| CLI command name | short imperative verb | `ls`, `add`, `remove`, `reveal` |
| Interface function | `snake_case` verb phrase, caller-semantic | `read_secrets`, `has_secrets` |
