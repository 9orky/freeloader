from pathlib import Path
from typing import Any

from ..context import ExecutionContext
from ..resolver.dag import ResolvedBlock
from .state import BlockRecord, BlockStatus, ProvisionState


class ProvisionProgress:
    def __init__(self, root: Path, resolved_blocks: list[ResolvedBlock]) -> None:
        self._state_file = root / "provision.json"
        self._state = self._load_state()

    def _load_state(self) -> ProvisionState:
        if not self._state_file.exists():
            return ProvisionState()
        
        state = ProvisionState.model_validate_json(self._state_file.read_text())
        for record in state.blocks.values():
            if record.status == BlockStatus.running:
                record.status = BlockStatus.pending
        return state

    def _save_state(self) -> None:
        self._state_file.write_text(self._state.model_dump_json(indent=2))

    def is_done(self, block_id: str) -> bool:
        record = self._state.blocks.get(block_id)
        return record is not None and record.status == BlockStatus.done

    def pending(self, all_blocks: list[ResolvedBlock]) -> list[ResolvedBlock]:
        return [b for b in all_blocks if not self.is_done(b.ref.resolved_id)]

    def mark_running(self, block_id: str) -> None:
        self._state.blocks[block_id] = BlockRecord(status=BlockStatus.running)
        self._save_state()

    def mark_done(self, block_id: str, outputs: dict[str, Any]) -> None:
        self._state.blocks[block_id] = BlockRecord( status=BlockStatus.done, outputs=outputs)
        self._save_state()

    def mark_failed(self, block_id: str, error: str) -> None:
        self._state.blocks[block_id] = BlockRecord(status=BlockStatus.failed, error=error)
        self._save_state()

    def restore_context(self, context: ExecutionContext) -> None:
        for block_id, record in self._state.blocks.items():
            if record.status == BlockStatus.done:
                context.set_outputs(block_id, record.outputs)
