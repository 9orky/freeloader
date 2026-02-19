from pathlib import Path

from freeloader.shared.system import Freeloader
from freeloader.shared.tech import detect_stack

from ..application import ProjectApplication
from .system.managed_project import ManagedProject


def initialize_project(name: str, project_root: Path):
    freeloader = Freeloader()
    app = ProjectApplication()

    for mp in ManagedProject.iter_all(freeloader.projects_folder):
        if mp.folder.name == name:
            raise ValueError(f"Project already registered with name '{name}'")
        
        project = app.get_project(mp.project_id)
        if project.path == str(project_root):
            raise ValueError(f"Project '{project.name}' is registered")

    tech_stack = detect_stack(project_root)
    project_id = app.register(name=name, path=str(project_root))
    ManagedProject.create(freeloader.projects_folder, name, project_id)

    if tech_stack is not None:
        app.detect_tech_stack(project_id, tech_stack)
