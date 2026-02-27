from pathlib import Path
from typing import Any

from ..base import SecretsReader
from ..context import ExecutionContext
from ..resolver import ResolvedBlock


class VariablesBuilder:
    def __init__(self, project_path: Path, secrets_reader: SecretsReader) -> None:
        self._project_path = project_path
        self._secrets_reader = secrets_reader

    def build(self, block: ResolvedBlock, context: ExecutionContext) -> dict[str, Any]:
        tfvars: dict[str, Any] = dict(block.ref.config)

        secret_fields = block.contract.config_fields("secrets")
        if secret_fields:
            secret_names = [f.name for f in secret_fields]
            secrets = self._secrets_reader.read(secret_names)
            tfvars.update(secrets)

        resolved = context.resolve_inputs(block.inputs)
        for req_key, value in resolved.items():
            tfvar_name = req_key.replace(".", "_")
            tfvars[tfvar_name] = value

        has_target_folder = any(
            f.name == "target_folder"
            for f in block.contract.config
        )

        if has_target_folder and "target_folder" not in tfvars and self._project_path is not None:
            tfvars["target_folder"] = str(self._project_path)

        return tfvars
