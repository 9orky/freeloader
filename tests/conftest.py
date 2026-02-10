from pathlib import Path

import pytest

from freeloader.blocks.models import BlockContract
from freeloader.projects.models import BlockRef, ProjectInfo, ProjectManifest
from freeloader.blocks.registry import BlockRegistry
from freeloader.projects.config import ConfigLoader
from freeloader.credentials.checkers import CredentialStatus, CheckerRegistry
from freeloader.projects.state import StateManager
from freeloader.credentials.vault import SecretVault
from freeloader.blocks.usecases import BlockUseCases
from freeloader.credentials.usecases.providers import ProviderUseCases
from freeloader.credentials.usecases.secrets import SecretUseCases
from freeloader.projects.usecases.status import StatusUseCases
from freeloader.shared.paths import bundled_blocks_dir
from freeloader.shared.yaml_io import load_yaml_model


def _load_contracts() -> dict[str, BlockContract]:
    return {
        c.block.name: c
        for p in sorted(bundled_blocks_dir().glob("*/block.yaml"))
        for c in [load_yaml_model(p, BlockContract)]
    }


CONTRACTS = _load_contracts()


class InMemoryBlockRegistry(BlockRegistry):
    def __init__(self, contracts: dict[str, BlockContract], block_dir: Path) -> None:
        self._preloaded = contracts
        self._block_dir = block_dir
        self._cache: dict[str, tuple[BlockContract, Path]] = {}

    def _scan(self) -> None:
        self._cache = {
            name: (contract, self._block_dir / name)
            for name, contract in self._preloaded.items()
        }

    def _ensure_loaded(self) -> None:
        if not self._cache:
            self._scan()


class FakeProvider:
    def __init__(self, provider_name: str, token_key: str) -> None:
        self._name = provider_name
        self._token_key = token_key

    @property
    def name(self) -> str:
        return self._name

    def check_credentials(self, secrets: dict[str, str], api_url: str) -> CredentialStatus:
        if secrets.get(self._token_key):
            return CredentialStatus(valid=True, identity=f"{self._name}-user")
        return CredentialStatus(valid=False, error=f"Missing token for {self._name}")


def _build_fake_providers(contracts: dict[str, BlockContract]) -> list[FakeProvider]:
    seen: dict[str, str] = {}
    for contract in contracts.values():
        if contract.block.provider and contract.block.provider not in seen:
            seen[contract.block.provider] = contract.block.required_secrets[0]
    return [FakeProvider(name, key) for name, key in seen.items()]


FAKE_PROVIDERS = _build_fake_providers(CONTRACTS)


@pytest.fixture()
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / ".freeloader"
    home.mkdir()
    monkeypatch.setenv("FREELOADER_HOME", str(home))
    import freeloader.shared.paths as paths_mod
    monkeypatch.setattr(paths_mod, "FREELOADER_HOME", home)
    return home


@pytest.fixture()
def block_dir(tmp_path: Path) -> Path:
    d = tmp_path / "blocks"
    d.mkdir()
    for name in CONTRACTS:
        (d / name).mkdir()
    return d


@pytest.fixture()
def registry(block_dir: Path) -> InMemoryBlockRegistry:
    return InMemoryBlockRegistry(CONTRACTS, block_dir)


@pytest.fixture()
def vault(tmp_home: Path) -> SecretVault:
    return SecretVault(tmp_home / "secrets.enc", "test-passphrase")


@pytest.fixture()
def seeded_vault(vault: SecretVault) -> SecretVault:
    for contract in CONTRACTS.values():
        for key in contract.block.required_secrets:
            vault.set(key, f"test-{key.lower()}")
    return vault


@pytest.fixture()
def config_loader(tmp_home: Path) -> ConfigLoader:
    return ConfigLoader(tmp_home / "config.yaml")


@pytest.fixture()
def checker() -> CheckerRegistry:
    return CheckerRegistry(FAKE_PROVIDERS)


@pytest.fixture()
def secret_usecases(vault: SecretVault) -> SecretUseCases:
    return SecretUseCases(vault)


@pytest.fixture()
def block_usecases(registry: InMemoryBlockRegistry) -> BlockUseCases:
    return BlockUseCases(registry)


@pytest.fixture()
def provider_usecases(
    registry: InMemoryBlockRegistry,
    vault: SecretVault,
    config_loader: ConfigLoader,
    checker: CheckerRegistry,
) -> ProviderUseCases:
    return ProviderUseCases(registry, vault, config_loader, checker)


@pytest.fixture()
def seeded_provider_usecases(
    registry: InMemoryBlockRegistry,
    seeded_vault: SecretVault,
    config_loader: ConfigLoader,
    checker: CheckerRegistry,
) -> ProviderUseCases:
    return ProviderUseCases(registry, seeded_vault, config_loader, checker)


@pytest.fixture()
def status_usecases(tmp_home: Path) -> StatusUseCases:
    state_mgr = StateManager("test-project", tmp_home /
                             "projects" / "test-project")
    return StatusUseCases(state_mgr)


@pytest.fixture()
def sample_manifest() -> ProjectManifest:
    return ProjectManifest(
        project=ProjectInfo(name="my-app"),
        blocks=[
            BlockRef(use="github-repo", config={"name": "my-app"}),
            BlockRef(use="gitlab-registry", config={"name": "my-app"}),
        ],
    )
