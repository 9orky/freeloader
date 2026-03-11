## Plan: Service Providers As Model Feature

Redesign `service_providers` so it becomes a feature that fits this repository’s real shape instead of copying a pattern from another package. The target architecture should make three things explicit: the human-facing CLI, the machine-facing feature API, and the internal provider infrastructure. Cross-feature communication should stay explicit and typed rather than flowing through hidden imports or a global mediator.

## Target Architecture

`service_providers` should become a dual-surface feature:

- `cli.py` is the terminal-facing entrypoint.
- `ports/interface.py` is the machine-facing entrypoint for other features.
- `application.py` or `facade.py` is the internal feature service that coordinates usecases.
- `models.py` holds the public request/result contracts.
- `usecases/` contains focused orchestration handlers grouped by capability.
- `adapters/` handles only external integrations outside this feature boundary, such as secrets persistence.
- `provider/` stays internal and owns provider registration, lookup, auth metadata, and billing implementations.

This matches the repo better than a factory-centric template because the codebase already has feature-to-feature interfaces in [src/freeloader/block/ports/interface.py](src/freeloader/block/ports/interface.py) and [src/freeloader/secrets/ports/interface.py](src/freeloader/secrets/ports/interface.py), and already uses facades as feature composition roots.

## Communication Strategy

Do not introduce a mediator, command bus, or event bus as the default way features communicate.

Today the real cross-feature dependencies are simple and synchronous:

- `project` calls `block` through [src/freeloader/block/ports/interface.py](src/freeloader/block/ports/interface.py).
- `block` calls `secrets` through [src/freeloader/secrets/ports/interface.py](src/freeloader/secrets/ports/interface.py).
- `service_providers` persists credentials through `secrets`.

These are direct feature-to-feature calls with clear ownership. A mediator or bus would hide those dependencies, make flows harder to trace, and add indirection without solving a real scaling problem.

Prefer this order of communication patterns:

1. Direct in-process call through another feature’s `ports/interface.py`.
2. A small feature facade or application service that orchestrates multiple internal usecases.
3. A dedicated workflow service when one user action coordinates multiple features.

Only consider adding a tiny synchronous domain event dispatcher later if one action must fan out to multiple independent reactions across features. If that ever becomes necessary, use it only for notifications after state changes, not as a command routing mechanism.

## Steps

1. Phase 1: stabilize the package surface.
   Clean up [src/freeloader/service_providers/__init__.py](src/freeloader/service_providers/__init__.py), which currently references a missing facade, and define a small valid public API.
2. Phase 1: establish the feature boundary.
   Make `service_providers` expose two explicit entrypoints: a human-facing [src/freeloader/service_providers/cli.py](src/freeloader/service_providers/cli.py) and a machine-facing [src/freeloader/service_providers/ports/interface.py](src/freeloader/service_providers/ports/interface.py).
3. Phase 1: replace the orphaned CLI structure.
   Move the user-facing commands out of [src/freeloader/service_providers/ports/cli.py](src/freeloader/service_providers/ports/cli.py) into a top-level feature CLI so the feature has one obvious command surface.
4. Phase 2: introduce a feature facade.
   Add `application.py` or `facade.py` with a `ServiceProviders` application service that coordinates the usecases and adapters. Keep dependency construction local to this feature instead of exposing a separate factory as the main abstraction.
5. Phase 2: organize usecases by capability.
   Keep separate usecases for provider catalog, auth, and billing, but make them internal implementation details behind the feature facade. Callers should not import individual usecase files directly.
6. Phase 2: centralize contracts in a models module.
   Move provider view types, token-step view types, auth results, and billing results into `models.py` so the feature has one clear contract surface.
7. Phase 2: clarify adapter boundaries.
   Keep only external integration concerns in `adapters`, such as secret persistence. Treat [src/freeloader/service_providers/provider/auth.py](src/freeloader/service_providers/provider/auth.py), [src/freeloader/service_providers/provider/billing.py](src/freeloader/service_providers/provider/billing.py), and [src/freeloader/service_providers/provider/registry.py](src/freeloader/service_providers/provider/registry.py) as the home for provider discovery, lookup, auth metadata, and billing infrastructure.
