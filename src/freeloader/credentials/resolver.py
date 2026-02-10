from dataclasses import dataclass

from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.vault import SecretVault
from freeloader.projects.models import ProjectManifest


@dataclass(frozen=True)
class SecretGap:
    key: str
    required_by: list[str]


class SecretResolver:
    def __init__(self, registry: BlockRegistry, vault: SecretVault) -> None:
        self._registry = registry
        self._vault = vault

    def collect_required(self, manifest: ProjectManifest) -> dict[str, list[str]]:
        required: dict[str, list[str]] = {}
        for ref in manifest.blocks:
            contract = self._registry.get_block(ref.use)
            for secret_key in contract.block.required_secrets:
                required.setdefault(secret_key, []).append(ref.resolved_id)
        return required

    def collect_for_provider(self, provider: str) -> dict[str, list[str]]:
        required: dict[str, list[str]] = {}
        for contract in self._registry.list_blocks():
            if contract.block.provider != provider:
                continue
            for secret_key in contract.block.required_secrets:
                required.setdefault(secret_key, []).append(contract.block.name)
        return required

    def find_missing(self, required: dict[str, list[str]]) -> list[SecretGap]:
        return [
            SecretGap(key=key, required_by=blocks)
            for key, blocks in sorted(required.items())
            if not self._vault.has(key)
        ]

    def find_present(self, required: dict[str, list[str]]) -> list[str]:
        return sorted(key for key in required if self._vault.has(key))

    def store(self, key: str, value: str) -> None:
        self._vault.set(key, value)

    def ensure_secrets(self, manifest: ProjectManifest) -> list[SecretGap]:
        required = self.collect_required(manifest)
        return self.find_missing(required)
