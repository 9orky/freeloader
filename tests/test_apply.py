from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import DAGResolver, ResolvedBlock
from freeloader.pipeline.orchestrator import Orchestrator, ExecutionGroup, ExecutionPlan
from freeloader.blocks.models import RunnerType
from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.pipeline.runners import RunnerRegistry
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.projects.state import StateManager
from freeloader.pipeline.usecases.apply import ApplyUseCases
from conftest import CONTRACTS, InMemoryBlockRegistry


class StubRunner(BaseRunner):
    def __init__(self, outputs: dict[str, dict[str, Any]] | None = None) -> None:
        self._outputs = outputs or {}

    def runner_name(self) -> str:
        return "stub"

    def check_feasibility(self, blocks: list[ResolvedBlock]) -> list:
        return []

    def plan(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> str:
        return "plan output"

    def apply(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> dict[str, dict[str, Any]]:
        return self._outputs

    def destroy(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> None:
        pass


def _build_apply_uc(
    tmp_home: Path,
    block_dir: Path,
    runner_outputs: dict[str, dict[str, Any]] | None = None,
) -> tuple[ApplyUseCases, ProjectManifest]:
    registry = InMemoryBlockRegistry(CONTRACTS, block_dir)
    vault = MagicMock()
    vault.list.return_value = ["GITHUB_TOKEN", "GITLAB_TOKEN"]
    vault.has.return_value = True
    vault.get.side_effect = lambda k: {
        "GITHUB_TOKEN": "t", "GITLAB_TOKEN": "t"}.get(k, "")

    from freeloader.projects.models import GlobalConfig

    config = GlobalConfig()
    state_dir = tmp_home / "projects" / "plan-test"
    state_mgr = StateManager("plan-test", state_dir)

    runner_registry = RunnerRegistry()
    stub = StubRunner(runner_outputs or {})
    runner_registry.register(RunnerType.terraform, stub)
    runner_registry.register(RunnerType.api, stub)
    runner_registry.register(RunnerType.generator, stub)

    orchestrator = Orchestrator(
        dag_resolver=DAGResolver(),
        runner_registry=runner_registry,
        state_manager=state_mgr,
        vault=vault,
        config=config,
        block_registry=registry,
    )

    manifest = ProjectManifest(
        project=ProjectInfo(name="plan-test"),
        blocks=[
            BlockRef(use="github-repo", config={"name": "my-app"}),
            BlockRef(use="gitlab-registry", config={"name": "my-app"}),
        ],
    )

    return ApplyUseCases(orchestrator), manifest


class TestPlan:
    def test_returns_plan_with_blocks(self, tmp_home: Path, block_dir: Path) -> None:
        uc, manifest = _build_apply_uc(tmp_home, block_dir)
        result = uc.plan(manifest)

        assert result.project_name == "plan-test"
        assert len(result.blocks) == 2
        block_ids = {b.block_id for b in result.blocks}
        assert "github-repo" in block_ids
        assert "gitlab-registry" in block_ids

    def test_plan_blocks_have_metadata(self, tmp_home: Path, block_dir: Path) -> None:
        uc, manifest = _build_apply_uc(tmp_home, block_dir)
        result = uc.plan(manifest)

        github = next(b for b in result.blocks if b.block_id == "github-repo")
        assert github.layer == "source"
        assert github.runner == "terraform"


class TestApply:
    def test_returns_outputs(self, tmp_home: Path, block_dir: Path) -> None:
        outputs = {
            "github-repo": {"source.repo_name": "org/repo"},
            "gitlab-registry": {"registry.host": "registry.gitlab.com"},
        }
        uc, manifest = _build_apply_uc(tmp_home, block_dir, outputs)
        result = uc.apply(manifest)

        assert result.project_name == "plan-test"
        assert "github-repo" in result.outputs


class TestDestroy:
    def test_returns_project_name(self, tmp_home: Path, block_dir: Path) -> None:
        uc, manifest = _build_apply_uc(tmp_home, block_dir)
        result = uc.destroy(manifest)
        assert result.project_name == "plan-test"
