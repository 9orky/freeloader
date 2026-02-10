from pathlib import Path

from freeloader.projects.tech import TechDetector, TechStack, tech_detector

DOCKERFILE_TEMPLATES: dict[str, str] = {
    "python-uv": "python-uv",
    "python-poetry": "python-uv",
    "python-pip": "python-uv",
}


@tech_detector
class PythonDetector(TechDetector):
    @property
    def name(self) -> str:
        return "python"

    @property
    def patterns(self) -> list[str]:
        return ["pyproject.toml", "requirements*.txt", "setup.py", "Pipfile"]

    def analyze(self, matched: dict[str, list[Path]]) -> TechStack | None:
        pkg_mgr = "pip"
        framework = "python-pip"
        if "pyproject.toml" in matched:
            content = self.read_text(matched["pyproject.toml"][0])
            if "[tool.uv]" in content:
                pkg_mgr = "uv"
                framework = "python-uv"
            elif "[tool.poetry]" in content:
                pkg_mgr = "poetry"
                framework = "python-poetry"
        return TechStack(
            language="python",
            package_manager=pkg_mgr,
            framework=framework,
            dockerfile_template=DOCKERFILE_TEMPLATES.get(framework, ""),
        )
