from pathlib import Path

from freeloader import runtime, tech

from ..application import ProjectApplication
from .system import policy
from .system.managed_project import ManagedProject
from .user.project import UserProject
from .adapters import service_providers, blocks


def initialize_project(name: str, project_folder: Path, full_manifest: bool = False) -> None:
    policy.project_cannot_be_managed(name)
    user_project = _resolve_project(name, project_folder)

    _store_manifest(user_project, full_manifest)
    _register_project(user_project)

def _resolve_project(name: str, project_folder: Path) -> UserProject:
    user_project = UserProject(name, project_folder)
    assert user_project.no_manifest(), "Manifest already exists"
    return user_project


def _store_manifest(user_project: UserProject, full_manifest: bool) -> None:
    block_configs = blocks.get_manifest_configs(
        service_providers.load_available(),
        full_config=full_manifest,
    )

    user_project.save_manifest(block_configs)


def _register_project(user_project: UserProject) -> None:
    app = ProjectApplication()
    project_id = app.register(name=user_project.name, path=str(user_project.folder))
    ManagedProject.create(runtime.projects_folder, user_project.name, project_id)

    tech_stack = tech.detect(user_project.folder)
    if tech_stack is not None:
        app.detect_tech_stack(project_id, tech_stack)
