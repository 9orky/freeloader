# Feature Architecture Guide

Freeloader features are already migrated. This guide describes the steady-state contract only.

## Core Rules

1. Package root is the only cross-feature entrypoint.
   - Other features import `freeloader.<feature>` only.
   - Imports like `freeloader.<feature>.application`, `freeloader.<feature>.domain`, `freeloader.<feature>.infrastructure`, and `freeloader.<feature>.ui` are forbidden outside that feature.
   - A feature package root exposes at most two names through `__all__`: the CLI app (`<feature>_app`) and the machine-facing facade from `application/interface.py`. A feature may export one or both. Nothing else.

2. Layer direction is fixed.

   ```
   ui/ (optional)        -> application/
   application/          -> infrastructure/ and domain/
   infrastructure/       -> domain/
   domain/               -> stdlib and freeloader.shared only
   ```

3. Optional layers are normal.
   - Omit `ui/` for machine-only features.
   - Omit `application/interface.py` when the feature has no cross-feature machine API.

4. `application/__init__.py` is the feature-local import surface for UI code.
   - `ui/cli.py` imports the `application` package as a module and calls `application.<function>()`.
   - `application/__init__.py` re-exports the use-case functions the UI needs, plus the optional facade.
   - Cross-feature callers do not use this module; they go through the feature package root.

5. Relative imports stay shallow.
   - Use `.` and `..` inside a feature when the target is nearby.
   - If `...` or deeper would be required, switch to `freeloader.<feature>...`.

6. Legacy layer names are gone.
   - Do not add `adapters/`, `ports/`, `storage/`, or `usecases/`.

## Layout

```text
src/freeloader/<feature>/
├── __init__.py          # cross-feature surface; exports app and/or facade only
├── domain/
│   ├── __init__.py      # domain constants only
│   ├── entity.py        # entities and domain models
│   ├── value_object.py  # typed wrappers for primitives
│   ├── repository.py    # abstract repository contracts
│   └── ...
├── application/
│   ├── __init__.py      # UI import surface; re-exports use cases and optional facade
│   ├── commands.py      # write use cases
│   ├── queries.py       # read use cases
│   ├── interface.py     # optional machine API for other features
│   └── services/        # optional orchestration, flat module or package
├── infrastructure/
│   ├── __init__.py      # load_* factories only
│   └── ...              # concrete storage / external-system implementations
└── ui/                  # optional
    ├── __init__.py
    ├── cli.py           # Typer wiring only
    └── views.py         # optional presentation-only shapes
```

## Package Root

- `src/freeloader/<feature>/__init__.py` is minimal.
- Re-export only `<feature>_app` and/or the facade class.
- Do not re-export domain entities, events, reports, repositories, or application functions.
- Same-feature internals should not route through the package root.

## Domain

- Domain code imports only the standard library, local `domain/` modules, and feature-neutral modules from `freeloader.shared`.
- Keep entities and value objects immutable unless mutability is a real domain requirement.
- Repository contracts are abstract base classes defined in `domain/repository.py`.
- Any model shared across layers belongs in the lowest layer that owns its meaning, usually `domain/`.
- If a type already has a cross-feature source of truth in `freeloader.shared` such as `shared.types` or `shared.tech`, domain code uses that shared model instead of duplicating it locally.

## Application

- `commands.py` handles writes; `queries.py` handles reads.
- Public signatures use primitives, `Path`, or plain frozen dataclasses. Do not expose repository ABCs, infrastructure implementations, or service classes in command/query signatures.
- Commands and queries obtain dependencies from `infrastructure/__init__.py`.
- `interface.py` is optional. When present, it is a thin facade for other features: normalize inputs, keep context, delegate to commands and queries, and do no I/O.
- `services/` is optional. Use it for orchestration that is too large for one command or query.
- Service modules may depend on feature-local infrastructure collaborators only when the caller already wired those collaborators. Services do not perform factory lookup, environment access, or storage discovery.

## Infrastructure

- Infrastructure implements repository contracts and other external-system adapters.
- Public wiring lives in `infrastructure/__init__.py` as `load_*` factories.
- Implementation modules do not own public factory functions.

## UI

- `ui/cli.py` contains Typer wiring only.
- Import the feature `application` package as a module, not `commands.py` or `queries.py` directly.
- UI does not import feature `domain/` or `infrastructure/`.
- Presentation-only data shapes belong in `ui/views.py`.

## Testing Conventions

- Application tests patch `feature.infrastructure.load_*` factories.
- Facade tests patch functions on `feature.application`.
- CLI tests patch `feature.ui.cli.application.<function>`.
- Cross-feature tests import through feature package roots, never through deeper feature modules.
- Architecture tests enforce the rules in this document; production code should not be reshaped just to accommodate a test patch path.