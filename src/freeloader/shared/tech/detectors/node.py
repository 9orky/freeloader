from ..base import TechDetector
from ..language import FileBasedLanguageSource, LocalhostCommandLineSource
from ..package_manager import PackageManager
from ..framework import Framework
from ..registry import tech_detector


class PackageJsonBased(PackageManager):
    package_pattern_template = r'^[ \t]*["\']?{package}(?![a-zA-Z0-9_-])["\']?[ \t]*:'
    language_version_pattern = r'"engines"\s*:\s*{[^}]*"node"\s*:\s*["\'](?:[>=<^~!\s]*)([\d\.]+)'


class Npm(PackageJsonBased):
    name = "npm"
    patterns = ["package.json"]


class Yarn(PackageJsonBased):
    name = "yarn"
    patterns = ["package.json", "yarn.lock"]


class Pnpm(PackageJsonBased):
    name = "pnpm"
    patterns = ["package.json", "pnpm-lock.yaml"]


class Astro(Framework):
    name = "astro"


class Express(Framework):
    name = "express"


class Angular(Framework):
    name = "angular"


class React(Framework):
    name = "react"


class NvmrcFile(FileBasedLanguageSource):
    file_patterns = [".nvmrc", ".node-version"]


class UserConsoleNodeVersion(LocalhostCommandLineSource):
    commands = ["node --version"]
    version_pattern = r"v?(\d+\.\d+\.\d+)"


@tech_detector(name="node")
class NodeNpm(TechDetector):
    language = "node"
    package_managers = [Yarn, Pnpm, Npm]
    language_sources = [NvmrcFile, UserConsoleNodeVersion]
    frameworks = [Astro, Express, Angular, React]
