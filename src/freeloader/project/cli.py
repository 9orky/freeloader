from pathlib import Path

import typer

from freeloader.shared import console

from . import application


project_app = typer.Typer(
    name="project",
    help="Manage project manifests and provisioning",
    no_args_is_help=True,
)


def _cwd() -> Path:
    return Path.cwd()


@project_app.command(help="Detect the technology stack for the current project")
@console.handle_errors
def detect() -> None:
    tech_stack = application.detect_project(_cwd())
    if tech_stack and tech_stack.language:
        console.print_dict(tech_stack.model_dump(mode="python"))
        return
    console.warn("Could not detect technology stack for this project.")


@project_app.command(help="Generate a project manifest for the current directory")
@console.handle_errors
def manage(
    full_manifest: bool = typer.Option(
        False,
        "--full-manifest",
        help="Include advanced configuration fields in the manifest",
    ),
) -> None:
    cwd = _cwd()
    report = application.manage_project(
        cwd.name,
        cwd,
        full_manifest,
    )

    console.print_dict(report.model_dump(mode="python"))


@project_app.command(help="Provision project resources from the current manifest")
@console.handle_errors
def provision() -> None:
    cwd = _cwd()
    application.provision_project(cwd)
    console.ok(f"Project '{cwd.name}' provisioned successfully.")


@project_app.command(help="Destroy project resources and remove local state")
@console.handle_errors
def forget() -> None:
    cwd = _cwd()
    application.forget_project(cwd)
    console.ok(f"Project '{cwd.name}' is not welcome anymore.")
