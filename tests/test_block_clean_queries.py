from dataclasses import dataclass

from freeloader.block.application import queries
from freeloader.block.domain import Layer
from freeloader.block.domain.entity import Block, BlockContract, BlockMeta, ConfigField
from freeloader.block.domain.value_object import BlockId


@dataclass(frozen=True)
class FakeRepository:
    blocks: dict[str, Block]

    def load_all(self) -> dict[str, Block]:
        return self.blocks


@dataclass(frozen=True)
class FakeSecretsReader:
    available: set[str]

    def has_secrets(self, secret_names: list[str]) -> bool:
        return all(secret_name in self.available for secret_name in secret_names)


def test_manifest_configs_excludes_blocks_missing_required_secrets(monkeypatch) -> None:
    blocks = {
        "github.remote_repo": _make_block(
            "github.remote_repo",
            [ConfigField(name="token", group="secrets")],
        ),
        "git.local_repo": _make_block("git.local_repo", [ConfigField(name="visibility")]),
    }
    monkeypatch.setattr(queries, "load_block_repository",
                        lambda: FakeRepository(blocks))
    monkeypatch.setattr(
        queries,
        "load_secrets_reader",
        lambda: FakeSecretsReader(available=set()),
    )

    configs = queries.get_manifest_configs(tech_stack={}, full_config=False)

    assert "github.remote_repo" not in configs
    assert "git.local_repo" in configs


def test_manifest_configs_excludes_blocks_missing_required_tech_stack(monkeypatch) -> None:
    blocks = {
        "docker.dockerfile": _make_block(
            "docker.dockerfile",
            [ConfigField(name="language"), ConfigField(name="framework")],
            required_tech_stack=True,
        ),
        "git.local_repo": _make_block("git.local_repo", [ConfigField(name="visibility")]),
    }
    monkeypatch.setattr(queries, "load_block_repository",
                        lambda: FakeRepository(blocks))
    monkeypatch.setattr(
        queries,
        "load_secrets_reader",
        lambda: FakeSecretsReader(available=set()),
    )

    configs = queries.get_manifest_configs(
        tech_stack={"language": "python"},
        full_config=False,
    )

    assert "docker.dockerfile" not in configs
    assert "git.local_repo" in configs


def test_manifest_configs_applies_required_tech_stack_when_available(monkeypatch) -> None:
    blocks = {
        "docker.dockerfile": _make_block(
            "docker.dockerfile",
            [ConfigField(name="language"), ConfigField(name="framework")],
            required_tech_stack=True,
        )
    }
    monkeypatch.setattr(queries, "load_block_repository",
                        lambda: FakeRepository(blocks))
    monkeypatch.setattr(
        queries,
        "load_secrets_reader",
        lambda: FakeSecretsReader(available=set()),
    )

    configs = queries.get_manifest_configs(
        tech_stack={"language": "python", "framework": "fastapi"},
        full_config=False,
    )

    assert configs["docker.dockerfile"]["language"] == "python"
    assert configs["docker.dockerfile"]["framework"] == "fastapi"


def _make_block(
    block_id: str,
    config_fields: list[ConfigField],
    *,
    required_tech_stack: bool = False,
) -> Block:
    return Block(
        id=BlockId(block_id),
        contract=BlockContract(
            block=BlockMeta(layer=Layer.build,
                            required_tech_stack=required_tech_stack),
            config=config_fields,
        ),
    )
