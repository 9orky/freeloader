from pathlib import Path

from freeloader.projects.tech import TechDetector, TechStack, tech_detector


@tech_detector
class RustDetector(TechDetector):
    @property
    def name(self) -> str:
        return "rust"

    @property
    def patterns(self) -> list[str]:
        return ["Cargo.toml"]

    def analyze(self, matched: dict[str, list[Path]]) -> TechStack | None:
        return TechStack(
            language="rust",
            package_manager="cargo",
            framework="rust",
            dockerfile_template="",
        )
