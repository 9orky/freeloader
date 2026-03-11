from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from freeloader.cli import app
from freeloader.project.models import ManageProjectResult, TechStack


def test_project_package_and_application_are_importable() -> None:
    importlib.import_module("freeloader.project")
    importlib.import_module("freeloader.project.application")


def test_project_help_lists_expected_commands() -> None:
    result = CliRunner().invoke(app, ["project", "--help"])

    assert result.exit_code == 0
    assert "detect" in result.output
    assert "manage" in result.output
    assert "provision" in result.output
    assert "forget" in result.output


def test_manage_command_calls_application_and_renders_result(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.cli as project_cli

    captured: list[dict] = []
    call_args: dict[str, object] = {}

    def fake_manage_project(name: str, project_folder: Path, full_manifest: bool) -> ManageProjectResult:
        call_args["name"] = name
        call_args["project_folder"] = project_folder
        call_args["full_manifest"] = full_manifest
        return ManageProjectResult(
            tech_stack=TechStack(
                language="python", package_manager="uv", language_version="3.12"),
            blocks_configs={"github/actions_ci": {"name": "demo"}},
        )

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(project_cli.application,
                        "manage_project", fake_manage_project)
    monkeypatch.setattr(project_cli.console, "print_dict",
                        lambda data, **_: captured.append(data))

    result = CliRunner().invoke(app, ["project", "manage", "--full-manifest"])

    assert result.exit_code == 0
    assert call_args == {
        "name": tmp_path.name,
        "project_folder": tmp_path,
        "full_manifest": True,
    }
    assert captured[0]["tech_stack"]["language"] == "python"
    assert captured[0]["blocks_configs"]["github/actions_ci"]["name"] == "demo"


def test_detect_command_warns_when_no_stack_is_detected(monkeypatch, tmp_path: Path) -> None:
    import freeloader.project.cli as project_cli

    warnings: list[str] = []

    monkeypatch.setattr(project_cli, "_cwd", lambda: tmp_path)
    monkeypatch.setattr(project_cli.application,
                        "detect_project", lambda project_folder: None)
    monkeypatch.setattr(project_cli.console, "warn",
                        lambda message: warnings.append(message))

    result = CliRunner().invoke(app, ["project", "detect"])

    assert result.exit_code == 0
    assert warnings == ["Could not detect technology stack for this project."]
