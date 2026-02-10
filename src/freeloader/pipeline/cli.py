from pathlib import Path

import typer

from freeloader.projects.discovery import ProjectDiscovery
from freeloader.projects.models import ProjectManifest
from freeloader.projects.policies import validate_manifest_exists
from freeloader.factory import Factory
from freeloader.pipeline.usecases.generate import GenerateUseCases
from freeloader.shared.console import confirm, info, print_panel, print_table, spinner, success
from freeloader.shared.errors import handle_errors
from freeloader.shared.yaml_io import load_yaml_model


pipeline_app = typer.Typer(
    name="pipeline", help="Plan and execute the pipeline", no_args_is_help=True)
generate_app = typer.Typer(
    name="generate", help="Generate files from generator blocks")
pipeline_app.add_typer(generate_app)


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

        for ro in result.runner_outputs:
            print_panel(f"Plan: {ro.runner}", ro.output, style="yellow")
    else:
        with spinner("Resolving DAG..."):
            result = uc.plan(manifest)

        rows = [[b.block_id, b.layer, b.runner, ", ".join(
            b.depends_on) or "—"] for b in result.blocks]
        print_table(f"Execution Plan: {result.project_name}", [
                    "Block", "Layer", "Runner", "Depends On"], rows)


@pipeline_app.command(help="Provision all blocks")
@handle_errors
def up(yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")) -> None:
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

    for ro in plan_result.runner_outputs:
        print_panel(f"Plan: {ro.runner}", ro.output, style="yellow")

    if not yes and not confirm("Proceed with apply?"):
        raise typer.Abort()

    with spinner("Applying..."):
        result = uc.apply(manifest)

    for block_id, block_outputs in result.outputs.items():
        success(f"{block_id}: {len(block_outputs)} outputs")
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
    uc = GenerateUseCases(factory.blocks.registry, Path(output_dir))
    result = uc.generate(manifest)
    if not result.generated_block_ids:
        info("No generator blocks in this project")
        return
    for block_id in result.generated_block_ids:
        success(f"Generated files for {block_id}")
