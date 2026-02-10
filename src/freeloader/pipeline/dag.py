from collections import defaultdict, deque
from dataclasses import dataclass

from freeloader.pipeline.blocks.models import BlockContract
from freeloader.projects.models import BlockRef
from freeloader.shared.errors import FreloaderError


@dataclass(frozen=True)
class ResolvedBlock:
    ref: BlockRef
    contract: BlockContract
    inputs: dict[str, str]


class DAGError(FreloaderError):
    ...


class MissingRequirement(DAGError):
    ...


class AmbiguousProvider(DAGError):
    ...


class CircularDependency(DAGError):
    ...


class DAGResolver:
    def resolve(
        self,
        block_refs: list[BlockRef],
        contracts: dict[str, BlockContract],
    ) -> list[ResolvedBlock]:
        provides_map = self._build_provides_map(block_refs, contracts)
        wires: dict[str, dict[str, str]] = {}
        adjacency: dict[str, set[str]] = defaultdict(set)

        for ref in block_refs:
            block_id = ref.resolved_id
            contract = contracts[block_id]
            block_inputs: dict[str, str] = {}

            for req_key, port in contract.requires.items():
                providers = provides_map.get(req_key, [])
                providers = [p for p in providers if p != block_id]

                if not providers:
                    if port.optional:
                        continue
                    raise MissingRequirement(
                        f"Block '{block_id}' requires '{req_key}' but no block provides it")

                if len(providers) > 1:
                    raise AmbiguousProvider(
                        f"Block '{block_id}' requires '{req_key}' but multiple blocks provide it: {providers}"
                    )

                provider_id = providers[0]
                block_inputs[req_key] = provider_id
                adjacency[block_id].add(provider_id)

            wires[block_id] = block_inputs

        order = self._topological_sort(block_refs, adjacency)

        return [
            ResolvedBlock(
                ref=ref,
                contract=contracts[ref.resolved_id],
                inputs=wires.get(ref.resolved_id, {}),
            )
            for ref in sorted(block_refs, key=lambda r: order[r.resolved_id])
        ]

    def _build_provides_map(
        self,
        block_refs: list[BlockRef],
        contracts: dict[str, BlockContract],
    ) -> dict[str, list[str]]:
        provides_map: dict[str, list[str]] = defaultdict(list)
        for ref in block_refs:
            block_id = ref.resolved_id
            contract = contracts[block_id]
            for port_key in contract.provides:
                provides_map[port_key].append(block_id)
        return provides_map

    def _topological_sort(
        self,
        block_refs: list[BlockRef],
        adjacency: dict[str, set[str]],
    ) -> dict[str, int]:
        all_ids = {ref.resolved_id for ref in block_refs}
        in_degree: dict[str, int] = {bid: 0 for bid in all_ids}

        for node, deps in adjacency.items():
            for dep in deps:
                if dep in all_ids:
                    in_degree[node] = in_degree.get(node, 0)

        reverse_adj: dict[str, set[str]] = defaultdict(set)
        for node, deps in adjacency.items():
            for dep in deps:
                reverse_adj[dep].add(node)
                in_degree[node] = in_degree.get(node, 0)

        for node in all_ids:
            in_degree.setdefault(node, 0)

        in_degree_calc: dict[str, int] = {bid: 0 for bid in all_ids}
        for node, deps in adjacency.items():
            in_degree_calc[node] = len(deps & all_ids)

        queue: deque[str] = deque(
            bid for bid, deg in in_degree_calc.items() if deg == 0)
        order: dict[str, int] = {}
        pos = 0

        while queue:
            node = queue.popleft()
            order[node] = pos
            pos += 1
            for dependent in reverse_adj.get(node, set()):
                in_degree_calc[dependent] -= 1
                if in_degree_calc[dependent] == 0:
                    queue.append(dependent)

        if len(order) != len(all_ids):
            missing = all_ids - set(order.keys())
            raise CircularDependency(
                f"Circular dependency detected involving: {missing}")

        return order
