from __future__ import annotations

from typing import TYPE_CHECKING

from freeloader.pipeline.blocks.models import BlockContract, ConfigField
from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.resolver import SecretResolver
from freeloader.credentials.vault import SecretVault
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.projects.models import BlockRef, ProjectManifest
from freeloader.shared.errors import FeasibilityError, FeasibilityIssue, ConfigurationError

NAME_FIELDS = ("name", "app_name")


def validate_block_exists(name: str, registry: BlockRegistry) -> BlockContract:
    if not registry.has_block(name):
        available = ", ".join(c.block.name for c in registry.list_blocks())
        raise ConfigurationError(
            f"Block '{name}' not found in catalog.\n"
            f"Available blocks: {available}\n"
            f"Run 'fl pipeline blocks' to see details."
        )
    return registry.get_block(name)


def validate_config(
    block_name: str,
    config: dict[str, str],
    fields: dict[str, ConfigField],
) -> None:
    for field_name, field_spec in fields.items():
        if field_spec.required and field_name not in NAME_FIELDS and not config.get(field_name):
            raise ConfigurationError(
                f"Block '{block_name}': required config field '{field_name}' is empty.\n"
                f"Set it in freeloader.yaml under the block's config section."
            )
        value = config.get(field_name)
        if value and field_spec.choices and value not in field_spec.choices:
            raise ConfigurationError(
                f"Block '{block_name}': config field '{field_name}' has invalid value '{value}'.\n"
                f"Allowed values: {', '.join(field_spec.choices)}"
            )


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
