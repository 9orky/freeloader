from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from freeloader.cli import app


def test_project_package_importable() -> None:
    importlib.import_module("freeloader.project")
    importlib.import_module("freeloader.project.application")


def test_project_help_lists_expected_commands() -> None:
    result = CliRunner().invoke(app, ["project", "--help"])

    assert result.exit_code == 0
    assert "detect" in result.output
    assert "manage" in result.output
    assert "provision" in result.output
    assert "forget" in result.output
    assert "status" in result.output


def test_detect_command_calls_application(monkeypatch) -> None:
    import freeloader.project.ui.cli as project_cli

    monkeypatch.setattr(project_cli, "_cwd", lambda: Path("/tmp"))
    monkeypatch.setattr(project_cli.application,
                        "detect_stack", lambda folder: None)

    result = CliRunner().invoke(app, ["project", "detect"])

    assert result.exit_code == 0


def test_manage_command_calls_application_and_renders_result(
    monkeypatch, tmp_path: Path
) -> None:
    import freeloader.project.ui.cli as project_cli
    from freeloader.project.domain.entity import Manifest, TechStack
    from freeloader.shared.block import BlockRef

    captured: list[dict] = []

    def fake_manage(name: str, folder: Path, full_manifest: bool) -> Manifest:
        return Manifest(
            name=name,
            tech_stack=TechStack(
                language="python",
                language_version="3.12",
                package_manager="uv",
            ),
            block_refs=(
                BlockRef.model_validate(
                    {"use": "github/actions_ci", "config": {"name": "demo"}}),
            ),
        )

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(project_cli.application, "manage_project", fake_manage)
    monkeypatch.setattr(
        project_cli.console, "print_dict", lambda data, **_: captured.append(
            data)
    )

    result = CliRunner().invoke(app, ["project", "manage", "--full-manifest"])

    assert result.exit_code == 0
    assert captured[0]["tech_stack"]["language"] == "python"
    assert captured[0]["block_configs"]["github/actions_ci"]["name"] == "demo"


def test_manage_project_filters_block_configs_via_service_providers(
    monkeypatch, tmp_path: Path
) -> None:
    import freeloader.project.application.commands as commands
    from freeloader.project.domain.entity import Manifest, TechStack
    from freeloader.shared.block import BlockRef

    saved_block_configs: dict[str, dict[str, str]] = {}
    support_calls: list[list[str]] = []

    class FakeManifestRepository:
        def manifest_exists(self, folder: Path) -> bool:
            assert folder == tmp_path
            return False

        def save(
            self,
            name: str,
            folder: Path,
            tech_stack: TechStack,
            block_configs: dict[str, dict[str, str]],
        ) -> None:
            assert name == tmp_path.name
            assert folder == tmp_path
            assert tech_stack.language == "python"
            saved_block_configs.update(block_configs)

        def load(self, folder: Path) -> Manifest:
            assert folder == tmp_path
            return Manifest(
                name=folder.name,
                tech_stack=TechStack(language="python"),
                block_refs=tuple(
                    BlockRef.model_validate(
                        {"use": ref_name, "config": config})
                    for ref_name, config in saved_block_configs.items()
                ),
            )

    class FakeTechStackDetector:
        def detect(self, folder: Path) -> TechStack:
            assert folder == tmp_path
            return TechStack(language="python")

    class FakeBlockGateway:
        def get_manifest_configs(
            self,
            project_root: Path,
            tech_stack: TechStack,
            full_manifest: bool,
            project_name: str | None,
        ) -> dict[str, dict[str, str]]:
            assert project_root == tmp_path
            assert tech_stack.language == "python"
            assert full_manifest is False
            assert project_name == tmp_path.name
            return {
                "docker.dockerfile": {"language": "python"},
                "docker.dockerignore": {"include": ".env"},
                "git.local_repo": {"visibility": "private"},
            }

    class FakeServiceProviders:
        def is_block_supported(self, driver_names: list[str]) -> bool:
            support_calls.append(driver_names)
            return driver_names != ["docker"]

    monkeypatch.setattr(commands, "load_manifest_repository",
                        lambda: FakeManifestRepository())
    monkeypatch.setattr(commands, "load_tech_stack_detector",
                        lambda: FakeTechStackDetector())
    monkeypatch.setattr(commands, "load_block_gateway",
                        lambda: FakeBlockGateway())
    monkeypatch.setattr(commands, "ServiceProviders",
                        lambda: FakeServiceProviders())

    manifest = commands.manage_project(tmp_path.name, tmp_path)

    assert saved_block_configs == {"git.local_repo": {"visibility": "private"}}
    assert [ref.use for ref in manifest.block_refs] == ["git.local_repo"]
    assert support_calls == [["docker"], ["git"]]


