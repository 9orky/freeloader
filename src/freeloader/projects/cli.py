from pathlib import Path

import typer

from freeloader.projects.discovery import ProjectDiscovery
from freeloader.projects.models import ProjectManifest
from freeloader.projects.policies import validate_manifest_exists, validate_no_existing_manifest
from freeloader.factory import Factory
from freeloader.shared.console import console, info, print_panel, print_table, success
from freeloader.shared.errors import handle_errors
from freeloader.shared.yaml_io import load_yaml_model


projects_app = typer.Typer(
    name="projects", help="Manage project lifecycle", no_args_is_help=True)


def _require_manifest() -> tuple[ProjectManifest, Path]:
    discovery = ProjectDiscovery()
    manifest_path = validate_manifest_exists(discovery.find_manifest())
    return load_yaml_model(manifest_path, ProjectManifest), manifest_path.parent


@projects_app.command(help="Initialize a new project")
@handle_errors
def init(
    name: str = typer.Option(None, help="Project name"),
    directory: str = typer.Option(".", help="Project directory"),
    full: bool = typer.Option(
        False, "--full", help="Include all config fields with defaults"),
) -> None:
    project_dir = Path(directory).resolve()
    validate_no_existing_manifest(project_dir)

    result = Factory().projects.init_usecases().init(project_dir, name, full)

    info(f"Initializing project '{result.project_name}'")
    if result.detected_stack:
        info(f"Detected: {result.detected_stack}")
    success(f"Created {result.manifest_path}")
    info(f"  {result.block_count} blocks configured")
    info("  Run 'fl pipeline up' to provision everything")


@projects_app.command(help="Show project status")
@handle_errors
def status(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed paths and settings"),
) -> None:
    manifest, _ = _require_manifest()
    result = Factory().projects.status_usecases(
        manifest.project.name).get(verbose=verbose)

    if verbose and result.paths:
        from rich.text import Text
        text = Text()
        labels = [
            ("Working directory", result.paths.cwd),
            ("FREELOADER_HOME", result.paths.freeloader_home),
            ("Config file", result.paths.config_path),
            ("Secrets vault", result.paths.secrets_path),
            ("Hosts inventory", result.paths.hosts_path),
            ("Project state", result.paths.project_state_dir),
            ("Resource dir", result.paths.project_resource_dir),
            ("User blocks", result.paths.user_blocks_dir),
            ("Bundled blocks", result.paths.bundled_blocks_dir),
        ]
        for label, value in labels:
            text.append(f"  {label:<20}", style="bold")
            path = Path(value)
            exists_mark = "✓" if path.exists() else "✗"
            style = "green" if path.exists() else "red"
            text.append(f" {exists_mark} ", style=style)
            text.append(f"{value}\n")

        console.print()
        print_panel(f"Paths — {result.project_name}", str(text))

    if not result.blocks:
        info(f"Project '{result.project_name}' has no provisioned blocks")
        return

    rows = [[b.block_name, b.status, str(
        b.output_count), b.last_applied, b.error or "—"] for b in result.blocks]
    print_table(
        f"Status: {result.project_name}",
        ["Block", "Status", "Outputs", "Last Applied", "Error"],
        rows,
    )

    if result.last_up:
        info(f"Last up: {result.last_up}")
    if result.last_down:
        info(f"Last down: {result.last_down}")
