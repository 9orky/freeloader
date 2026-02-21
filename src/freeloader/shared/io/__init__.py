from pathlib import Path
from typing import TypeVar, Type

from ruamel.yaml import YAML
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_yaml = YAML()
_yaml.indent(mapping=2, sequence=4, offset=2)
_yaml.preserve_quotes = True
_yaml.default_flow_style = False


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return _yaml.load(f) or {}


def save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data, f)


def load_yaml_model(path: Path, model_class: Type[T]) -> T:
    data = load_yaml(path)
    return model_class.model_validate(data)


def save_yaml_model(path: Path, instance: BaseModel) -> None:
    exclude = _computed_fields(instance)
    data = instance.model_dump(mode="python", exclude_none=True, exclude=exclude)
    save_yaml(path, data)


def _computed_fields(instance: BaseModel) -> set[str]:
    cls = type(instance)
    exclude: dict = {}
    for name in cls.model_computed_fields:
        exclude[name] = True
    for name in cls.model_fields:
        value = getattr(instance, name, None)
        if isinstance(value, BaseModel):
            nested = _computed_fields(value)
            if nested:
                exclude[name] = nested
        elif isinstance(value, list):
            nested_set: dict = {}
            for i, item in enumerate(value):
                if isinstance(item, BaseModel):
                    nested = _computed_fields(item)
                    if nested:
                        nested_set[i] = nested
            if nested_set:
                exclude[name] = nested_set
    return exclude