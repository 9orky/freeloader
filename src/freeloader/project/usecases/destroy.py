from pathlib import Path
from freeloader.shared.runtime import Freeloader

from ..application import ProjectApplication
from .system.managed_project import ManagedProject


def destroy_project(project_root: Path):
    app = ProjectApplication()
    freeloader = Freeloader()

    for mp in ManagedProject.iter_all(freeloader.projects_folder):
        project = app.get_project(mp.project_id)
        if project.path == str(project_root):
            app.delete_project(project.id)
            mp.destroy()
            return

    raise ValueError(f"Project at '{project_root}' is not registered")
