import click
from pathlib import Path

from freeloader.shared import console

from . import usecases


@click.group(name="project")
def project_group():
    pass


def _cwd() -> Path:
    return Path.cwd()


@project_group.command()
# @console.handle_cli_error
def detect():
    tech_stack = usecases.detect_stack(_cwd())
    if tech_stack:
        return console.print_dict(tech_stack)
    console.warn("Could not detect technology stack for this project.")


@project_group.command()
@click.option("--full-manifest", is_flag=True, help="Include advanced configuration fields in the manifest")
# @console.handle_cli_error
def manage(full_manifest: bool):
    cwd = _cwd()
    report = usecases.manage_project(
        cwd.name,
        cwd,
        full_manifest,
    )

    console.print_dict(report)


@project_group.command()
# @console.handle_cli_error
def provision():
    cwd = _cwd()
    usecases.provision(cwd)
    console.ok(f"Project '{cwd.name}' provisioned successfully.")


@project_group.command()
# @console.handle_cli_error
def forget():
    cwd = _cwd()
    usecases.forget_project(cwd)
    console.ok(f"Project '{cwd.name}' is not welcome anymore.")


@project_group.command()
# @console.handle_cli_error
def reset():
    cwd = _cwd()
    usecases.forget_project(cwd)
    usecases.manage_project(cwd.name, cwd, full_manifest=False)
    usecases.provision(cwd)
    console.ok(f"Project '{cwd.name}' has been reset successfully.")


@project_group.command()
# @console.handle_cli_error
def test():
    graph = usecases.build_test_projects(_cwd())
    console.print_dict(graph)
