import click

from .. import usecases
from freeloader import runtime, console


@click.group(name="project")
def project_group():
    pass


@project_group.command()
@console.handle_cli_error
def ls():
    all_projects = usecases.list_all_projects()
    if len(all_projects) == 0:
        console.warn("No projects registered yet.")
        return 0

    console.print_table(
        "Registered Projects",
        ["Name", "Path"],
        [[project['name'], project['path']] for project in all_projects]
    )


@project_group.command()
@click.option("--full-manifest", is_flag=True, help="Include advanced configuration fields in the manifest")
@console.handle_cli_error
def manage(full_manifest: bool):
    usecases.initialize_project(
        runtime.cwd.name,
        runtime.cwd,
        full_manifest,
    )

    console.ok(f"Project is now managed by Freeloader.")


@project_group.command()
@console.handle_cli_error
def provision():
    usecases.provision(runtime.cwd)
    console.ok(f"Project '{runtime.cwd.name}' provisioned successfully.")


@project_group.command()
@console.handle_cli_error
def forget():
    usecases.forget_project(runtime.cwd)
    console.ok(f"Project '{runtime.cwd.name}' is not welcome anymore.")
