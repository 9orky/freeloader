from __future__ import annotations

from pathlib import Path

import pytest

from freeloader.block.infrastructure import BlockLoader

BLOCKS_ROOT = Path(__file__).parent.parent / "src" / "blocks"


def test_blocks_load() -> None:
    loader = BlockLoader.init(BLOCKS_ROOT)
    blocks = loader.all_blocks
    assert blocks, "No blocks found"

    for block_id, block in blocks.items():
        contract = block.contract
        assert contract.block.layer, f"Block {block_id} has no layer"
        assert contract.config is not None, f"Block {block_id} has no config"

        for field in contract.config:
            assert field.group in ("basic", "advanced", "secrets"), (
                f"Block {block_id} field {field.name} has invalid group {field.group}"
            )


def test_tech_stack_blocks_have_tech_fields() -> None:
    loader = BlockLoader.init(BLOCKS_ROOT)
    for block_id, block in loader.all_blocks.items():
        contract = block.contract
        if contract.block.required_tech_stack:
            assert contract.tech_stack_field_names, (
                f"Block {block_id} is marked required_tech_stack but has no tech stack fields"
            )