def test_provision_project_events_loads_manifest_and_forwards_iterator(
    monkeypatch, tmp_path: Path
) -> None:
    import freeloader.project.application.commands as commands
    from freeloader.block.domain.provisioning import ProvisioningPlan, ProvisioningReport
    from freeloader.project.domain.entity import Manifest, TechStack
    from freeloader.shared.block import BlockRef, ProvisioningFinished

    block_ref = BlockRef.model_validate(
        {"use": "github/actions_ci", "config": {"name": "demo"}}
    )
    manifest = Manifest(
        name="demo",
        tech_stack=TechStack(language="python"),
        block_refs=(block_ref,),
    )
    resources_root = tmp_path / ".freeloader"
    forwarded_events = iter(
        [
            ProvisioningFinished(
                report=ProvisioningReport(
                    plan=ProvisioningPlan(steps=[]),
                    applied_steps=[],
                )
            )
        ]
    )
    seen: list[tuple[Path, Path, list[BlockRef]]] = []

    class FakeManifestRepository:
        def load(self, folder: Path) -> Manifest:
            assert folder == tmp_path
            return manifest

        def resources_folder(self, folder: Path) -> Path:
            assert folder == tmp_path
            return resources_root

    class FakeBlockGateway:
        def provision_events(
            self,
            project_root: Path,
            manifest_resources_root: Path,
            block_refs: list[BlockRef],
        ):
            seen.append((project_root, manifest_resources_root, block_refs))
            return forwarded_events

    monkeypatch.setattr(commands, "load_manifest_repository",
                        lambda: FakeManifestRepository())
    monkeypatch.setattr(commands, "load_block_gateway",
                        lambda: FakeBlockGateway())

    actual = commands.provision_project_events(tmp_path)

    assert actual is forwarded_events
    assert seen == [(tmp_path, resources_root, [block_ref])]


def test_provision_command_uses_streaming_progress(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli
    from freeloader.shared.block import ProvisioningStarted

    received: list[list[object]] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(
        project_cli.application,
        "provision_project_events",
        lambda folder: iter([ProvisioningStarted(
            total_blocks=1, block_ids=[folder.name])]),
    )
    monkeypatch.setattr(
        project_cli,
        "render_project_provision_progress",
        lambda events: received.append(list(events)),
    )

    result = CliRunner().invoke(app, ["project", "provision"])

    assert result.exit_code == 0
    assert received == [[ProvisioningStarted(
        total_blocks=1, block_ids=[tmp_path.name])]]
    assert "provisioned successfully" in result.output


def test_status_command_renders_unmanaged(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli

    captured: list[dict] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(project_cli.application,
                        "get_status", lambda folder: None)
    monkeypatch.setattr(
        project_cli.console, "print_dict", lambda data, **_: captured.append(
            data)
    )

    result = CliRunner().invoke(app, ["project", "status"])

    assert result.exit_code == 0
    assert captured[0]["is_managed"] is False


def test_status_command_renders_managed(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli
    from freeloader.project.domain.entity import Manifest, TechStack
    from freeloader.shared.block import BlockRef

    captured: list[dict] = []
    fake_manifest = Manifest(
        name="my-project",
        tech_stack=TechStack(language="python"),
        block_refs=(BlockRef.model_validate(
            {"use": "github/actions_ci", "config": {}}),),
    )

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(project_cli.application,
                        "get_status", lambda folder: fake_manifest)
    monkeypatch.setattr(
        project_cli.console, "print_dict", lambda data, **_: captured.append(
            data)
    )

    result = CliRunner().invoke(app, ["project", "status"])

    assert result.exit_code == 0
    assert captured[0]["is_managed"] is True
    assert captured[0]["details"]["name"] == "my-project"
    assert captured[0]["details"]["blocks"] == "1"


def test_forget_command_uses_streaming_progress(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli
    from freeloader.shared.block import DestroyStarted

    received: list[list[object]] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(
        project_cli.application,
        "forget_project_events",
        lambda folder: iter(
            [DestroyStarted(total_blocks=1, block_ids=[folder.name])]),
    )
    monkeypatch.setattr(
        project_cli,
        "render_project_forget_progress",
        lambda events: received.append(list(events)),
    )

    result = CliRunner().invoke(app, ["project", "forget"])

    assert result.exit_code == 0
    assert received == [
        [DestroyStarted(total_blocks=1, block_ids=[tmp_path.name])]]
    assert "is not welcome anymore" in result.output
