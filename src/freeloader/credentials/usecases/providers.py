from dataclasses import dataclass

from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.checkers import CheckerRegistry, CredentialStatus
from freeloader.credentials.policies import collect_provider_secrets, store_missing_secrets, collect_all_providers
from freeloader.credentials.resolver import SecretResolver
from freeloader.credentials.vault import SecretVault
from freeloader.projects.config import ConfigLoader
from freeloader.projects.models import ProviderConfig


@dataclass(frozen=True)
class AddProviderResult:
    stored_keys: list[str]
    already_present: list[str]
    credential_status: CredentialStatus


@dataclass(frozen=True)
class ProviderCheckRow:
    provider: str
    valid: bool
    detail: str


@dataclass(frozen=True)
class CheckProvidersResult:
    rows: list[ProviderCheckRow]


@dataclass(frozen=True)
class ProviderSecretsInfo:
    provider: str
    secrets: list[tuple[str, bool]]


@dataclass(frozen=True)
class ListProvidersResult:
    providers: list[ProviderSecretsInfo]


@dataclass(frozen=True)
class ListRequiredSecretsResult:
    required: dict[str, list[str]]
    missing_keys: list[str]


class ProviderUseCases:
    def __init__(
        self,
        registry: BlockRegistry,
        vault: SecretVault,
        config_loader: ConfigLoader,
        checker: CheckerRegistry,
    ) -> None:
        self._registry = registry
        self._vault = vault
        self._config_loader = config_loader
        self._checker = checker

    def list_required_secrets(self, provider: str) -> ListRequiredSecretsResult:
        required, missing, _ = collect_provider_secrets(
            provider, self._registry, self._vault)
        return ListRequiredSecretsResult(required=required, missing_keys=missing)

    def add(self, provider: str, secret_values: dict[str, str]) -> AddProviderResult:
        required, missing, present = collect_provider_secrets(
            provider, self._registry, self._vault)

        resolver = SecretResolver(self._registry, self._vault)
        stored = store_missing_secrets(missing, secret_values, resolver)

        secrets_dict = {key: self._vault.get(
            key) for key in self._vault.list()}
        config = self._config_loader.load()
        api_url = config.providers.get(
            provider, ProviderConfig()).api_url or ""
        status = self._checker.check(provider, secrets_dict, api_url)

        config.providers[provider] = config.providers.get(
            provider, ProviderConfig())
        self._config_loader.save(config)

        return AddProviderResult(
            stored_keys=stored,
            already_present=present,
            credential_status=status,
        )

    def check(self) -> CheckProvidersResult:
        config = self._config_loader.load()
        secrets_dict = {key: self._vault.get(
            key) for key in self._vault.list()}

        all_providers = collect_all_providers(self._registry)

        rows: list[ProviderCheckRow] = []
        for provider in sorted(all_providers):
            api_url = config.providers.get(
                provider, ProviderConfig()).api_url or ""
            status = self._checker.check(provider, secrets_dict, api_url)
            detail = status.identity if status.valid else status.error
            rows.append(ProviderCheckRow(provider=provider,
                        valid=status.valid, detail=detail))

        return CheckProvidersResult(rows=rows)

    def list(self) -> ListProvidersResult:
        all_providers = collect_all_providers(self._registry)

        providers: list[ProviderSecretsInfo] = []
        for provider, secret_keys in sorted(all_providers.items()):
            secrets = [(key, self._vault.has(key)) for key in secret_keys]
            providers.append(ProviderSecretsInfo(
                provider=provider, secrets=secrets))

        return ListProvidersResult(providers=providers)
