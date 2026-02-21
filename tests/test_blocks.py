from __future__ import annotations

from pathlib import Path

import pytest

from freeloader.shared.block import Blocks

BLOCKS_ROOT = Path(__file__).parent.parent / "src" / "freeloader" / "blocks"


def test_blocks() -> None:
    msg: str | None = None
    try:
        Blocks(str(BLOCKS_ROOT))
    except Exception as exc:
        msg = str(exc)
    if msg is not None:
        pytest.fail(msg, pytrace=False)
