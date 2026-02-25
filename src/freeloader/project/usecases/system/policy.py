from uuid import UUID

from freeloader import runtime

from .managed_project import ManagedProject


def project_cannot_be_managed(name: str) -> None:
    for mp in ManagedProject.iter_all(runtime.projects_folder):
        if mp.folder.name == name:
            raise ValueError(f"Project already registered with name '{name}'")


def manage_project(name: str, project_id: UUID) -> ManagedProject:
    project_cannot_be_managed(name)
    return ManagedProject.create(runtime.projects_folder, name, project_id)


def unmanage_project(name: str) -> None:
    for mp in ManagedProject.iter_all(runtime.projects_folder):
        if mp.folder.name == name:
            mp.destroy()
            return
    
    raise ValueError(f"Project with name '{name}' is not registered")