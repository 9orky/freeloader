from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, computed_field

from .contract import BlockContract
from .layer import LAYER_ORDER


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


class DAGError(Exception):
    ...


class MissingRequirement(DAGError):
    ...


class AmbiguousProvider(DAGError):
    ...


class CircularDependency(DAGError):
    ...


class DuplicateBlockId(DAGError):
    ...


class DAGResolver:
    def resolve(
        self,
        block_refs: list[BlockRef],
        contracts: dict[str, BlockContract],
    ) -> list[ResolvedBlock]:
        seen: set[str] = set()
        for ref in block_refs:
            if ref.resolved_id in seen:
                raise DuplicateBlockId(
                    f"Duplicate block id: {ref.resolved_id!r}")
            seen.add(ref.resolved_id)

        provides_map = self._build_provides_map(block_refs, contracts)
        inputs_by_id: dict[str, dict[str, str]] = {
            ref.resolved_id: {} for ref in block_refs}
        adjacency: dict[str, set[str]] = {
            ref.resolved_id: set() for ref in block_refs}

        for ref in block_refs:
            contract = contracts[ref.use]
            for req_key, port_spec in contract.requires.items():
                providers = provides_map.get(req_key, [])
                if not providers:
                    if not port_spec.optional:
                        raise MissingRequirement(
                            f"Block {ref.resolved_id!r} requires {req_key!r} "
                            f"but no block in the pipeline provides it."
                        )
                    continue
                if len(providers) > 1:
                    raise AmbiguousProvider(
                        f"Port {req_key!r} is provided by multiple blocks: {providers}"
                    )
                provider_id = providers[0]
                inputs_by_id[ref.resolved_id][req_key] = provider_id
                adjacency[provider_id].add(ref.resolved_id)

        order = self._topological_sort(block_refs, adjacency, contracts)
        sorted_refs = sorted(block_refs, key=lambda r: order[r.resolved_id])
        return [
            ResolvedBlock(
                ref=ref,
                contract=contracts[ref.use],
                inputs=inputs_by_id[ref.resolved_id],
            )
            for ref in sorted_refs
        ]

    def _build_provides_map(
        self,
        block_refs: list[BlockRef],
        contracts: dict[str, BlockContract],
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for ref in block_refs:
            contract = contracts[ref.use]
            layer = contract.block.layer.value
            for output_name in contract.provides:
                key = f"{layer}.{output_name}"
                result.setdefault(key, []).append(ref.resolved_id)
        return result

    def _topological_sort(
        self,
        block_refs: list[BlockRef],
        adjacency: dict[str, set[str]],
        contracts: dict[str, BlockContract],
    ) -> dict[str, int]:
        in_degree: dict[str, int] = {ref.resolved_id: 0 for ref in block_refs}
        for dependents in adjacency.values():
            for dep in dependents:
                in_degree[dep] += 1

        layer_priority: dict[str, int] = {}
        original_index: dict[str, int] = {}
        for idx, ref in enumerate(block_refs):
            contract = contracts[ref.use]
            layer_priority[ref.resolved_id] = LAYER_ORDER[contract.block.layer]
            original_index[ref.resolved_id] = idx

        heap: list[tuple[int, int, str]] = []
        for ref in block_refs:
            if in_degree[ref.resolved_id] == 0:
                heapq.heappush(
                    heap,
                    (layer_priority[ref.resolved_id],
                     original_index[ref.resolved_id], ref.resolved_id),
                )

        sorted_order: list[str] = []
        while heap:
            _, _, block_id = heapq.heappop(heap)
            sorted_order.append(block_id)
            for dep in adjacency[block_id]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    heapq.heappush(
                        heap,
                        (layer_priority[dep], original_index[dep], dep),
                    )

        if len(sorted_order) != len(block_refs):
            raise CircularDependency(
                "Circular dependency detected among blocks.")

        return {block_id: idx for idx, block_id in enumerate(sorted_order)}
