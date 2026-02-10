from __future__ import annotations

from typing import TYPE_CHECKING

from freeloader.blocks.models import BlockContract
from freeloader.blocks.registry import BlockRegistry
from freeloader.pipeline.runners import RunnerRegistry
from freeloader.credentials.resolver import SecretResolver
from freeloader.credentials.vault import SecretVault
from freeloader.projects.models import BlockRef, ProjectManifest
from freeloader.shared.errors import FeasibilityError, FeasibilityIssue, ConfigurationError

if TYPE_CHECKING:
    from freeloader.pipeline.orchestrator import ExecutionGroup


def validate_manifest_blocks(
    block_refs: list[BlockRef],
    registry: BlockRegistry,
) -> dict[str, BlockContract]:
    contracts: dict[str, BlockContract] = {}
    for ref in block_refs:
        if not registry.has_block(ref.use):
            raise ConfigurationError(
                f"Block '{ref.use}' not found in catalog. "
                f"Run 'fl blocks list' to see available blocks."
            )
        contracts[ref.resolved_id] = registry.get_block(ref.use)
    return contracts


def check_secrets(
    manifest: ProjectManifest,
    registry: BlockRegistry,
    vault: SecretVault,
) -> list[str]:
    resolver = SecretResolver(registry, vault)
    gaps = resolver.ensure_secrets(manifest)
    return [g.key for g in gaps]


def check_all_runners_feasibility(
    groups: list[ExecutionGroup],
    runner_registry: RunnerRegistry,
) -> None:
    all_issues: list[FeasibilityIssue] = []
    for group in groups:
        runner = runner_registry.get(group.runner_type)
        issues = runner.check_feasibility(group.blocks)
        all_issues.extend(issues)
    if all_issues:
        raise FeasibilityError(all_issues)
