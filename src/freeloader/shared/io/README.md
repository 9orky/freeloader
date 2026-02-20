# io

YAML persistence for Pydantic models and plain dicts.

## Responsibilities

- Reads YAML files into raw dicts or validated Pydantic models
- Writes dicts and Pydantic model instances to YAML, excluding computed fields

## Public interface

```python
from freeloader.shared.io import load_yaml, load_yaml_model, save_yaml, save_yaml_model

data: dict = load_yaml(path)
instance: MyModel = load_yaml_model(path, MyModel)
save_yaml(path, {"key": "value"})
save_yaml_model(path, instance)
```
