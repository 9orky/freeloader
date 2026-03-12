from __future__ import annotations

from pathlib import Path

from freeloader.block.infrastructure.loader import FileSystemBlockLoader
from freeloader.shared.tech import TECH_STACK_FIELD_NAMES

BLOCKS_ROOT = Path(__file__).parent.parent / "src" / "blocks"


def test_blocks_load() -> None:
    loader = FileSystemBlockLoader.init(BLOCKS_ROOT)
    blocks = loader.load_all()
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
    loader = FileSystemBlockLoader.init(BLOCKS_ROOT)
    for block_id, block in loader.load_all().items():
        contract = block.contract
        if contract.block.required_tech_stack:
            tech_stack_fields = [
                field.name for field in contract.config if field.name in TECH_STACK_FIELD_NAMES
            ]
            assert tech_stack_fields, (
                f"Block {block_id} is marked required_tech_stack but has no tech stack fields"
            )
