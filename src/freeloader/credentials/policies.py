from freeloader.credentials.resolver import SecretResolver
from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.vault import SecretVault


def collect_provider_secrets(
    provider: str,
    registry: BlockRegistry,
    vault: SecretVault,
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    resolver = SecretResolver(registry, vault)
    required = resolver.collect_for_provider(provider)
    missing = [g.key for g in resolver.find_missing(required)]
    present = resolver.find_present(required)
    return required, missing, present


def store_missing_secrets(
    missing_keys: list[str],
    secret_values: dict[str, str],
    resolver: SecretResolver,
) -> list[str]:
    stored: list[str] = []
    for key in missing_keys:
        if key in secret_values:
            resolver.store(key, secret_values[key])
            stored.append(key)
    return stored


def collect_all_providers(registry: BlockRegistry) -> dict[str, list[str]]:
    providers: dict[str, list[str]] = {}
    for contract in registry.list_blocks():
        if contract.block.provider:
            providers.setdefault(contract.block.provider, [])
            for key in contract.block.required_secrets:
                if key not in providers[contract.block.provider]:
                    providers[contract.block.provider].append(key)
    return providers
