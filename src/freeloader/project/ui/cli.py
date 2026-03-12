import dataclasses

import typer

from freeloader import fl
from freeloader.shared import console

from .. import application
from .views import ManageProjectView, ProjectStatusView


project_app = typer.Typer(
    name="project",
    help="Manage project manifests and provisioning",
    no_args_is_help=True,
)

@project_app.command(help="Detect the technology stack for the current project")
@console.handle_errors
def detect() -> None:
    tech_stack = application.detect_stack(fl.cwd)
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
) -> None:
    manifest = application.manage_project(fl.cwd.name, fl.cwd, full_manifest)
    view = ManageProjectView(
        tech_stack=dataclasses.asdict(manifest.tech_stack),
        block_configs={ref.use: ref.config for ref in manifest.block_refs},
    )
    console.print_dict(view.model_dump(mode="python"))


@project_app.command(help="Show whether this directory is managed by freeloader")
@console.handle_errors
def status() -> None:
    manifest = application.get_status(fl.cwd)
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
    application.provision_project(fl.cwd)
    console.ok(f"Project '{fl.cwd.name}' provisioned successfully.")



@project_app.command(help="Destroy project resources and remove local state")
@console.handle_errors
def forget() -> None:
    application.forget_project(fl.cwd)
    console.ok(f"Project '{fl.cwd.name}' is not welcome anymore.")
