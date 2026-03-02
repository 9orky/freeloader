from pathlib import Path

from freeloader.shared.terraform import TerraformResource

from freeloader.shared.types import ConfigValue

from .base import SecretsReader
from .context import ExecutionContext
from .resolver import ResolvedBlock
from .provision import ProvisioningResource


class BlockRunner:
    def __init__(self, project_path: Path, secrets: SecretsReader) -> None:
        self._variables_builder = VariablesBuilder(project_path, secrets)

    def run_init(self, resource: ProvisioningResource, block: ResolvedBlock) -> None:
        tfvars = self._variables_builder.build(block)
        TerraformResource(resource.folder).init(tfvars)

    def run_init_with_deps(self, resource: ProvisioningResource, block: ResolvedBlock, context: ExecutionContext) -> None:
        tfvars = self._variables_builder.build(block, context)
        TerraformResource(resource.folder).init(tfvars)

    def run_plan(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).plan()

    def run_apply(self, resource: ProvisioningResource) -> dict[str, ConfigValue | None]:
        tf = TerraformResource(resource.folder)
        tf.apply()
        raw = tf.output()
        return _normalize_outputs(raw)

    def run_destroy(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).destroy()


def _normalize_outputs(raw: dict | list) -> dict[str, ConfigValue | None]:
    if isinstance(raw, list) or not raw:
        return {}
    result: dict[str, ConfigValue | None] = {}
    for key, entry in raw.items():
        if isinstance(entry, dict) and "value" in entry:
            result[key] = entry["value"]
        else:
            result[key] = entry
    return result


class VariablesBuilder:
    def __init__(self, project_path: Path, secrets_reader: SecretsReader) -> None:
        self._project_path = project_path
        self._secrets_reader = secrets_reader

    def build(self, block: ResolvedBlock, context: ExecutionContext | None = None) -> dict[str, ConfigValue | None]:
        tfvars: dict[str, ConfigValue | None] = dict(block.ref.config)

        secret_fields = block.contract.config_fields("secrets")
        if secret_fields:
            secret_names = [f.name for f in secret_fields]
            secrets = self._secrets_reader.read(secret_names)
            tfvars.update(secrets)

        if context and block.inputs:
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

        if self._project_path is not None:
            for f in block.contract.config:
                if f.project_name_default and f.name not in tfvars:
                    tfvars[f.name] = self._project_path.name

        return tfvars
