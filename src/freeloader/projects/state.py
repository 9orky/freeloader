import json
from pathlib import Path

from freeloader.projects.models import BlockState, BlockStatus, ProjectState
from freeloader.shared.paths import project_state_dir


class StateManager:
    def __init__(self, project_name: str, base_dir: Path | None = None) -> None:
        self._project_name = project_name
        self._dir = base_dir or project_state_dir(project_name)
        self._state_path = self._dir / "state.json"

    def load(self) -> ProjectState:
        if not self._state_path.exists():
            return ProjectState(project_name=self._project_name)
        data = json.loads(self._state_path.read_text())
        return ProjectState.model_validate(data)

    def save(self, state: ProjectState) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(state.model_dump(mode="json"), indent=2)
        )

    def get_block_state(self, state: ProjectState, block_name: str) -> BlockState | None:
        for bs in state.blocks:
            if bs.block_name == block_name:
                return bs
        return None

    def update_block(
        self,
        state: ProjectState,
        block_name: str,
        block_use: str,
        status: BlockStatus,
        outputs: dict | None = None,
        error: str | None = None,
    ) -> ProjectState:
        from datetime import datetime, timezone

        existing = self.get_block_state(state, block_name)
        new_bs = BlockState(
            block_name=block_name,
            block_use=block_use,
            status=status,
            outputs=outputs or (existing.outputs if existing else {}),
            last_applied=datetime.now(timezone.utc),
            error=error,
        )
        blocks = [bs for bs in state.blocks if bs.block_name != block_name]
        blocks.append(new_bs)
        return state.model_copy(update={"blocks": blocks})
