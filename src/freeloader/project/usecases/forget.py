from pathlib import Path

from .user.project import UserProject


def forget_project(project_root: Path):
    user_project = UserProject.from_path(project_root)
    user_project.clean_up()
