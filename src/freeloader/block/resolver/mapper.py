from .base import BlockRef

from ..contract import BlockContract


class ProvidesMapper:
    def build_map( self, block_refs: list[BlockRef], contracts: dict[str, BlockContract]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for ref in block_refs:
            contract = contracts[ref.use]
            layer = contract.block.layer.value
            for output_name in contract.provides:
                key = f"{layer}.{output_name}"
                result.setdefault(key, []).append(ref.resolved_id)
        return result
