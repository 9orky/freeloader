from pathlib import Path

from freeloader.projects.tech import TechDetector, TechStack, tech_detector

DOCKERFILE_TEMPLATE = "node-npm-nginx"


@tech_detector
class NodeNpm(TechDetector):
    @property
    def name(self) -> str:
        return "node.npm"

    @property
    def patterns(self) -> list[str]:
        return ["package.json", "package-lock.json"]

    def analyze(self, matched: dict[str, list[Path]]) -> TechStack | None:
        pkg_mgr = "npm"
        framework = "node-npm"
        if "pnpm-lock.yaml" in matched:
            pkg_mgr = "pnpm"
            framework = "node-pnpm"
        elif "yarn.lock" in matched:
            pkg_mgr = "yarn"
            framework = "node-yarn"
        if "package.json" in matched:
            content = self.read_text(matched["package.json"][0])
            if '"next"' in content:
                framework = "node-next"
        return TechStack(
            language="node",
            package_manager=pkg_mgr,
            framework=framework,
            dockerfile_template=DOCKERFILE_TEMPLATE,
        )
