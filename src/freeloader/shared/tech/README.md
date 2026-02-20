# tech

Technology stack detection from project directory contents.

## Responsibilities

- Detects the language and package manager of a project by scanning its files
- Maintains a registry of `TechDetector` implementations (Node, Python)
- Returns a `TechStack` value object or `None` when no detector matches

## Public interface

```python
from freeloader.shared.tech import detect_stack, TechStack

stack: TechStack | None = detect_stack(Path("/my/project"))
if stack:
    print(stack.language, stack.package_manager)
```
