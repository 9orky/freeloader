import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class ProgressStatus(str, Enum):
    pending = "pending"
    planned = "planned"
    applied = "applied"
    failed = "failed"


class BlockProgress(BaseModel):
    block_id: str
    block_use: str
    runner: str
    status: ProgressStatus = ProgressStatus.pending
    last_error: str | None = None


class PipelineProgress(BaseModel):
    project_name: str
    action: str
    blocks: list[BlockProgress]
    started_at: datetime
    updated_at: datetime


class ProgressTracker:
    def __init__(self, progress_dir: Path) -> None:
        self._dir = progress_dir

    def load(self, project_name: str) -> PipelineProgress | None:
        path = self._path(project_name)
        if not path.exists():
            return None
        return PipelineProgress.model_validate(json.loads(path.read_text()))

    def create(self, project_name: str, action: str, blocks: list[BlockProgress]) -> PipelineProgress:
        now = datetime.now(timezone.utc)
        progress = PipelineProgress(
            project_name=project_name,
            action=action,
            blocks=blocks,
            started_at=now,
            updated_at=now,
        )
        self.save(progress)
        return progress

    def mark_planned(self, progress: PipelineProgress, block_id: str) -> PipelineProgress:
        return self._update_status(progress, block_id, ProgressStatus.planned)

    def mark_applied(self, progress: PipelineProgress, block_id: str) -> PipelineProgress:
        return self._update_status(progress, block_id, ProgressStatus.applied)

    def mark_failed(self, progress: PipelineProgress, block_id: str, error: str) -> PipelineProgress:
        return self._update_status(progress, block_id, ProgressStatus.failed, error)

    def save(self, progress: PipelineProgress) -> None:
        path = self._path(progress.project_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(progress.model_dump(mode="json"), indent=2))

    def clear(self, project_name: str) -> None:
        path = self._path(project_name)
        if path.exists():
            path.unlink()

    def _path(self, project_name: str) -> Path:
        return self._dir / project_name / "progress.json"

    def _update_status(
        self,
        progress: PipelineProgress,
        block_id: str,
        status: ProgressStatus,
        error: str | None = None,
    ) -> PipelineProgress:
        updated_blocks = [
            bp.model_copy(update={"status": status, "last_error": error})
            if bp.block_id == block_id else bp
            for bp in progress.blocks
        ]
        updated = progress.model_copy(update={
            "blocks": updated_blocks,
            "updated_at": datetime.now(timezone.utc),
        })
        self.save(updated)
        return updated
