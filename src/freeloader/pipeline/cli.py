from pathlib import Path

import typer

from freeloader.projects.discovery import ProjectDiscovery
from freeloader.projects.models import ProjectManifest
from freeloader.projects.policies import validate_manifest_exists
from freeloader.factory import Factory
from freeloader.shared.console import confirm, console, info, print_panel, print_table, spinner, success
from freeloader.shared.errors import handle_errors
from freeloader.shared.yaml_io import load_yaml_model


pipeline_app = typer.Typer(
    name="pipeline", help="Plan and execute the pipeline", no_args_is_help=True)
generate_app = typer.Typer(
    name="generate", help="Generate files from generator blocks")
pipeline_app.add_typer(generate_app)


@pipeline_app.command("blocks", help="List available blocks")
@handle_errors
def blocks_list(layer: str = typer.Option(None, help="Filter by layer")) -> None:
    result = Factory().pipeline.block_usecases().list(layer)
    if not result.blocks:
        info("No blocks found" + (f" for layer '{layer}'" if layer else ""))
        return
    rows = [
        [b.name, b.layer, b.runner, ", ".join(
            b.provides) or "—", ", ".join(b.requires) or "—"]
        for b in result.blocks
    ]
    print_table("Available Blocks", [
                "Name", "Layer", "Runner", "Provides", "Requires"], rows)


def _require_manifest() -> tuple[ProjectManifest, Path]:
    discovery = ProjectDiscovery()
    manifest_path = validate_manifest_exists(discovery.find_manifest())
    return load_yaml_model(manifest_path, ProjectManifest), manifest_path.parent


@pipeline_app.command(help="Show the execution plan")
@handle_errors
def plan(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Run real terraform plan"),
) -> None:
    manifest, _ = _require_manifest()
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    factory = Factory(passphrase)
    uc = factory.pipeline.apply_usecases(manifest.project.name)

    if detailed:
        with spinner("Running terraform plan..."):
            result = uc.detailed_plan(manifest)

        rows = [[b.block_id, b.layer, b.runner, ", ".join(
            b.depends_on) or "—"] for b in result.blocks]
        print_table(f"Execution Plan: {result.project_name}", [
                    "Block", "Layer", "Runner", "Depends On"], rows)

        for po in result.plan_outputs:
            print_panel(f"Plan: {po.block_id}", po.output, style="yellow")
    else:
        with spinner("Resolving DAG..."):
            result = uc.plan(manifest)

        rows = [[b.block_id, b.layer, b.runner, ", ".join(
            b.depends_on) or "—"] for b in result.blocks]
        print_table(f"Execution Plan: {result.project_name}", [
                    "Block", "Layer", "Runner", "Depends On"], rows)


@pipeline_app.command(help="Provision all blocks")
@handle_errors
def up(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Stream terraform output"),
) -> None:
    manifest, _ = _require_manifest()
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    factory = Factory(passphrase)
    uc = factory.pipeline.apply_usecases(manifest.project.name)

    with spinner("Running terraform plan..."):
        plan_result = uc.detailed_plan(manifest)

    rows = [[b.block_id, b.layer, b.runner, ", ".join(
        b.depends_on) or "—"] for b in plan_result.blocks]
    print_table(f"Execution Plan: {plan_result.project_name}", [
                "Block", "Layer", "Runner", "Depends On"], rows)

    for po in plan_result.plan_outputs:
        print_panel(f"Plan: {po.block_id}", po.output, style="yellow")

    if not yes and not confirm("Proceed with apply?"):
        raise typer.Abort()

    if verbose:
        from freeloader.shared import subprocess as sp
        sp.STREAM_OUTPUT = True

    def _on_plan(block_id: str, output: str) -> None:
        info(f"[plan] {block_id}")
        if verbose:
            console.print(output)

    def _on_apply(block_id: str, outputs: dict) -> None:
        success(f"{block_id}: {len(outputs)} outputs")

    def _on_skip(block_id: str) -> None:
        info(f"[skip] {block_id} (already applied)")

    result = uc.apply(
        manifest, on_plan=_on_plan, on_apply=_on_apply, on_skip=_on_skip)

    success(f"Project '{result.project_name}' is up")


@pipeline_app.command(help="Destroy all provisioned resources")
@handle_errors
def down(yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")) -> None:
    manifest, _ = _require_manifest()
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    uc = Factory(passphrase).pipeline.apply_usecases(manifest.project.name)

    block_names = [ref.resolved_id for ref in manifest.blocks]
    info(f"Will destroy {len(block_names)} blocks: {', '.join(block_names)}")

    if not yes and not confirm("Destroy all resources?"):
        raise typer.Abort()

    def _on_block(block_id: str) -> None:
        success(f"Destroyed {block_id}")

    result = uc.destroy(manifest, on_block=_on_block)

    success(f"Project '{result.project_name}' destroyed")


@generate_app.callback(invoke_without_command=True, help="Run generator blocks")
@handle_errors
def generate_run(
    output_dir: str = typer.Option(
        ".", help="Output directory for generated files"),
) -> None:
    manifest, _ = _require_manifest()
    factory = Factory()
    uc = factory.pipeline.generate_usecases(Path(output_dir))
    result = uc.generate(manifest)
    if not result.generated_block_ids:
        info("No generator blocks in this project")
        return
    for block_id in result.generated_block_ids:
        success(f"Generated files for {block_id}")
