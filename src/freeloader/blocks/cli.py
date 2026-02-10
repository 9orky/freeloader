import typer

from freeloader.factory import Factory
from freeloader.shared.console import info, print_table
from freeloader.shared.errors import handle_errors


blocks_app = typer.Typer(
    name="blocks", help="Browse available blocks", no_args_is_help=True)


@blocks_app.command("list", help="List available blocks")
@handle_errors
def blocks_list(layer: str = typer.Option(None, help="Filter by layer")) -> None:
    result = Factory().blocks.usecases().list(layer)
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
