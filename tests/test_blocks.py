from freeloader.blocks.usecases import BlockUseCases


class TestBlocksList:
    def test_returns_all_blocks(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list()
        names = {b.name for b in result.blocks}
        assert "github_repo" in names
        assert "coolify_service" in names
        assert "coolify_project" in names
        assert "aws_ec2" in names

    def test_filters_by_layer(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list(layer="source")
        assert all(b.layer == "source" for b in result.blocks)
        assert any(b.name == "github_repo" for b in result.blocks)

    def test_filter_empty_layer(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list(layer="nonexistent")
        assert result.blocks == []

    def test_block_info_has_ports(self, block_usecases: BlockUseCases) -> None:
        result = block_usecases.list()
        github = next(b for b in result.blocks if b.name == "github_repo")
        assert "source.repo_name" in github.provides
        assert "source.clone_url" in github.provides
