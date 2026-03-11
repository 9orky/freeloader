# Model Feature Architecture

Use this as the default feature shape for user-facing features in this repository.

## Goal

Make feature structure obvious.
An LLM or human should be able to answer these questions quickly:

- Where does the CLI live?
- What is the machine-facing API for other features?
- Where does orchestration live?
- Where is the real behavior?
- Which modules are internal only?

## Default Shape

```text
src/freeloader/<feature>/
  __init__.py
  cli.py
  application.py
  models.py
  ports/
    __init__.py
    interface.py
  usecases/
    __init__.py
    <usecase>.py
  adapters/
    __init__.py
    <adapter>.py
```

Optional internal infrastructure is allowed when the feature needs it:

```text
  provider/
    __init__.py
    registry.py
    auth.py
    billing.py
    <implementation packages>/
```

## Layer Roles

- `cli.py`
  Terminal-facing commands only.
  Collect input, call `application.py`, render output.

- `ports/interface.py`
  Machine-facing API for other features.
  Other features may import only this file from the feature.

- `application.py`
  Feature entrypoint.
  Exposes the small public surface used by `cli.py` and `ports/interface.py`.
  Delegates to usecases.

- `usecases/`
  Actual feature behavior.
  Each file handles one focused capability.
  This is where orchestration logic belongs.

- `models.py`
  Typed request/result contracts shared by application, ports, and CLI.

- `adapters/`
  Dependencies outside the feature boundary.
  Example: secrets storage, filesystem, HTTP clients, subprocesses.

- Internal infrastructure like `provider/`
  Internal only.
  May contain registries, decorators, provider implementations, or low-level domain mechanics.
  Must not be imported by other features.

## Allowed Flow

Primary user flow:

```text
cli.py -> application.py -> usecases/*
```

Cross-feature flow:

```text
other feature -> ports/interface.py -> application.py -> usecases/*
```

Usecases may call:

- `models.py`
- `adapters/*`
- internal infrastructure inside the same feature

## Import Rules

- Other features may import only `<feature>.ports.interface`.
- `cli.py` should import `application.py`, not `ports/interface.py`.
- `application.py` should import `usecases/*`.
- `usecases/*` should not import `ports/interface.py`.
- `usecases/*` may import internal modules of the same feature.
- Package root `__init__.py` should stay minimal. Do not build a fake facade there.
- Internal subpackages should not re-export abstractions unless there is a real caller.

## Communication Rule

Do not add a mediator, command bus, or event bus by default.

Prefer:

1. Direct in-process call through another feature's `ports/interface.py`.
2. A small `application.py` module inside the feature.
3. A dedicated workflow service only when one action coordinates multiple features.

Add event-style dispatch only if one state change must trigger multiple independent reactions and direct calls become noisy.

## Anti-Patterns

- `cli.py -> ports/interface.py -> application.py`
- `usecases/* -> application.py`
- other features importing `adapters/*` or internal infrastructure
- package root re-exporting half the feature
- internal registries exposed as the public API
- compatibility wrappers that only forward calls between layers

## Minimal Checklist For A New Feature

1. Add `cli.py` if the feature is user-facing.
2. Add `ports/interface.py` if other features need it.
3. Keep `application.py` small and explicit.
4. Put real behavior in focused usecase files.
5. Keep external dependencies in adapters.
6. Keep internal infrastructure private.
7. Expose only what real callers need.

## Reference In This Repo

`service_providers` is the current model feature for this shape:

- [src/freeloader/service_providers/cli.py](src/freeloader/service_providers/cli.py)
- [src/freeloader/service_providers/application.py](src/freeloader/service_providers/application.py)
- [src/freeloader/service_providers/ports/interface.py](src/freeloader/service_providers/ports/interface.py)
- [src/freeloader/service_providers/usecases](src/freeloader/service_providers/usecases)
- [src/freeloader/service_providers/provider](src/freeloader/service_providers/provider)