8. Phase 2: define cross-feature communication rules.
   Require other features to call `service_providers` only through `ports/interface.py`. Do not allow direct imports from `provider/` or `adapters/` outside this package.
9. Phase 3: register the feature in the root CLI.
   Add it to [src/freeloader/cli.py](src/freeloader/cli.py) so the feature becomes first-class and its public entrypoint is visible.
10. Phase 3: replace import-only tests with behavior tests.
    Evolve [tests/test_service_providers.py](tests/test_service_providers.py) into tests for the feature interface, CLI behavior, and billing/auth orchestration.
11. Phase 4: make it the documented model feature.
    Update [AGENT.md](AGENT.md) after the refactor so new functionality is guided by this architecture: explicit ports, typed contracts, and a feature facade over internal usecases.

## Proposed Package Shape

```text
src/freeloader/service_providers/
  __init__.py
  cli.py
  application.py
  models.py
  ports/
    __init__.py
    interface.py
  usecases/
    __init__.py
    catalog.py
    auth.py
    billing.py
  adapters/
    __init__.py
    secrets.py
  provider/
    auth.py
    billing.py
    registry.py
    aws/
    coolify/
    docker/
    git/
    github/
    gitlab/
```

## Relevant files

- [src/freeloader/service_providers/__init__.py](src/freeloader/service_providers/__init__.py) — broken entrypoint; first thing to fix.
- [src/freeloader/service_providers/ports/cli.py](src/freeloader/service_providers/ports/cli.py) — current command surface; should be replaced by a top-level CLI.
- [src/freeloader/service_providers/usecases/__init__.py](src/freeloader/service_providers/usecases/__init__.py) — current exported API; should become internal-facing.
- [src/freeloader/service_providers/usecases/list_providers.py](src/freeloader/service_providers/usecases/list_providers.py) — current catalog usecase candidate.
- [src/freeloader/service_providers/usecases/check_billing.py](src/freeloader/service_providers/usecases/check_billing.py) — broken today and should be redesigned around typed outputs.
- [src/freeloader/service_providers/usecases/auth_provider.py](src/freeloader/service_providers/usecases/auth_provider.py) — current auth usecase candidate.
- [src/freeloader/service_providers/provider/auth.py](src/freeloader/service_providers/provider/auth.py) — provider auth contracts that should remain internal.
- [src/freeloader/service_providers/provider/billing.py](src/freeloader/service_providers/provider/billing.py) — provider billing contracts that should remain internal.
- [src/freeloader/service_providers/provider/registry.py](src/freeloader/service_providers/provider/registry.py) — internal provider registry boundary.
- [src/freeloader/block/ports/interface.py](src/freeloader/block/ports/interface.py) — reference for explicit cross-feature calls.
- [src/freeloader/secrets/ports/interface.py](src/freeloader/secrets/ports/interface.py) — reference for a feature-owned machine interface.
- [src/freeloader/project/usecases/manage.py](src/freeloader/project/usecases/manage.py) — example of a feature consuming another feature through an interface.
- [src/freeloader/cli.py](src/freeloader/cli.py) — root command registration point.
- [tests/test_service_providers.py](tests/test_service_providers.py) — should become behavior-focused.

## Verification

1. A newcomer should be able to understand the feature by reading `cli.py`, `ports/interface.py`, `application.py`, and `models.py` without opening provider internals.
2. The root CLI should expose the feature as a first-class command group.
3. Another feature should be able to use `service_providers` only through `ports/interface.py`.
4. The feature should remain understandable without any mediator, event bus, or command bus.
5. The package shape should be simple enough to reuse as the default architecture for other user-facing features in this project.

## Recommendation

The better fit for this repository is not “copy `hosts`” and not “add a mediator.” It is a feature architecture built around explicit interfaces and a small feature facade.

`service_providers` should become the model feature because it can demonstrate all three layers clearly:

- terminal interface through `cli.py`
- cross-feature interface through `ports/interface.py`
- internal provider infrastructure through `provider/`

That gives the project a more coherent default than a factory-based pattern and keeps feature communication visible, typed, and easy to trace.

If you want, the next step is:

1. Refine this into a concrete target file tree with responsibilities per file.
2. Convert it into an implementation sequence with minimal-risk commits.
