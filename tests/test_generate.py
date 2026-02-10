from pathlib import Path

from freeloader.pipeline.dag import DAGResolver
from freeloader.pipeline.orchestrator import Preflight
from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.pipeline.usecases.generate import GenerateUseCases
from conftest import CONTRACTS, InMemoryBlockRegistry


def _build_generate_uc(block_dir: Path, output_dir: Path) -> tuple[GenerateUseCases, InMemoryBlockRegistry]:
    registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
    preflight = Preflight(DAGResolver(), registry, None)
    return GenerateUseCases(preflight, registry, output_dir), registry


class TestGenerate:
    def test_no_generator_blocks(self, block_dir: Path, tmp_path: Path) -> None:
        uc, _ = _build_generate_uc(block_dir, tmp_path)
        manifest = ProjectManifest(
            project=ProjectInfo(name="test"),
            blocks=[BlockRef(use="github_repo", config={"name": "test"})],
        )
        result = uc.generate(manifest)
        assert result.generated_block_ids == []

    def test_with_generator_block_and_templates(self, block_dir: Path, tmp_path: Path) -> None:
        templates_dir = block_dir / "dockerfile" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir /
         "Dockerfile.j2").write_text("FROM python:{{ config.template }}\n")

        uc, _ = _build_generate_uc(block_dir, tmp_path)
        manifest = ProjectManifest(
            project=ProjectInfo(name="test"),
            blocks=[BlockRef(use="dockerfile", config={
                             "template": "python-uv"})],
        )
        result = uc.generate(manifest)
        assert "dockerfile" in result.generated_block_ids

    def test_dockerfile_auto_template_empty_serve_with(self, block_dir: Path, tmp_path: Path) -> None:
        templates_dir = block_dir / "dockerfile" / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "node-npm-nginx.Dockerfile.j2").write_text(
            "FROM node:{{ config.node_version }}\n",
        )
        (templates_dir / "dockerignore.j2").write_text("node_modules\n")
        (tmp_path / "package.json").write_text("{}")

        uc, _ = _build_generate_uc(block_dir, tmp_path)
        manifest = ProjectManifest(
            project=ProjectInfo(name="test"),
            blocks=[BlockRef(use="dockerfile", config={
                "template": "auto", "node_version": "22", "serve_with": ""})],
        )
        result = uc.generate(manifest)
        assert "dockerfile" in result.generated_block_ids
        assert (tmp_path / "Dockerfile").exists()
        assert (tmp_path / ".dockerignore").exists()
