from freeloader.block.application import queries
from freeloader.block.domain import Layer
from freeloader.block.domain.entity import Block, BlockContract, BlockMeta, ConfigField
from freeloader.block.domain.value_object import BlockId


class FakeRepository:
    def __init__(self, blocks: dict[str, Block]) -> None:
        self.blocks = blocks

    blocks: dict[str, Block]

    def load_all(self) -> dict[str, Block]:
        return self.blocks


def test_manifest_candidates_expose_provider_requirements_and_default_config(monkeypatch) -> None:
    blocks = {
        "docker.dockerfile": _make_block(
            "docker.dockerfile",
            [
                ConfigField(name="language"),
                ConfigField(name="framework"),
                ConfigField(name="image_tag", default="latest", group="advanced"),
                ConfigField(name="docker_token", group="secrets"),
            ],
            required_tech_stack=True,
        )
    }
    monkeypatch.setattr(queries, "load_block_repository", lambda: FakeRepository(blocks))

    candidates = queries.get_manifest_candidates(
        tech_stack={"language": "python", "framework": "fastapi"},
        full_config=True,
        project_name="demo",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert str(candidate.id) == "docker.dockerfile"
    assert candidate.provider == "docker"
    assert candidate.config == {
        "language": "python",
        "framework": "fastapi",
        "image_tag": "latest",
    }
    assert candidate.required_secret_keys == ("docker_token",)
    assert candidate.required_tech_fields == ("language", "framework")
    assert candidate.required_tech_stack is True
    assert candidate.config_groups == ("basic", "advanced")


def test_manifest_candidates_do_not_filter_missing_requirements(monkeypatch) -> None:
    blocks = {
        "github.remote_repo": _make_block(
            "github.remote_repo",
            [ConfigField(name="github_token", group="secrets")],
        ),
        "docker.dockerfile": _make_block(
            "docker.dockerfile",
            [ConfigField(name="language"), ConfigField(name="framework")],
            required_tech_stack=True,
        ),
    }
    monkeypatch.setattr(queries, "load_block_repository", lambda: FakeRepository(blocks))

    candidates = queries.get_manifest_candidates(tech_stack={}, full_config=False)

    assert [str(candidate.id) for candidate in candidates] == [
        "github.remote_repo",
        "docker.dockerfile",
    ]
    assert candidates[0].required_secret_keys == ("github_token",)
    assert candidates[1].required_tech_fields == ("language", "framework")


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
