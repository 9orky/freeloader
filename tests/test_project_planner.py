from pathlib import Path

from freeloader.project.application.services import ProjectPlanner, SelectionContext
from freeloader.project.domain.entity import CandidateBlock, TechStack
from freeloader.service_providers.domain import BlockSupportReport, DriverSupportReport
from freeloader.secrets.domain.entity import SecretAvailabilityReport


class FakeSecrets:
    def __init__(self, available: set[str] | None = None) -> None:
        self._available = available or set()

    def check_availability(self, names: list[str]) -> SecretAvailabilityReport:
        required = tuple(names)
        present = tuple(name for name in required if name in self._available)
        missing = tuple(name for name in required if name not in self._available)
        return SecretAvailabilityReport(
            required_keys=required,
            present_keys=present,
            missing_keys=missing,
        )


def test_project_planner_preserves_selected_config_order_and_shape(tmp_path: Path) -> None:
    support_calls: list[list[str]] = []

    class FakeBlockGateway:
        def get_manifest_candidates(
            self,
            project_root: Path,
            tech_stack: TechStack,
            full_manifest: bool,
            project_name: str | None,
        ) -> tuple[CandidateBlock, ...]:
            assert project_root == tmp_path
            assert tech_stack.language == "python"
            assert full_manifest is True
            assert project_name == "demo"
            return (
                CandidateBlock("docker.dockerfile", "docker", {"language": "python"}),
                CandidateBlock("git.local_repo", "git", {"visibility": "private"}),
            )

    class FakeServiceProviders:
        def check_block_support(self, driver_names: list[str]) -> BlockSupportReport:
            support_calls.append(driver_names)
            return BlockSupportReport(
                driver_reports=tuple(DriverSupportReport(driver=name) for name in driver_names)
            )

    planner = ProjectPlanner(FakeBlockGateway(), FakeServiceProviders(), FakeSecrets())

    report = planner.plan(
        SelectionContext(
            name="demo",
            folder=tmp_path,
            tech_stack=TechStack(language="python"),
            full_manifest=True,
        )
    )

    assert report.selected_configs == {
        "docker.dockerfile": {"language": "python"},
        "git.local_repo": {"visibility": "private"},
    }
    assert [decision.block_id for decision in report.decisions] == [
        "docker.dockerfile",
        "git.local_repo",
    ]
    assert all(decision.selected for decision in report.decisions)
    assert support_calls == [["docker"], ["git"]]


def test_project_planner_records_unsupported_provider_exclusion(tmp_path: Path) -> None:
    class FakeBlockGateway:
        def get_manifest_candidates(
            self,
            project_root: Path,
            tech_stack: TechStack,
            full_manifest: bool,
            project_name: str | None,
        ) -> tuple[CandidateBlock, ...]:
            return (
                CandidateBlock("docker.dockerfile", "docker", {"language": "python"}),
                CandidateBlock("docker.dockerignore", "docker", {"include": ".env"}),
                CandidateBlock("git.local_repo", "git", {"visibility": "private"}),
            )

    class FakeServiceProviders:
        def check_block_support(self, driver_names: list[str]) -> BlockSupportReport:
            return BlockSupportReport(
                driver_reports=tuple(
                    DriverSupportReport(
                        driver=name,
                        reasons=("Docker CLI not found in PATH.",) if name == "docker" else (),
                        definitive=name != "docker",
                    )
                    for name in driver_names
                )
            )

    planner = ProjectPlanner(FakeBlockGateway(), FakeServiceProviders(), FakeSecrets())

    report = planner.plan(
        SelectionContext(
            name="demo",
            folder=tmp_path,
            tech_stack=TechStack(language="python"),
            full_manifest=False,
        )
    )

    assert report.selected_configs == {"git.local_repo": {"visibility": "private"}}
    assert [decision.selected for decision in report.decisions] == [False, False, True]
    assert report.decisions[0].reasons[0].code == "provider_unsupported"
    assert report.decisions[0].reasons[0].message == "Docker CLI not found in PATH."
    assert report.decisions[1].reasons[0].code == "provider_unsupported"
    assert report.decisions[2].reasons == ()


def test_project_planner_records_missing_secret_exclusion(tmp_path: Path) -> None:
    support_calls: list[list[str]] = []

    class FakeBlockGateway:
        def get_manifest_candidates(
            self,
            project_root: Path,
            tech_stack: TechStack,
            full_manifest: bool,
            project_name: str | None,
        ) -> tuple[CandidateBlock, ...]:
            return (
                CandidateBlock(
                    "github.remote_repo",
                    "github",
                    {"visibility": "private"},
                    required_secret_keys=("github_token",),
                ),
                CandidateBlock("git.local_repo", "git", {"visibility": "private"}),
            )

    class FakeServiceProviders:
        def check_block_support(self, driver_names: list[str]) -> BlockSupportReport:
            support_calls.append(driver_names)
            return BlockSupportReport(
                driver_reports=tuple(DriverSupportReport(driver=name) for name in driver_names)
            )

    planner = ProjectPlanner(FakeBlockGateway(), FakeServiceProviders(), FakeSecrets())

    report = planner.plan(
        SelectionContext(
            name="demo",
            folder=tmp_path,
            tech_stack=TechStack(language="python"),
            full_manifest=False,
        )
    )

    assert report.selected_configs == {"git.local_repo": {"visibility": "private"}}
    assert report.decisions[0].selected is False
    assert report.decisions[0].reasons[0].code == "missing_secrets"
    assert report.decisions[0].reasons[0].message == "Missing required secrets: github_token"
    assert support_calls == [["git"]]


def test_project_planner_records_missing_tech_exclusion(tmp_path: Path) -> None:
    support_calls: list[list[str]] = []

    class FakeBlockGateway:
        def get_manifest_candidates(
            self,
            project_root: Path,
            tech_stack: TechStack,
            full_manifest: bool,
            project_name: str | None,
        ) -> tuple[CandidateBlock, ...]:
            return (
                CandidateBlock(
                    "docker.dockerfile",
                    "docker",
                    {},
                    required_tech_fields=("language", "framework"),
                    required_tech_stack=True,
                ),
                CandidateBlock("git.local_repo", "git", {"visibility": "private"}),
            )

    class FakeServiceProviders:
        def check_block_support(self, driver_names: list[str]) -> BlockSupportReport:
            support_calls.append(driver_names)
            return BlockSupportReport(
                driver_reports=tuple(DriverSupportReport(driver=name) for name in driver_names)
            )

    planner = ProjectPlanner(FakeBlockGateway(), FakeServiceProviders(), FakeSecrets())

    report = planner.plan(
        SelectionContext(
            name="demo",
            folder=tmp_path,
            tech_stack=TechStack(language="python"),
            full_manifest=False,
        )
    )

    assert report.selected_configs == {"git.local_repo": {"visibility": "private"}}
    assert report.decisions[0].selected is False
    assert report.decisions[0].reasons[0].code == "missing_tech"
    assert report.decisions[0].reasons[0].message == "Missing required tech facts: framework"
    assert support_calls == [["git"]]
