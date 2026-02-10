from freeloader.projects.models import BlockState, BlockStatus, ProjectState
from freeloader.projects.state import StateManager
from freeloader.projects.usecases.status import StatusUseCases

from datetime import datetime, timezone


class TestGetStatus:
    def test_empty_project(self, status_usecases: StatusUseCases) -> None:
        result = status_usecases.get()
        assert result.project_name == "test-project"
        assert result.blocks == []

    def test_with_blocks(self, tmp_home) -> None:
        state_dir = tmp_home / "projects" / "test-project"
        state_mgr = StateManager("test-project", state_dir)
        state = ProjectState(
            project_name="test-project",
            blocks=[
                BlockState(
                    block_name="github_repo",
                    block_use="github_repo",
                    status=BlockStatus.created,
                    outputs={"source.repo_name": "org/repo"},
                    last_applied=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
            ],
            last_up=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        state_mgr.save(state)

        uc = StatusUseCases(state_mgr)
        result = uc.get()

        assert len(result.blocks) == 1
        assert result.blocks[0].block_name == "github_repo"
        assert result.blocks[0].status == "created"
        assert result.blocks[0].output_count == 1
        assert result.last_up != ""
        assert result.last_down == ""
