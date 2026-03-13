# Architecture Rules Subsystem Design

## Status

Proposed

## Goal

Move the architecture checks out of [tests/test_architecture.py](tests/test_architecture.py) into a dedicated Python subpackage so:

- the test file becomes a thin harness
- rules can be reused by other tests, scripts, or CI entrypoints
- adding a new rule means creating one class and registering it in one place
- repository traversal, AST parsing, reporting, and rule execution are shared instead of embedded in one test module

## Non-Goals

- Moving the rules into production runtime packages under `src/freeloader/`
- Turning the subsystem into a generic third-party framework
- Changing the architecture rules themselves as part of the extraction
- Replacing pytest as the enforcement entrypoint

## Placement

The subsystem should live under `tests/`, not `src/`.

Reasoning:

- These rules are repository-specific developer tooling, not application runtime behavior.
- They need direct access to test-oriented reporting and failure formatting.
- Keeping them under `tests/` avoids mixing development policy code into feature packages.
- The package is still reusable elsewhere through imports or `python -m` execution because `tests/` is already a Python package.

Proposed package:

```text
tests/
├── architecture_rules/
│   ├── __init__.py
│   ├── __main__.py
│   ├── context.py
│   ├── pipeline.py
│   ├── registry.py
│   ├── reporting.py
│   ├── results.py
│   └── rules/
│       ├── __init__.py
│       ├── base.py
│       ├── feature_isolation.py
│       ├── shared_independence.py
│       ├── layer_order.py
│       ├── domain_boundary.py
│       ├── ui_import_surface.py
│       ├── package_surface.py
│       ├── legacy_layers.py
│       └── deep_relative_imports.py
└── test_architecture.py
```

## Design Summary

The current test mixes four concerns in one file:

- repository inspection helpers
- rule definitions
- rule execution order
- pytest-specific failure behavior

The redesign separates them into explicit layers:

1. `context.py`
   - Repository model and shared AST/import helpers.

2. `rules/base.py`
   - Small abstract rule interface.

3. `rules/*.py`
   - One file per rule class.

4. `registry.py`
   - Ordered default rule list.

5. `pipeline.py`
   - Runs a sequence of rule objects and returns structured results.

6. `reporting.py`
   - Converts structured results into console text.

7. `test_architecture.py`
   - Builds the default pipeline, runs it, prints the report, fails if needed.

## Core Types

### `ArchitectureContext`

Purpose: centralize repo traversal and AST helpers that rules need.

Responsibilities:

- hold canonical paths such as repo root, `src/`, `src/freeloader/`, and `shared/`
- enumerate feature packages
- enumerate shared subpackages
- map files to module names
- parse files once and cache ASTs
- resolve relative imports
- expose helper queries such as package imports and `__all__` extraction

Key point: rules should ask the context for data, not each rule reimplement filesystem logic.

Example API:

```python
@dataclass(frozen=True)
class ArchitectureContext:
    repo_root: Path
    src_root: Path
    freeloader_root: Path
    shared_root: Path

    @classmethod
    def for_repo_root(cls, repo_root: Path) -> "ArchitectureContext": ...

    def feature_packages(self) -> list[Path]: ...
    def shared_subpackages(self) -> list[Path]: ...
    def file_to_module(self, py_file: Path) -> str: ...
    def parse_file(self, py_file: Path) -> ast.AST | None: ...
    def imports_in_file(self, py_file: Path) -> list[str]: ...
    def package_imports(self, pkg_dir: Path) -> list[tuple[str, str]]: ...
    def string_list_assignment(self, py_file: Path, name: str) -> list[str] | None: ...
```

### `RuleViolation`

Purpose: normalize how failures are represented.

Suggested shape:

```python
@dataclass(frozen=True)
class RuleViolation:
    message: str
    file_path: Path | None = None
    line: int | None = None
```

This keeps rules structured enough for later consumers without overdesigning a rich diagnostics system.

### `RuleResult`

Purpose: capture one rule execution outcome.

Suggested shape:

```python
@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    description: str
    violations: list[RuleViolation]

    @property
    def passed(self) -> bool:
        return not self.violations
```

### `PipelineResult`

Purpose: aggregate all rule results.

Suggested shape:

```python
@dataclass(frozen=True)
class PipelineResult:
    results: list[RuleResult]

    @property
    def failed(self) -> bool:
        return any(not result.passed for result in self.results)
```

## Rule Interface

Use a single abstract base class, but do not use chain-of-responsibility.

