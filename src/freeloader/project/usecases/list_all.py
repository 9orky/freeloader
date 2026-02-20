from pathlib import Path

from freeloader.shared.runtime import Freeloader

from ..application import ProjectApplication
from .system.managed_project import ManagedProject


def list_all_projects() -> list[dict]:
    app = ProjectApplication()
    freeloader = Freeloader()

    projects = []
    for mp in ManagedProject.iter_all(freeloader.projects_folder):
        project = app.get_project(mp.project_id)
        projects.append({
            "id": str(project.id),
            "name": project.name,
            "path": project.path,
            "tech_stack": project.tech_stack
        })

    return projects
