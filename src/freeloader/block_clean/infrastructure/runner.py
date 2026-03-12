from pathlib import Path

from freeloader.shared.terraform import TerraformResource
from freeloader.shared.types import ConfigValue

from ..domain.entity import ResolvedBlock
from ..domain.repository import SecretsReader

from .resource import ProvisioningResource


class BlockRunner:
    def __init__(self, project_path: Path, secrets: SecretsReader) -> None:
        self._variables_builder = VariablesBuilder(project_path, secrets)

    def run_init(
        self,
        resource: ProvisioningResource,
        block: ResolvedBlock,
        extra_vars: dict[str, ConfigValue | None] | None = None,
    ) -> None:
        tfvars = self._variables_builder.build(block, extra_vars)
        TerraformResource(resource.folder).init(tfvars)

    def run_plan(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).plan()

    def run_apply(self, resource: ProvisioningResource) -> dict[str, ConfigValue | None]:
        tf = TerraformResource(resource.folder)
        tf.apply()
        return _normalize_outputs(tf.output())

    def run_destroy(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).destroy()


def _normalize_outputs(raw: dict | list) -> dict[str, ConfigValue | None]:
    if isinstance(raw, list) or not raw:
        return {}
    result: dict[str, ConfigValue | None] = {}
    for key, entry in raw.items():
        result[key] = entry["value"] if isinstance(
            entry, dict) and "value" in entry else entry
    return result


class VariablesBuilder:
    def __init__(self, project_path: Path, secrets_reader: SecretsReader) -> None:
        self._project_path = project_path
        self._secrets_reader = secrets_reader

    def build(
        self,
        block: ResolvedBlock,
        extra_vars: dict[str, ConfigValue | None] | None = None,
    ) -> dict[str, ConfigValue | None]:
        tfvars: dict[str, ConfigValue | None] = dict(block.ref.config)

        secret_fields = block.contract.config_fields("secrets")
        if secret_fields:
            secret_names = [f.name for f in secret_fields]
            tfvars.update(self._secrets_reader.read(secret_names))

        if extra_vars:
            tfvars.update(extra_vars)

        has_target_folder = any(
            f.name == "target_folder" for f in block.contract.config)
        if has_target_folder and "target_folder" not in tfvars and self._project_path is not None:
            tfvars["target_folder"] = str(self._project_path)

        return tfvars
