import dataclasses

import typer

from freeloader import fl
from freeloader.shared import console

from .. import application
from .progress import render_project_forget_progress, render_project_provision_progress
from .views import ManageProjectView, ProjectStatusView, planning_diagnostics_view


project_app = typer.Typer(
    name="project",
    help="Manage project manifests and provisioning",
    no_args_is_help=True,
)


def _cwd():
    return fl.cwd


@project_app.command(help="Detect the technology stack for the current project")
@console.handle_errors
def detect() -> None:
    tech_stack = application.detect_stack(_cwd())
    if tech_stack and tech_stack.language:
        console.print_dict(dataclasses.asdict(tech_stack))
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
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Include block selection diagnostics",
    ),
) -> None:
    folder = _cwd()
    if explain:
        result = application.manage_project_with_report(folder.name, folder, full_manifest)
        manifest = result.manifest
        planning = planning_diagnostics_view(result.selection_report)
    else:
        manifest = application.manage_project(folder.name, folder, full_manifest)
        planning = None

    view = ManageProjectView(
        tech_stack=dataclasses.asdict(manifest.tech_stack),
        block_configs={ref.use: ref.config for ref in manifest.block_refs},
        planning=planning,
    )
    console.print_dict(view.model_dump(mode="python", exclude_none=True))


@project_app.command(help="Show whether this directory is managed by freeloader")
@console.handle_errors
def status() -> None:
    manifest = application.get_status(_cwd())
    if manifest is None:
        view = ProjectStatusView(is_managed=False)
    else:
        view = ProjectStatusView(
            is_managed=True,
            details={
                "name": manifest.name,
                "language": manifest.tech_stack.language or "",
                "blocks": str(len(manifest.block_refs)),
            },
        )
    console.print_dict(view.model_dump(mode="python"))


@project_app.command(help="Provision project resources from the current manifest")
@console.handle_errors
def provision() -> None:
    folder = _cwd()
    events = application.provision_project_events(folder)
    render_project_provision_progress(events)
    console.ok(f"Project '{folder.name}' provisioned successfully.")


@project_app.command(help="Destroy project resources and remove local state")
@console.handle_errors
def forget() -> None:
    folder = _cwd()
    events = application.forget_project_events(folder)
    render_project_forget_progress(events)
    console.ok(f"Project '{folder.name}' is not welcome anymore.")
