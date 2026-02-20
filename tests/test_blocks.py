from __future__ import annotations

from pathlib import Path

import pytest

from freeloader.shared.block import BlocksRootInvalid, validate_blocks_root

BLOCKS_ROOT = Path(__file__).parent.parent / "src" / "freeloader" / "blocks"


def test_blocks() -> None:
    msg: str | None = None
    try:
        validate_blocks_root(BLOCKS_ROOT)
    except BlocksRootInvalid as exc:
        msg = str(exc)
    if msg is not None:
        pytest.fail(msg, pytrace=False)
