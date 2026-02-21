from freeloader import runtime

from ..application import ProjectApplication
from .system.managed_project import ManagedProject


def list_all_projects() -> list[dict]:
    app = ProjectApplication()

    projects = []
    for mp in ManagedProject.iter_all(runtime.projects_folder):
        project = app.get_project(mp.project_id)
        projects.append({
            "id": str(project.id),
            "name": project.name,
            "path": project.path,
            "tech_stack": project.tech_stack
        })

    return projects
