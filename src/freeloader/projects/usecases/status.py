from dataclasses import dataclass
from pathlib import Path

from freeloader.projects.state import StateManager
from freeloader.shared.paths import FREELOADER_HOME, project_state_dir, project_resource_dir, blocks_dir, bundled_blocks_dir, config_path, secrets_path, hosts_path


@dataclass(frozen=True)
class StatusBlock:
    block_name: str
    status: str
    output_count: int
    last_applied: str
    error: str


@dataclass(frozen=True)
class PathsInfo:
    cwd: str
    freeloader_home: str
    config_path: str
    secrets_path: str
    hosts_path: str
    project_state_dir: str
    project_resource_dir: str
    user_blocks_dir: str
    bundled_blocks_dir: str


@dataclass(frozen=True)
class StatusResult:
    project_name: str
    blocks: list[StatusBlock]
    last_up: str
    last_down: str
    paths: PathsInfo | None = None


class StatusUseCases:
    def __init__(self, state_manager: StateManager) -> None:
        self._state_manager = state_manager

    def get(self, verbose: bool = False) -> StatusResult:
        state = self._state_manager.load()
        blocks = [
            StatusBlock(
                block_name=bs.block_name,
                status=bs.status.value,
                output_count=len(bs.outputs),
                last_applied=bs.last_applied.isoformat() if bs.last_applied else "never",
                error=bs.error or "",
            )
            for bs in sorted(state.blocks, key=lambda x: x.block_name)
        ]

        paths: PathsInfo | None = None
        if verbose:
            paths = PathsInfo(
                cwd=str(Path.cwd()),
                freeloader_home=str(FREELOADER_HOME),
                config_path=str(config_path()),
                secrets_path=str(secrets_path()),
                hosts_path=str(hosts_path()),
                project_state_dir=str(project_state_dir(state.project_name)),
                project_resource_dir=str(
                    project_resource_dir(state.project_name)),
                user_blocks_dir=str(blocks_dir()),
                bundled_blocks_dir=str(bundled_blocks_dir()),
            )

        return StatusResult(
            project_name=state.project_name,
            blocks=blocks,
            last_up=state.last_up.isoformat() if state.last_up else "",
            last_down=state.last_down.isoformat() if state.last_down else "",
            paths=paths,
        )
