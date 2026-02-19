from ..base import PackageManager, TechDetector
from ..registry import tech_detector


class Npm(PackageManager):
    name = "npm"
    patterns = ["package.json"]
    match_all = False


class Yarn(PackageManager):
    name = "yarn"
    patterns = ["package.json", "yarn.lock"]
    match_all = True


class Pnpm(PackageManager):
    name = "pnpm"
    patterns = ["package.json", "pnpm-lock.yaml"]
    match_all = True


@tech_detector(name="node")
class NodeNpm(TechDetector):
    language = "node"
    package_managers = [Yarn, Pnpm, Npm]