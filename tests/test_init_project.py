from pathlib import Path

import yaml

from freeloader.projects.usecases.init_project import InitProjectUseCases
from conftest import InMemoryBlockRegistry, CONTRACTS


class TestInitProject:
    def test_creates_manifest(self, tmp_path: Path, block_dir: Path) -> None:
        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        uc = InitProjectUseCases(registry)
        result = uc.init(tmp_path, "test-proj")

        assert result.project_name == "test-proj"
        assert result.block_count > 0
        assert (tmp_path / "freeloader.yaml").exists()

    def test_manifest_has_correct_project_name(self, tmp_path: Path, block_dir: Path) -> None:
        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        uc = InitProjectUseCases(registry)
        uc.init(tmp_path, "my-saas")

        data = yaml.safe_load((tmp_path / "freeloader.yaml").read_text())
        assert data["project"]["name"] == "my-saas"

    def test_uses_dir_name_when_no_name(self, tmp_path: Path, block_dir: Path) -> None:
        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        uc = InitProjectUseCases(registry)
        result = uc.init(tmp_path)

        assert result.project_name == tmp_path.name

    def test_detects_python_stack(self, tmp_path: Path, block_dir: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.uv]\n")
        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        uc = InitProjectUseCases(registry)
        result = uc.init(tmp_path, "py-proj")

        assert "python" in result.detected_stack
        assert "uv" in result.detected_stack

    def test_only_includes_available_blocks(self, tmp_path: Path, block_dir: Path) -> None:
        limited = {"github_repo": CONTRACTS["github_repo"]}
        registry = InMemoryBlockRegistry(limited, block_dir)
        uc = InitProjectUseCases(registry)
        result = uc.init(tmp_path, "limited")

        assert result.block_count == 1
