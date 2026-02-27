from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, computed_field

from ..contract import BlockContract


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, Any] = {}

    @computed_field
    @property
    def resolved_id(self) -> str:
        return self.id or self.use


@dataclass(frozen=True)
class ResolvedBlock:
    ref: BlockRef
    contract: BlockContract
    inputs: dict[str, str]

    @property
    def id(self) -> str:
        return self.ref.resolved_id
