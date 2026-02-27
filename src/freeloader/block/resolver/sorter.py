import heapq

from ..layer import LAYER_ORDER
from ..contract import BlockContract

from .base import BlockRef
from .error import CircularDependency


class TopologicalSorter:
    def sort(
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
            raise CircularDependency( "Circular dependency detected among blocks.")

        return {block_id: idx for idx, block_id in enumerate(sorted_order)}
