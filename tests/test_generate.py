from pathlib import Path

from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.pipeline.usecases.generate import GenerateUseCases
from conftest import CONTRACTS, InMemoryBlockRegistry


class TestGenerate:
    def test_no_generator_blocks(self, block_dir: Path, tmp_path: Path) -> None:
        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        manifest = ProjectManifest(
            project=ProjectInfo(name="test"),
            blocks=[BlockRef(use="github-repo", config={"name": "test"})],
        )
        uc = GenerateUseCases(registry, tmp_path)
        result = uc.generate(manifest)
        assert result.generated_block_ids == []

    def test_with_generator_block_and_templates(self, block_dir: Path, tmp_path: Path) -> None:
        templates_dir = block_dir / "dockerfile" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir /
         "Dockerfile.j2").write_text("FROM python:{{ config.template }}\n")

        registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
        manifest = ProjectManifest(
            project=ProjectInfo(name="test"),
            blocks=[BlockRef(use="dockerfile", config={
                             "template": "python-uv"})],
        )
        uc = GenerateUseCases(registry, tmp_path)
        result = uc.generate(manifest)
        assert "dockerfile" in result.generated_block_ids
