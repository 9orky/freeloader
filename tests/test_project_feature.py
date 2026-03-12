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
    from freeloader.block import BlockRef
    from freeloader.project.domain.entities import Manifest, TechStack

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


def test_provision_command_calls_application(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli

    called: list[Path] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(
        project_cli.application, "provision_project", lambda folder: called.append(
            folder)
    )

    result = CliRunner().invoke(app, ["project", "provision"])

    assert result.exit_code == 0
    assert called == [tmp_path]


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
    from freeloader.block import BlockRef
    from freeloader.project.domain.entities import Manifest, TechStack

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


def test_forget_command_calls_application(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.ui.cli as project_cli

    called: list[Path] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(
        project_cli.application, "forget_project", lambda folder: called.append(
            folder)
    )

    result = CliRunner().invoke(app, ["project", "forget"])

    assert result.exit_code == 0
    assert called == [tmp_path]
