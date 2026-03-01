from ..contract import BlockContract

from .base import BlockRef, ResolvedBlock
from .error import AmbiguousProvider, MissingRequirement
from .mapper import ProvidesMapper
from .sorter import TopologicalSorter


class DAGResolver:
    def __init__(self) -> None:
        self._mapper = ProvidesMapper()
        self._sorter = TopologicalSorter()
    
    def resolve( self, refs: list[BlockRef], contracts: dict[str, BlockContract]) -> list[ResolvedBlock]:
        provides_map = self._mapper.build_map(refs, contracts)

        inputs_by_id: dict[str, dict[str, str]] = { ref.resolved_id: {} for ref in refs}
        adjacency: dict[str, set[str]] = { ref.resolved_id: set() for ref in refs}

        for ref in refs:
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

        order = self._sorter.sort(refs, adjacency, contracts)
        sorted_refs = sorted(refs, key=lambda r: order[r.resolved_id])
        
        return [
            ResolvedBlock(
                ref=ref,
                contract=contracts[ref.use],
                inputs=inputs_by_id[ref.resolved_id],
            )
            for ref in sorted_refs
        ]
