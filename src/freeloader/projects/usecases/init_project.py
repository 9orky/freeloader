from dataclasses import dataclass
from pathlib import Path

from freeloader.blocks.registry import BlockRegistry
from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.projects.tech import detect_stack
from freeloader.shared.yaml_io import save_yaml_model

DEFAULT_BLOCKS = [
    "github-repo", "gitlab-registry", "aws-ec2",
    "dockerfile", "github-actions-ci", "coolify-project", "coolify-service",
]


@dataclass(frozen=True)
class InitProjectResult:
    manifest_path: str
    block_count: int
    project_name: str
    detected_stack: str


class InitProjectUseCases:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry

    def init(self, project_dir: Path, name: str | None = None, full: bool = False) -> InitProjectResult:
        project_dir = project_dir.resolve()
        manifest_path = project_dir / "freeloader.yaml"

        detected = detect_stack(project_dir)
        project_name = name or project_dir.name

        block_names = list(DEFAULT_BLOCKS)
        if detected and detected.dockerfile_template and "dockerfile" not in block_names:
            block_names.append("dockerfile")

        chosen_blocks: list[BlockRef] = []
        for block_name in block_names:
            if not self._registry.has_block(block_name):
                continue
            contract = self._registry.get_block(block_name)
            config: dict[str, str] = {}
            if full:
                for field_name, field_spec in contract.config.items():
                    if field_spec.required:
                        config[field_name] = project_name if field_name in (
                            "name", "app_name") else ""
                    elif field_spec.default is not None:
                        config[field_name] = field_spec.default
                    else:
                        config[field_name] = ""
            else:
                for field_name, field_spec in contract.config.items():
                    if field_spec.required:
                        config[field_name] = project_name if field_name in (
                            "name", "app_name") else ""
            chosen_blocks.append(BlockRef(use=block_name, config=config))

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
