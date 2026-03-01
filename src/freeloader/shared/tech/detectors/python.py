from ..base import TechDetector
from ..language import FileBasedLanguageSource, LocalhostCommandLineSource
from ..package_manager import PackageManager
from ..framework import Framework
from ..registry import tech_detector


class PyProjectBased(PackageManager):
    package_pattern_template = r'^[ \t]*["\']?{package}(?![a-zA-Z0-9_-])["\']?(?:[ \t]*[>=<~!]|[ \t]*=|[ \t]*["\']|[ \t]*[,\]]|$)'
    language_version_pattern = r'(?:\bpython\b|requires-python)\s*=\s*["\'](?:[>=<^~!\s]*)([\d\.]+)'


class PipfileBased(PackageManager):
    package_pattern_template = r'^[ \t]*["\']?{package}(?![a-zA-Z0-9_-])["\']?[ \t]*='
    language_version_pattern = r'python(?:_version)?\s*=\s*["\'](?:[>=<^~!\s]*)([\d\.]+)'


class Pip(PipfileBased):
    name = "pip"
    patterns = ["requirements*.txt", "Pipfile"]
    language_version_pattern = r'(?<=")(python)(?=[>=<~!]|")'
    command_templates = {
        "init": "pip freeze > requirements.txt",
        "install": "pip install -r requirements.txt",
        "update": "pip install --upgrade -r requirements.txt",
        "add": "pip install {package} && pip freeze > requirements.txt",
        "remove": "pip uninstall {package} && pip freeze > requirements.txt",
    }


class Uv(PyProjectBased):
    name = "uv"
    patterns = ["pyproject.toml", "uv.lock"]
    command_templates = {
        "init": "uv init",
        "install": "uv install",
        "update": "uv update",
        "add": "uv add {package}",
        "remove": "uv remove {package}",
    }


class Poetry(PyProjectBased):
    name = "poetry"
    patterns = ["pyproject.toml", "poetry.lock"]
    command_templates = {
        "init": "poetry init -n",
        "install": "poetry install",
        "update": "poetry update",
        "add": "poetry add {package}",
        "remove": "poetry remove {package}",
    }


class Django(Framework):
    name = "django"


class Flask(Framework):
    name = "flask"


class FastAPI(Framework):
    name = "fastapi"


class PythonVersionFile(FileBasedLanguageSource):
    file_patterns = [".python-version"]


class UserConsolePythonVersion(LocalhostCommandLineSource):
    commands = ["python --version", "python3 --version"]
    version_pattern = r"Python\s+(\d+\.\d+\.\d+)"


@tech_detector(name="python")
class PythonDetector(TechDetector):
    language = "python"
    package_managers = [Pip, Uv, Poetry]
    language_sources = [PythonVersionFile, UserConsolePythonVersion]
    frameworks = [Django, Flask, FastAPI]
