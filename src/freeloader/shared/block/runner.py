from pathlib import Path
from typing import Any

from .base import TerraformBridge, SecretsBridge
from .context import ExecutionContext
from .dag import ResolvedBlock


class BlockRunner:
    def __init__(
        self,
        work_dir: Path,
        blocks_root: Path,
        secrets_bridge: SecretsBridge,
        terraform_bridge: TerraformBridge,
        project_path: Path | None = None,
    ) -> None:
        self._work_dir = work_dir
        self._blocks_root = blocks_root
        self._secrets_bridge = secrets_bridge
        self._terraform_bridge = terraform_bridge
        self._project_path = project_path

    def run_all(
        self,
        blocks: list[ResolvedBlock],
        context: ExecutionContext,
    ) -> None:
        for block in blocks:
            self.run_one(block, context)

    def run_one(
        self,
        block: ResolvedBlock,
        context: ExecutionContext,
    ) -> None:
        tfvars = self._build_tfvars(block, context)
        template = self._blocks_root / block.ref.use / "main.tf"
        work_dir = self._block_work_dir(block.ref.resolved_id)
        tf = self._terraform_bridge 
        tf.prepare(template, tfvars)
        tf.apply()
        raw = tf.output()
        outputs = block.contract.map_outputs(
            raw if isinstance(raw, dict) else {})
        context.set_outputs(block.ref.resolved_id, outputs)

    def _build_tfvars(
        self,
        block: ResolvedBlock,
        context: ExecutionContext,
    ) -> dict[str, Any]:
        tfvars: dict[str, Any] = dict(block.ref.config)

        secret_fields = block.contract.config_fields("secrets")
        if secret_fields:
            secret_names = [f.name for f in secret_fields]
            secrets = self._secrets_reader(block.ref.use, secret_names)
            tfvars.update(secrets)

        resolved = context.resolve_inputs(block.inputs)
        for req_key, value in resolved.items():
            tfvar_name = req_key.replace(".", "_")
            tfvars[tfvar_name] = value

        has_target_folder = any(
            f.name == "target_folder" for f in block.contract.config
        )
        if has_target_folder and "target_folder" not in tfvars and self._project_path is not None:
            tfvars["target_folder"] = str(self._project_path)

        return tfvars

    def _block_work_dir(self, resolved_id: str) -> Path:
        return self._work_dir / resolved_id
