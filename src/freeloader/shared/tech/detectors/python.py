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


class Uv(PyProjectBased):
    name = "uv"
    patterns = ["pyproject.toml", "uv.lock"]


class Poetry(PyProjectBased):
    name = "poetry"
    patterns = ["pyproject.toml", "poetry.lock"]


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
