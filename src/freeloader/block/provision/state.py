from enum import Enum
from typing import Any

from pydantic import BaseModel


class BlockStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class BlockRecord(BaseModel):
    status: BlockStatus
    outputs: dict[str, Any] = {}
    error: str | None = None


class ProvisionState(BaseModel):
    blocks: dict[str, BlockRecord] = {}
