from pathlib import Path

from .models import ManageProjectResult, TechStack
from . import usecases


def detect_project(project_folder: Path) -> TechStack | None:
    return usecases.detect_project_stack(project_folder)


def manage_project(name: str, project_folder: Path, full_manifest: bool = False) -> ManageProjectResult:
    return usecases.manage_project(name, project_folder, full_manifest)


def provision_project(project_folder: Path) -> None:
    usecases.provision_project(project_folder)


def forget_project(project_folder: Path) -> None:
    usecases.forget_project(project_folder)
