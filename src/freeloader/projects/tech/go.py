from pathlib import Path

from freeloader.projects.tech import TechDetector, TechStack, tech_detector


@tech_detector
class GoDetector(TechDetector):
    @property
    def name(self) -> str:
        return "go"

    @property
    def patterns(self) -> list[str]:
        return ["go.mod"]

    def analyze(self, matched: dict[str, list[Path]]) -> TechStack | None:
        return TechStack(
            language="go",
            package_manager="go",
            framework="go",
            dockerfile_template="",
        )
