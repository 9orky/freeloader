from pathlib import Path
from freeloader import runtime

from ..application import ProjectApplication
from .system.managed_project import ManagedProject


def destroy_project(project_root: Path):
    app = ProjectApplication()

    for mp in ManagedProject.iter_all(runtime.projects_folder):
        project = app.get_project(mp.project_id)
        if project.path == str(project_root):
            app.delete_project(project.id)
            mp.destroy()
            return

    raise ValueError(f"Project at '{project_root}' is not registered")
