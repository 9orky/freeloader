import click

from freeloader import runtime, console

from . import usecases


@click.group(name="project")
def project_group():
    pass


@project_group.command()
# @console.handle_cli_error
def detect():
    tech_stack = usecases.detect_stack(runtime.cwd)
    if tech_stack:
        return console.print_dict(tech_stack)
    console.warn("Could not detect technology stack for this project.")
    

@project_group.command()
@click.option("--full-manifest", is_flag=True, help="Include advanced configuration fields in the manifest")
# @console.handle_cli_error
def manage(full_manifest: bool):
    usecases.manage_project(
        runtime.cwd.name,
        runtime.cwd,
        full_manifest,
    )

    console.ok(f"Project is now managed by Freeloader.")


@project_group.command()
# @console.handle_cli_error
def provision():
    usecases.provision(runtime.cwd)
    console.ok(f"Project '{runtime.cwd.name}' provisioned successfully.")


@project_group.command()
# @console.handle_cli_error
def forget():
    usecases.forget_project(runtime.cwd)
    console.ok(f"Project '{runtime.cwd.name}' is not welcome anymore.")


@project_group.command()
# @console.handle_cli_error
def reset():
    usecases.forget_project(runtime.cwd)
    usecases.manage_project(runtime.cwd.name, runtime.cwd, full_manifest=False)
    usecases.provision(runtime.cwd)
    console.ok(f"Project '{runtime.cwd.name}' has been reset successfully.")


@project_group.command()
# @console.handle_cli_error
def test():
    graph = usecases.build_test_projects()
    console.print_dict(graph)