The current linked `set_next()` pipeline makes rules harder to reorder, test, subset, or reuse. A list-based pipeline is simpler and more composable.

Suggested interface:

```python
class ArchitectureRule(ABC):
    rule_id: str
    title: str
    description: str

    @abstractmethod
    def check(self, context: ArchitectureContext) -> RuleResult: ...
```

Rule author workflow:

1. Create a new file in `tests/architecture_rules/rules/`.
2. Implement one `ArchitectureRule` subclass.
3. Register it in `registry.py`.

That is the only required extension path.

## Pipeline

Suggested implementation:

```python
@dataclass(frozen=True)
class RulePipeline:
    rules: tuple[ArchitectureRule, ...]

    def run(self, context: ArchitectureContext) -> PipelineResult:
        return PipelineResult([rule.check(context) for rule in self.rules])
```

This makes it easy to:

- run the default full set
- run only one rule in a focused test
- run a smaller subset in CI or local debugging
- add future grouping or filtering without changing rule classes

## Registry

`registry.py` should own ordering.

Suggested API:

```python
def default_rules() -> tuple[ArchitectureRule, ...]: ...


def build_default_pipeline() -> RulePipeline:
    return RulePipeline(default_rules())
```

Why a registry file:

- one obvious place to add or reorder rules
- no hidden side effects from import-time auto-registration
- predictable output order in tests and CI

Avoid decorator-based global registries. They add indirection without real value here.

## Reporting

The pipeline should return data, not print.

`reporting.py` should format results for humans:

```python
def render_pipeline_result(result: PipelineResult) -> str: ...
```

That keeps rule logic testable and makes the subsystem reusable for:

- pytest
- `python -m tests.architecture_rules`
- future `make architecture` or CI wrappers

## Test Harness

Target shape for [tests/test_architecture.py](tests/test_architecture.py):

```python
from pathlib import Path

import pytest

from tests.architecture_rules import (
    ArchitectureContext,
    build_default_pipeline,
    render_pipeline_result,
)


def test_architecture() -> None:
    context = ArchitectureContext.for_repo_root(Path(__file__).resolve().parents[1])
    result = build_default_pipeline().run(context)
    print(render_pipeline_result(result))
    if result.failed:
        pytest.fail("Architecture violations detected (see above)", pytrace=False)
```

That is the desired end state: the test runs the subsystem, but does not contain the subsystem.

## Reuse Outside Pytest

Add `tests/architecture_rules/__main__.py` so the rules can also be run as:

```bash
python -m tests.architecture_rules
```

This gives immediate reuse without inventing a separate CLI package.

Later, a Make target or CI step can call that module directly.

## Rule Granularity

Keep one rule class per policy, even if the implementation is short.

Why:

- easier focused failures
- easier unit tests for one rule at a time
- easier future disablement or temporary quarantine of one rule
- simpler ownership when a new rule is added

Do not group multiple unrelated policies into one checker class just because they all use the same helpers.

## Migration Plan

### Step 1

Create `tests/architecture_rules/context.py`, `results.py`, `pipeline.py`, and `rules/base.py`.

### Step 2

Move shared helper logic out of [tests/test_architecture.py](tests/test_architecture.py) into `ArchitectureContext`.

### Step 3

Port each existing checker into its own file under `rules/` with the same titles, descriptions, and violation messages.

### Step 4

Add `registry.py` and `reporting.py`.

### Step 5

Shrink [tests/test_architecture.py](tests/test_architecture.py) to the thin harness.

### Step 6

Add `__main__.py` so the subsystem can run outside pytest.

### Step 7

Optionally add focused unit tests for `ArchitectureContext`, `render_pipeline_result()`, and one or two representative rules.

## Trade-offs

### Positive

- Clear separation between policy, shared inspection code, and test harness.
- New rules become cheap to add.
- The rules can run in pytest, direct module execution, or future tooling.
- The output path becomes consistent and testable.

### Cost

- More files than the current single-module implementation.
- Slightly more ceremony for simple rules.
- Need to preserve current message text carefully so the first extraction does not create noisy diffs in test output.

## Recommendation

Proceed with the extraction into `tests/architecture_rules/` using:

- a cached `ArchitectureContext`
- one-class-per-rule modules
- a list-based `RulePipeline`
- a manual `registry.py` for default ordering
- a tiny pytest harness in [tests/test_architecture.py](tests/test_architecture.py)

This is the smallest design that makes the rules reusable, keeps the test readable, and makes adding new rule classes straightforward.