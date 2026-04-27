import dataclasses
from collections.abc import Iterator
from pathlib import Path

from freeloader.block import Blocks
from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent, BlockRef

from ..domain.entity import CandidateBlock, TechStack
from ..domain.repository import BlockGateway


class BlockSystemGateway(BlockGateway):
    def get_manifest_candidates(
        self,
        project_root: Path,
        tech_stack: TechStack,
        full_manifest: bool,
        project_name: str | None,
    ) -> tuple[CandidateBlock, ...]:
        stack_dict = {
            k: v
            for k, v in dataclasses.asdict(tech_stack).items()
            if v is not None
        }
        candidates = Blocks.for_project(project_root).manifest_candidates(
            stack_dict, full_manifest, project_name
        )
        return tuple(
            CandidateBlock(
                block_id=str(candidate.id),
                provider=candidate.provider,
                config=candidate.config,
                required_secret_keys=candidate.required_secret_keys,
                required_tech_fields=candidate.required_tech_fields,
                required_tech_stack=candidate.required_tech_stack,
            )
            for candidate in candidates
        )

    def provision(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).provision(resources_root, block_refs)

    def provision_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockProvisionEvent]:
        return Blocks.for_project(project_root).provision_events(resources_root, block_refs)

    def destroy(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).destroy(resources_root, block_refs)

    def destroy_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockDestroyEvent]:
        return Blocks.for_project(project_root).destroy_events(resources_root, block_refs)
