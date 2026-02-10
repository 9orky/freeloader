from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.checkers import CheckerRegistry
from freeloader.credentials.usecases.providers import ProviderUseCases
from freeloader.credentials.usecases.secrets import SecretUseCases
from freeloader.credentials.vault import SecretVault
from freeloader.projects.config import ConfigLoader
from freeloader.shared.paths import secrets_path


class CredentialsFactory:
    def __init__(
        self,
        passphrase: str | None,
        registry: BlockRegistry,
        config_loader: ConfigLoader,
    ) -> None:
        self._passphrase = passphrase
        self._registry = registry
        self._config_loader = config_loader
        self._checker_registry = CheckerRegistry.discover()

    def vault(self) -> SecretVault:
        return SecretVault(secrets_path(), self._passphrase)

    def secret_usecases(self) -> SecretUseCases:
        return SecretUseCases(self.vault())

    def provider_usecases(self) -> ProviderUseCases:
        return ProviderUseCases(
            self._registry,
            self.vault(),
            self._config_loader,
            self._checker_registry,
        )
