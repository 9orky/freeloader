from pathlib import Path

from freeloader.block.infrastructure import load_block_repository
import freeloader.block.infrastructure as infrastructure


def test_load_block_repository_uses_repo_src_blocks_by_default(monkeypatch) -> None:
    expected = Path(__file__).resolve().parents[1] / "src" / "blocks"
    captured: list[Path] = []

    monkeypatch.delenv("FREELOADER_BLOCKS", raising=False)
    monkeypatch.setattr(
        infrastructure.FileSystemBlockLoader,
        "init",
        classmethod(lambda cls, path: captured.append(path) or object()),
    )

    load_block_repository()

    assert captured == [expected]


def test_load_block_repository_allows_env_override(monkeypatch, tmp_path) -> None:
    captured: list[Path] = []

    monkeypatch.setenv("FREELOADER_BLOCKS", str(tmp_path))
    monkeypatch.setattr(
        infrastructure.FileSystemBlockLoader,
        "init",
        classmethod(lambda cls, path: captured.append(path) or object()),
    )

    load_block_repository()

    assert captured == [tmp_path]
