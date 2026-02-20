from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def load_yaml_model(path: Path, model_class: type[T]) -> T:
    return model_class.model_validate(load_yaml(path))


def save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def save_yaml_model(path: Path, instance: BaseModel) -> None:
    save_yaml(path, instance.model_dump(
        mode="json", exclude_none=True, exclude=_computed_fields(instance)))


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
