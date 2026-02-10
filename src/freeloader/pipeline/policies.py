from __future__ import annotations

from typing import TYPE_CHECKING

from freeloader.blocks.models import BlockContract
from freeloader.blocks.policies import validate_block_exists
from freeloader.blocks.registry import BlockRegistry
from freeloader.credentials.resolver import SecretResolver
from freeloader.credentials.vault import SecretVault
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.projects.models import BlockRef, ProjectManifest
from freeloader.shared.errors import FeasibilityError, FeasibilityIssue, ConfigurationError


def validate_manifest_blocks(
    block_refs: list[BlockRef],
    registry: BlockRegistry,
) -> dict[str, BlockContract]:
    contracts: dict[str, BlockContract] = {}
    for ref in block_refs:
        contracts[ref.resolved_id] = validate_block_exists(ref.use, registry)
    return contracts


def check_secrets(
    manifest: ProjectManifest,
    registry: BlockRegistry,
    vault: SecretVault,
) -> list[str]:
    resolver = SecretResolver(registry, vault)
    gaps = resolver.ensure_secrets(manifest)
    return [g.key for g in gaps]


def check_block_feasibility(
    block: ResolvedBlock,
    runner: BaseRunner,
) -> None:
    issues = runner.check_feasibility(block)
    if issues:
        raise FeasibilityError(issues)
