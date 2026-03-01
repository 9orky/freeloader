from os import getenv
from pathlib import Path
import subprocess

from freeloader import runtime
from freeloader.shared.tech import TechFacade


def detect_stack(project_folder: Path) -> dict:
    return TechFacade().detect_stack(project_folder)


def build_test_projects() -> dict:
    if runtime.cwd != Path().cwd():
        raise RuntimeError("It works only in dev mode and in dev project.")
    
    test_projects_dir = Path(getenv("FREELOADER_TEST_PROJECTS", ""))

    if not test_projects_dir.exists():
        raise RuntimeError(f"Test projects dir does not exist.")
    
    graph = TechFacade().build_graph(test_projects_dir)
    folders_to_commands = {}
    project_paths: list[Path] = []

    for lang, pms in graph.items():
        for pm, fms in pms.items():
            for fm, commands in fms.items():
                single_folder = test_projects_dir / lang / pm / fm
                folders_to_commands[str(single_folder)] = commands

    for folder, commands in folders_to_commands.items():
        folder_path = Path(folder + "_project")
        folder_path.mkdir(parents=True, exist_ok=True)

        for command_name, command_str in commands.items():
            if command_name in ["init", "add"]:
                try:
                    subprocess.run(command_str, cwd=folder_path, shell=True, check=True)
                    project_paths.append(folder_path)
                except subprocess.CalledProcessError as e:
                    print(f"Command '{command_str}' failed in folder '{folder_path}': {e}")
    
    folders_to_stack = {}
    for project_folder in project_paths:
        tech_stack = detect_stack(project_folder)
        stack_line = ", ".join(f"{k}: {v}" for k, v in tech_stack.items())
        folders_to_stack[str(project_folder)] = stack_line or "No tech stack detected"

    return folders_to_stack