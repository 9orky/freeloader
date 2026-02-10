from freeloader.pipeline.dag import DAGResolver, ResolvedBlock
from freeloader.pipeline.policies import validate_manifest_blocks, check_secrets
from freeloader.projects.models import ProjectManifest
from freeloader.shared.errors import ConfigurationError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freeloader.pipeline.blocks.registry import BlockRegistry
    from freeloader.credentials.vault import SecretVault


class Preflight:
    def __init__(
        self,
        dag_resolver: DAGResolver,
        block_registry: "BlockRegistry",
        vault: "SecretVault",
    ) -> None:
        self._dag = dag_resolver
        self._blocks = block_registry
        self._vault = vault

    def resolve(self, manifest: ProjectManifest) -> list[ResolvedBlock]:
        contracts = validate_manifest_blocks(manifest.blocks, self._blocks)
        return self._dag.resolve(manifest.blocks, contracts)

    def check_secrets(self, manifest: ProjectManifest) -> None:
        missing = check_secrets(manifest, self._blocks, self._vault)
        if missing:
            raise ConfigurationError(
                f"Missing secrets: {', '.join(missing)}\n"
                "Run 'fl credentials add-provider <provider>' to configure them."
            )
