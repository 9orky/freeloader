from dataclasses import dataclass
from pathlib import Path

from freeloader.blocks.registry import BlockRegistry
from freeloader.projects.discovery import ProjectDiscovery
from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.projects.tech import detect_stack
from freeloader.projects.usecases.init_project.config_builder import ConfigBuilder
from freeloader.shared.yaml_io import save_yaml_model


@dataclass(frozen=True)
class InitProjectResult:
    manifest_path: str
    block_count: int
    project_name: str
    detected_stack: str


class InitProjectUseCases:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry
        self._config_builder = ConfigBuilder(registry)

    def init(self, project_dir: Path, name: str | None = None, full: bool = False) -> InitProjectResult:
        project_dir = project_dir.resolve()
        manifest_path = project_dir / ProjectDiscovery.MANIFEST_NAME

        detected = detect_stack(project_dir)
        project_name = name or project_dir.name

        default_contracts = self._registry.default_blocks()
        if detected and detected.dockerfile_template:
            names = {c.block.name for c in default_contracts}
            if "dockerfile" not in names:
                dockerfile = self._registry.get_block("dockerfile")
                default_contracts.append(dockerfile)

        chosen_blocks: list[BlockRef] = []
        for contract in default_contracts:
            config = self._config_builder.build(
                contract.block.name, project_name, full)
            chosen_blocks.append(
                BlockRef(use=contract.block.name, config=config))

        manifest = ProjectManifest(
            project=ProjectInfo(name=project_name, source_dir="."),
            blocks=chosen_blocks,
        )

        save_yaml_model(manifest_path, manifest)

        detected_stack = ""
        if detected:
            detected_stack = f"{detected.language}/{detected.package_manager} ({detected.framework})"

        return InitProjectResult(
            manifest_path=str(manifest_path),
            block_count=len(chosen_blocks),
            project_name=project_name,
            detected_stack=detected_stack,
        )
