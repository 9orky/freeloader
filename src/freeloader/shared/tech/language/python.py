from ..base import PackageManager, TechDetector
from ..registry import tech_detector


class Pip(PackageManager):
    name = "pip"
    patterns = ["requirements*.txt", "Pipfile"]
    match_all = False


class Uv(PackageManager):
    name = "uv"
    patterns = ["pyproject.toml", "uv.lock"]
    match_all = True


class Poetry(PackageManager):
    name = "poetry"
    patterns = ["pyproject.toml", "poetry.lock"]
    match_all = True



@tech_detector(name="python")
class PythonDetector(TechDetector):
    language = "python"
    package_managers = [Pip, Uv, Poetry]
