from dataclasses import dataclass, field
from pathlib import Path

from freeloader.block.context import ExecutionContext
from freeloader.block.contract import BlockContract, BlockMeta
from freeloader.block.layer import Layer
from freeloader.block.provisioner import Provisioner
from freeloader.block.resolver import BlockRef, ResolvedBlock


def test_execution_context_resolves_explicit_input_bindings() -> None:
    context = ExecutionContext()
    context.set_outputs("git.repo", {"url": "https://example.test/repo.git"})

    resolved_inputs = context.resolve_inputs({"build.url": "git.repo"})

    assert len(resolved_inputs) == 1
    assert resolved_inputs[0].reference.provider_id == "git.repo"
    assert resolved_inputs[0].reference.output_name == "url"
    assert resolved_inputs[0].tfvar_name == "build_url"
    assert resolved_inputs[0].value == "https://example.test/repo.git"


def test_provisioner_can_plan_without_runner_side_effects(tmp_path: Path) -> None:
    source_contract = _contract(Layer.source)
    build_contract = _contract(Layer.build)
    source_block = FakeBlock("git.repo", source_contract)
    build_block = FakeBlock("docker.image", build_contract)
    runner = FakeRunner()

    provisioner = Provisioner(
        tmp_path,
        FakeLoader({"git.repo": source_block, "docker.image": build_block}),
        runner,
    )
    provisioner._resolver = FakeResolver(
        [
            ResolvedBlock(BlockRef(use="git.repo"), source_contract, {}),
            ResolvedBlock(
                BlockRef(use="docker.image"),
                build_contract,
                {"build.url": "git.repo"},
            ),
        ]
    )

    plan = provisioner.plan(
        [BlockRef(use="git.repo"), BlockRef(use="docker.image")])

    assert plan.block_ids == ["git.repo", "docker.image"]
    assert runner.calls == []


def test_provisioner_returns_report_with_outputs_and_dependency_replan(tmp_path: Path) -> None:
    source_contract = _contract(Layer.source)
    build_contract = _contract(Layer.build)
    source_block = FakeBlock("git.repo", source_contract)
    build_block = FakeBlock("docker.image", build_contract)
    runner = FakeRunner(
        outputs_by_block={
            "git.repo": {"url": "https://example.test/repo.git"},
            "docker.image": {"image": "registry.example/app:latest"},
        }
    )

    provisioner = Provisioner(
        tmp_path,
        FakeLoader({"git.repo": source_block, "docker.image": build_block}),
        runner,
    )
    provisioner._resolver = FakeResolver(
        [
            ResolvedBlock(BlockRef(use="git.repo"), source_contract, {}),
            ResolvedBlock(
                BlockRef(use="docker.image"),
                build_contract,
                {"build.url": "git.repo"},
            ),
        ]
    )

    report = provisioner.provision(
        [BlockRef(use="git.repo"), BlockRef(use="docker.image")])

    assert report.plan.block_ids == ["git.repo", "docker.image"]
    assert report.outputs_by_block["git.repo"]["url"] == "https://example.test/repo.git"
    assert report.outputs_by_block["docker.image"]["image"] == "registry.example/app:latest"
    assert ("init_with_deps", "docker.image") in runner.calls
    assert any(
        step.had_dependency_inputs for step in report.applied_steps if step.block_id == "docker.image")


def _contract(layer: Layer) -> BlockContract:
    return BlockContract(block=BlockMeta(layer=layer))


@dataclass
class FakeBlock:
    block_id: str
    contract: BlockContract
    dumped_to: list[Path] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.block_id

    def dump_assets(self, folder: Path) -> None:
        self.dumped_to.append(folder)


@dataclass
class FakeLoader:
    blocks: dict[str, FakeBlock]

    def load_by_refs(self, block_refs: list[BlockRef]) -> dict[str, FakeBlock]:
        return self.blocks


@dataclass
class FakeResolver:
    resolved_blocks: list[ResolvedBlock]

    def resolve(
        self,
        block_refs: list[BlockRef],
        contracts: dict[str, BlockContract],
    ) -> list[ResolvedBlock]:
        return self.resolved_blocks


@dataclass
class FakeRunner:
    outputs_by_block: dict[str, dict[str, str]] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def run_init(self, resource, block: ResolvedBlock) -> None:
        self.calls.append(("init", block.id))

    def run_init_with_deps(self, resource, block: ResolvedBlock, context: ExecutionContext) -> None:
        self.calls.append(("init_with_deps", block.id))
        context.resolve_inputs(block.inputs)

    def run_plan(self, resource) -> None:
        self.calls.append(("plan", resource.folder.name))

    def run_apply(self, resource) -> dict[str, str]:
        self.calls.append(("apply", resource.folder.name))
        return self.outputs_by_block[resource.folder.name]

    def run_destroy(self, resource) -> None:
        self.calls.append(("destroy", resource.folder.name))
