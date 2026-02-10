from freeloader.blocks.usecases import BlockUseCases


class TestBlocksList:
    def test_returns_all_blocks(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list()
        names = {b.name for b in result.blocks}
        assert "github-repo" in names
        assert "coolify-service" in names
        assert "coolify-project" in names
        assert "aws-ec2" in names

    def test_filters_by_layer(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list(layer="source")
        assert all(b.layer == "source" for b in result.blocks)
        assert any(b.name == "github-repo" for b in result.blocks)

    def test_filter_empty_layer(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list(layer="nonexistent")
        assert result.blocks == []

    def test_block_info_has_ports(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list()
        github = next(b for b in result.blocks if b.name == "github-repo")
        assert "source.repo_name" in github.provides
        assert "source.clone_url" in github.provides
