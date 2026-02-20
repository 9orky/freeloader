from uuid import UUID

from freeloader.shared.runtime import FreeloaderApplication
from freeloader.shared.tech import TechStack

from .domain import Project


class ProjectApplication(FreeloaderApplication):
    def register(self, name: str, path: str) -> UUID:
        project = Project(name=name, path=path)
        self.save(project)
        return project.id

    def detect_tech_stack(self, project_id: UUID, tech_stack: TechStack) -> None:
        project: Project = self.repository.get(project_id)
        project.detect_tech_stack(**tech_stack.to_dict())
        self.save(project)

    def get_project(self, project_id: UUID) -> Project:
        return self.repository.get(project_id)

    def delete_project(self, project_id: UUID) -> None:
        project: Project = self.repository.get(project_id)
        project.discard()
        self.save(project)
