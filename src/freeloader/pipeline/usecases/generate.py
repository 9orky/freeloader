import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import DAGResolver
from freeloader.blocks.models import RunnerType
from freeloader.projects.models import ProjectManifest
from freeloader.pipeline.runners.generator import GeneratorRunner
from freeloader.blocks.registry import BlockRegistry
from freeloader.shared.paths import project_tf_dir


@dataclass(frozen=True)
class GenerateResult:
    generated_block_ids: list[str]


class GenerateUseCases:
    def __init__(self, registry: BlockRegistry, output_dir: Path) -> None:
        self._registry = registry
        self._output_dir = output_dir.resolve()

    def generate(self, manifest: ProjectManifest) -> GenerateResult:
        contracts = {
            ref.resolved_id: self._registry.get_block(ref.use)
            for ref in manifest.blocks
        }

        dag = DAGResolver()
        resolved = dag.resolve(manifest.blocks, contracts)

        generator_blocks = [
            b for b in resolved if b.contract.block.runner == RunnerType.generator
        ]
        if not generator_blocks:
            return GenerateResult(generated_block_ids=[])

        block_dirs = {
            ref.resolved_id: self._registry.get_block_dir(ref.use)
            for ref in manifest.blocks
        }

        ctx = ExecutionContext()
        tf_dir = project_tf_dir(manifest.project.name)
        for b in resolved:
            if b.contract.block.runner != RunnerType.generator:
                real = self._read_tf_outputs(
                    tf_dir, b.ref.resolved_id, b.contract.provides)
                if real:
                    ctx.set_outputs(b.ref.resolved_id, real)
                else:
                    for key in b.contract.provides:
                        ctx.set_outputs(b.ref.resolved_id, {
                                        key: f"<pending:{key}>"})

        runner = GeneratorRunner(self._output_dir, block_dirs)
        outputs = runner.apply(generator_blocks, ctx)

        return GenerateResult(generated_block_ids=list(outputs.keys()))

    @staticmethod
    def _read_tf_outputs(
        tf_dir: Path, block_id: str, provides: dict[str, object],
    ) -> dict[str, str]:
        """Read real terraform outputs for a block if state exists."""
        workspace = tf_dir / block_id
        state_file = workspace / "terraform.tfstate"
        if not state_file.exists():
            return {}
        try:
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=workspace, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return {}
            raw = json.loads(result.stdout)
            outputs: dict[str, str] = {}
            for port_key in provides:
                tf_name = port_key.split(".")[-1]
                if tf_name in raw:
                    outputs[port_key] = raw[tf_name].get("value", "")
            return outputs
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            return {}
