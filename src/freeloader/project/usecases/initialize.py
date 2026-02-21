from pathlib import Path

from freeloader import runtime, tech

from ..application import ProjectApplication
from .system import policy
from .user.project import UserProject
from .adapters import service_providers, blocks


def initialize_project(name: str, project_folder: Path):
    user_project = UserProject(name, project_folder)

    assert not user_project.is_initialized(), f"Project already initialized in {project_folder}"

    available_providers = service_providers.load_available()
    print(available_providers)

    block_configs = blocks.get_manifest_configs(available_providers)

    user_project.save_manifest(block_configs)

    # app = ProjectApplication()

    # for mp in ManagedProject.iter_all(runtime.projects_folder):
    #     if mp.folder.name == name:
    #         raise ValueError(f"Project already registered with name '{name}'")

    #     project = app.get_project(mp.project_id)
    #     if project.path == str(project_folder):
    #         raise ValueError(f"Project '{project.name}' is registered")

    # tech_stack = tech.detect(project_folder)
    # project_id = app.register(name=name, path=str(project_folder))
    # ManagedProject.create(runtime.projects_folder, name, project_id)

    # if tech_stack is not None:
    #     app.detect_tech_stack(project_id, tech_stack)
