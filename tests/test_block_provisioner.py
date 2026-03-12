from dataclasses import dataclass, field
from pathlib import Path

from freeloader.block.application import commands
from freeloader.block.application.services.provisioner import BlockProvisioningService
from freeloader.block.domain import Layer
from freeloader.block.domain.entity import Block, BlockContract, BlockMeta, BlockRef, PortSpec
from freeloader.block.domain.repository import BlockRepository
from freeloader.block.domain.value_object import BlockId


def test_service_can_build_plan_without_runner_side_effects() -> None:
    repository = FakeBlockRepository(
        {
            "git.repo": _block("git.repo", layer=Layer.source, provides={"url": PortSpec()}),
            "docker.image": _block(
                "docker.image",
                layer=Layer.build,
                requires={"source.url": PortSpec()},
            ),
        }
    )
    runner = FakeRunner()

    plan = BlockProvisioningService(repository, runner).build_plan(
        [BlockRef(use="git.repo"), BlockRef(use="docker.image")]
    )

    assert plan.block_ids == ["git.repo", "docker.image"]
    assert runner.calls == []


def test_service_returns_report_with_outputs_and_dependency_replan(tmp_path: Path) -> None:
    repository = FakeBlockRepository(
        {
            "git.repo": _block("git.repo", layer=Layer.source, provides={"url": PortSpec()}),
            "docker.image": _block(
                "docker.image",
                layer=Layer.build,
                requires={"source.url": PortSpec()},
            ),
        }
    )
    runner = FakeRunner(
        outputs_by_block={
            "git.repo": {"url": "https://example.test/repo.git"},
            "docker.image": {"image": "registry.example/app:latest"},
        }
    )

    report = BlockProvisioningService(repository, runner).provision(
        tmp_path,
        [BlockRef(use="git.repo"), BlockRef(use="docker.image")],
    )

    assert report.plan.block_ids == ["git.repo", "docker.image"]
    assert report.outputs_by_block["git.repo"]["url"] == "https://example.test/repo.git"
    assert report.outputs_by_block["docker.image"]["image"] == "registry.example/app:latest"
    assert repository.dumped_ids == ["git.repo", "docker.image"]
    assert runner.calls == [
        ("init", "git.repo", None),
        ("plan", "git.repo", None),
        ("init", "docker.image", None),
        ("plan", "docker.image", None),
        ("apply", "git.repo", None),
        ("init", "docker.image", {
         "source_url": "https://example.test/repo.git"}),
        ("plan", "docker.image", None),
        ("apply", "docker.image", None),
    ]
    assert any(
        step.had_dependency_inputs for step in report.applied_steps if step.block_id == "docker.image")


def test_provision_command_wires_repository_runner_and_service(monkeypatch, tmp_path: Path) -> None:
    repository = object()
    runner = object()
    captured: dict[str, object] = {}
    expected_refs = [BlockRef(use="git.repo")]
    expected_report = object()

    monkeypatch.setattr(commands, "load_block_repository", lambda: repository)

    def fake_load_block_runner(project_root: Path) -> object:
        captured["runner_arg"] = project_root
        return runner

    monkeypatch.setattr(commands, "load_block_runner", fake_load_block_runner)

    class FakeService:
        def __init__(self, loaded_repository: object, runner: object) -> None:
            captured["service_args"] = (loaded_repository, runner)

        def provision(self, resources_root: Path, block_refs: list[BlockRef]) -> object:
            captured["provision_args"] = (resources_root, block_refs)
            return expected_report

    monkeypatch.setattr(commands, "BlockProvisioningService", FakeService)

    report = commands.provision_blocks(
        tmp_path, tmp_path / ".freeloader", expected_refs)

    assert report is expected_report
    assert captured["runner_arg"] == tmp_path
    assert captured["service_args"] == (repository, runner)
    assert captured["provision_args"] == (
        tmp_path / ".freeloader", expected_refs)


@dataclass
class FakeBlockRepository(BlockRepository):
    blocks: dict[str, Block]
    dumped_ids: list[str] = field(default_factory=list)

    def load_all(self) -> dict[str, Block]:
        return self.blocks

    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]:
        return {str(block_id): self.blocks[str(block_id)] for block_id in block_ids}

    def dump_assets(self, block_id: BlockId, target: Path) -> None:
        self.dumped_ids.append(str(block_id))
        target.mkdir(parents=True, exist_ok=True)


def _block(
    block_id: str,
    *,
    layer: Layer,
    provides: dict[str, PortSpec] | None = None,
    requires: dict[str, PortSpec] | None = None,
) -> Block:
    return Block(
        id=BlockId(block_id),
        contract=BlockContract(
            block=BlockMeta(layer=layer),
            provides=provides or {},
            requires=requires or {},
        ),
    )


@dataclass
class FakeRunner:
    outputs_by_block: dict[str, dict[str, str]] = field(default_factory=dict)
    calls: list[tuple[str, str, dict[str, str] | None]
                ] = field(default_factory=list)

    def run_init(self, resource, block, extra_vars=None) -> None:
        self.calls.append(("init", block.id, extra_vars))

    def run_plan(self, resource) -> None:
        self.calls.append(("plan", resource.folder.name, None))

    def run_apply(self, resource) -> dict[str, str]:
        self.calls.append(("apply", resource.folder.name, None))
        return self.outputs_by_block[resource.folder.name]

    def run_destroy(self, resource) -> None:
        self.calls.append(("destroy", resource.folder.name, None))
