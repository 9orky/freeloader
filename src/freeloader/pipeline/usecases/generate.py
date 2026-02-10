import os
from dataclasses import dataclass
from pathlib import Path

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.orchestrator import Preflight
from freeloader.blocks.models import RunnerType
from freeloader.projects.models import ProjectManifest
from freeloader.pipeline.runners.generator import GeneratorRunner
from freeloader.pipeline.runners.terraform.resource import TerraformResource
from freeloader.blocks.registry import BlockRegistry
from freeloader.shared.paths import project_resource_dir


@dataclass(frozen=True)
class GenerateResult:
    generated_block_ids: list[str]


class GenerateUseCases:
    def __init__(self, preflight: Preflight, registry: BlockRegistry, output_dir: Path) -> None:
        self._preflight = preflight
        self._registry = registry
        self._output_dir = output_dir.resolve()

    def generate(self, manifest: ProjectManifest) -> GenerateResult:
        resolved = self._preflight.resolve(manifest)

        generator_blocks = [
            b for b in resolved if b.contract.block.runner == RunnerType.generator
        ]
        if not generator_blocks:
            return GenerateResult(generated_block_ids=[])

        block_dirs = {
            b.contract.block.name: self._registry.get_block_dir(b.ref.use)
            for b in resolved
        }

        ctx = ExecutionContext()
        resource_dir = project_resource_dir(manifest.project.name)
        for b in resolved:
            if b.contract.block.runner != RunnerType.generator:
                outputs = self._read_block_outputs(resource_dir, b)
                if outputs:
                    ctx.set_outputs(b.ref.resolved_id, outputs)
                else:
                    for key in b.contract.provides:
                        ctx.set_outputs(b.ref.resolved_id, {
                                        key: f"<pending:{key}>"})

        runner = GeneratorRunner(self._output_dir, block_dirs)
        generated_ids: list[str] = []
        for block in generator_blocks:
            result = runner.apply_block(block, ctx)
            if result:
                generated_ids.append(block.ref.resolved_id)

        return GenerateResult(generated_block_ids=generated_ids)

    @staticmethod
    def _read_block_outputs(
        resource_dir: Path, block: ResolvedBlock,
    ) -> dict[str, str]:
        workspace = resource_dir / block.ref.resolved_id
        state_file = workspace / "terraform.tfstate"
        if not state_file.exists():
            return {}
        raw = TerraformResource.read_outputs_from_dir(
            workspace, dict(os.environ))
        return block.contract.map_outputs(raw)
