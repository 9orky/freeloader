from pathlib import Path

from pydantic import BaseModel

from ..context import ExecutionContext
from ..dag import ResolvedBlock


class ProvisionProgress:
    def __init__(self, root: Path, resolved_blocks: list[ResolvedBlock]) -> None:
        self.root = root
        self.resolved_blocks = resolved_blocks

    def _load_state(self):
        state_file = self.root / "provision.json"

    def is_block_done(self, block: ResolvedBlock) -> bool:
        pass

    def mark_running(self, block: ResolvedBlock):
        pass

    def mark_done(self, block: ResolvedBlock):
        pass

    def mark_failed(self, block: ResolvedBlock, error: str):
        pass

    def restore_context(self, context: ExecutionContext):
        pass