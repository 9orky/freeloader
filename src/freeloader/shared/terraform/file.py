from dataclasses import dataclass
from pathlib import Path

import hcl2

from .variable import TerraformVariable


UNSET = object()


@dataclass(frozen=True)
class TerraformOutput:
    name: str
    description: str
    sensitive: bool


class TerraformFile:
    def __init__(self, path: Path) -> None:
        assert path.is_file(), f"Terraform file not found: {path}"
        
        self._path = path
        raw = hcl2.loads(path.read_text())
        self._variables = _parse_variables(raw.get("variable", []))
        self._outputs = _parse_outputs(raw.get("output", []))

    @property
    def path(self) -> Path:
        return self._path

    @property
    def variables(self) -> list[TerraformVariable]:
        return self._variables

    @property
    def outputs(self) -> list[TerraformOutput]:
        return self._outputs
    
    def dump(self, target: Path) -> None:
        content = self._path.read_text()
        target.write_text(content)

    def required_variables(self) -> list[TerraformVariable]:
        return [v for v in self._variables if v.required]

    def optional_variables(self) -> list[TerraformVariable]:
        return [v for v in self._variables if not v.required]

    def sensitive_variables(self) -> list[TerraformVariable]:
        return [v for v in self._variables if v.sensitive]

    def variable_names(self) -> set[str]:
        return {v.name for v in self._variables}

    def has_variable(self, name: str) -> bool:
        return name in self.variable_names()


def _parse_variables(raw_vars: list[dict]) -> list[TerraformVariable]:
    result: list[TerraformVariable] = []
    for block in raw_vars:
        for name, attrs in block.items():
            default_val = attrs.get("default", UNSET)
            has_default = default_val is not UNSET
            result.append(TerraformVariable(
                name=name,
                type=_extract_type(attrs.get("type", "string")),
                default=default_val if has_default else None,
                description=attrs.get("description", ""),
                sensitive=attrs.get("sensitive", False),
                required=not has_default,
            ))
    return result


def _parse_outputs(raw_outputs: list[dict]) -> list[TerraformOutput]:
    result: list[TerraformOutput] = []
    for block in raw_outputs:
        for name, attrs in block.items():
            result.append(TerraformOutput(
                name=name,
                description=attrs.get("description", ""),
                sensitive=attrs.get("sensitive", False),
            ))
    return result


def _extract_type(raw: str | dict) -> str:
    if isinstance(raw, str):
        return raw
    return str(raw)
