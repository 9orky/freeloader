from __future__ import annotations

import ast
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"
FREELOADER = SRC / "freeloader"
SHARED = FREELOADER / "shared"
PKG = "freeloader"

_LAYER_RANK: dict[str, int] = {
    "domain": 0,
    "infrastructure": 1,
    "application": 2,
    "ui": 3,
}
_LEGACY_LAYER_NAMES = {"adapters", "ports", "storage", "usecases"}
_ROOT_REEXPORT_MODULES = {
    "application",
    "application.interface",
    "ui",
    "ui.cli",
}


class ArchChecker(ABC):
    _next: ArchChecker | None = None

    @property
    @abstractmethod
    def title(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def violations(self) -> list[str]: ...

    def set_next(self, checker: ArchChecker) -> ArchChecker:
        self._next = checker
        return checker

    def run(self) -> bool:
        viols = self.violations()
        print(f"[{self.title}] {self.description}")
        if viols:
            for violation in viols:
                print(f"  \u2717 {violation}")
        else:
            print("  \u2713 ok")
        failed = bool(viols)
        if self._next:
            failed = self._next.run() or failed
        return failed

    def _is_package(self, path: Path) -> bool:
        return path.is_dir() and (path / "__init__.py").exists()

    _SUBSYSTEMS = {"shared", "block_old"}

    def _feature_packages(self) -> list[Path]:
        return sorted(
            directory
            for directory in FREELOADER.iterdir()
            if self._is_package(directory) and directory.name not in self._SUBSYSTEMS
        )

    def _shared_subpackages(self) -> list[Path]:
        return sorted(directory for directory in SHARED.iterdir() if self._is_package(directory))

    def _file_to_module(self, py_file: Path) -> str:
        parts = list(py_file.relative_to(SRC).parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        return ".".join(parts)

    def _pkg_parts(self, py_file: Path, module: str) -> list[str]:
        if py_file.name == "__init__.py":
            return module.split(".")
        return module.split(".")[:-1]

    def _resolve_relative(self, py_file: Path, base_module: str, level: int, name: str) -> str:
        pkg = self._pkg_parts(py_file, base_module)
        ancestor = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg
        return ".".join(ancestor + name.split(".")) if name else ".".join(ancestor)

    def _parse_file(self, py_file: Path) -> ast.AST | None:
        try:
            return ast.parse(py_file.read_text())
        except SyntaxError:
            return None

    def _imports_in_file(self, py_file: Path) -> list[str]:
        tree = self._parse_file(py_file)
        if tree is None:
            return []

        base_module = self._file_to_module(py_file)
        result: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    if node.module:
                        result.append(node.module)
                    continue

                base = self._resolve_relative(py_file, base_module, node.level, node.module or "")
                if node.module:
                    result.append(base)
                else:
                    for alias in node.names:
                        result.append(f"{base}.{alias.name}")
        return result

    def _package_imports(self, pkg_dir: Path) -> list[tuple[str, str]]:
        return [
            (from_mod, imported)
            for py_file in sorted(pkg_dir.rglob("*.py"))
            for from_mod in [self._file_to_module(py_file)]
            for imported in self._imports_in_file(py_file)
        ]

    def _layer_rank(self, module: str, feature_pkg: str) -> int | None:
        suffix = module.removeprefix(feature_pkg + ".")
        for layer, rank in _LAYER_RANK.items():
            if suffix == layer or suffix.startswith(layer + "."):
                return rank
        return None

    def _extract_string_list_assignment(self, tree: ast.AST, name: str) -> list[str] | None:
        for node in getattr(tree, "body", []):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue

            target = node.targets[0]
            if not isinstance(target, ast.Name) or target.id != name:
                continue
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                return None

            values: list[str] = []
            for element in node.value.elts:
                if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                    return None
                values.append(element.value)
            return values
        return None


class FeatureIsolationChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Feature Isolation"

    @property
    def description(self) -> str:
        return "Features may only import other features through package roots"

    def violations(self) -> list[str]:
        result: list[str] = []
        features = self._feature_packages()
        for feature_dir in features:
            for from_mod, imported in self._package_imports(feature_dir):
                for other_dir in features:
                    if other_dir == feature_dir:
                        continue
                    other_pkg = f"{PKG}.{other_dir.name}"
                    if imported.startswith(other_pkg + "."):
                        result.append(f"{from_mod} -> {imported}")
        return result


class SharedIndependenceChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Shared Independence"

    @property
    def description(self) -> str:
        return "Shared subpackages do not import each other"

    def violations(self) -> list[str]:
        result: list[str] = []
        subpackages = self._shared_subpackages()
        for pkg_dir in subpackages:
            for from_mod, imported in self._package_imports(pkg_dir):
                for other_dir in subpackages:
                    if other_dir == pkg_dir:
                        continue
                    other_name = f"{PKG}.shared.{other_dir.name}"
                    if imported == other_name or imported.startswith(other_name + "."):
                        result.append(f"{from_mod} -> {imported}")
        return result


class LayerOrderChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Layer Order"

    @property
    def description(self) -> str:
        return "domain < infrastructure < application < ui"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            feature_pkg = f"{PKG}.{feature_dir.name}"
            for from_mod, imported in self._package_imports(feature_dir):
                if not (imported == feature_pkg or imported.startswith(feature_pkg + ".")):
                    continue
                from_rank = self._layer_rank(from_mod, feature_pkg)
                imported_rank = self._layer_rank(imported, feature_pkg)
                if from_rank is not None and imported_rank is not None and imported_rank > from_rank:
                    result.append(
                        f"{from_mod} (rank {from_rank}) -> {imported} (rank {imported_rank})"
                    )
        return result


class DomainBoundaryChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Domain Boundary"

    @property
    def description(self) -> str:
        return "Domain imports stay within local domain modules or freeloader.shared"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            feature_pkg = f"{PKG}.{feature_dir.name}"
            domain_dir = feature_dir / "domain"
            if not domain_dir.exists():
                continue

            for from_mod, imported in self._package_imports(domain_dir):
                if not imported.startswith(f"{PKG}."):
                    continue
                if imported == f"{PKG}.shared" or imported.startswith(f"{PKG}.shared."):
                    continue
                if imported == f"{feature_pkg}.domain" or imported.startswith(f"{feature_pkg}.domain."):
                    continue
                result.append(f"{from_mod} -> {imported}")
        return result


class UiImportSurfaceChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "UI Import Surface"

    @property
    def description(self) -> str:
        return "UI imports the application package, not application submodules or lower layers"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            feature_pkg = f"{PKG}.{feature_dir.name}"
            ui_dir = feature_dir / "ui"
            if not ui_dir.exists():
                continue

            for from_mod, imported in self._package_imports(ui_dir):
                if imported.startswith(f"{feature_pkg}.application."):
                    result.append(f"{from_mod} -> {imported}")
                    continue
                if imported == f"{feature_pkg}.domain" or imported.startswith(f"{feature_pkg}.domain."):
                    result.append(f"{from_mod} -> {imported}")
                    continue
                if imported == f"{feature_pkg}.infrastructure" or imported.startswith(
                    f"{feature_pkg}.infrastructure."
                ):
                    result.append(f"{from_mod} -> {imported}")

            for py_file in sorted(ui_dir.rglob("*.py")):
                tree = self._parse_file(py_file)
                if tree is None:
                    continue

                module = self._file_to_module(py_file)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue

                    imported_module = (
                        node.module
                        if node.level == 0
                        else self._resolve_relative(py_file, module, node.level, node.module or "")
                    )
                    if imported_module != f"{feature_pkg}.application":
                        continue

                    result.append(
                        f"{module}:{node.lineno} imports names from {imported_module} instead of the module"
                    )
        return result


class PackageSurfaceChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Package Surface"

    @property
    def description(self) -> str:
        return "Feature package roots re-export only an app and/or a facade"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            init_file = feature_dir / "__init__.py"
            tree = self._parse_file(init_file)
            if tree is None:
                result.append(f"{feature_dir.name}.__init__ has syntax errors")
                continue

            module = self._file_to_module(init_file)
            feature_pkg = f"{PKG}.{feature_dir.name}"

            for node in getattr(tree, "body", []):
                if isinstance(node, ast.Import):
                    result.append(f"{module} uses plain import statements")
                    continue
                if not isinstance(node, ast.ImportFrom):
                    continue

                imported_module = (
                    node.module
                    if node.level == 0
                    else self._resolve_relative(init_file, module, node.level, node.module or "")
                )

                if imported_module is None:
                    result.append(f"{module} has an import without a module target")
                    continue

                if not imported_module.startswith(feature_pkg):
                    result.append(f"{module} re-exports external module {imported_module}")
                    continue

                suffix = imported_module.removeprefix(feature_pkg + ".")
                if suffix not in _ROOT_REEXPORT_MODULES:
                    result.append(f"{module} re-exports forbidden module {imported_module}")

            exports = self._extract_string_list_assignment(tree, "__all__")
            if exports is None:
                result.append(f"{module} must define an explicit __all__")
                continue

            if len(exports) > 2:
                result.append(f"{module} exports more than two names: {exports}")

            app_exports = [name for name in exports if name.endswith("_app")]
            facade_exports = [name for name in exports if not name.endswith("_app")]

            if len(app_exports) > 1:
                result.append(f"{module} exports multiple CLI apps: {app_exports}")
            if len(facade_exports) > 1:
                result.append(f"{module} exports multiple non-app names: {facade_exports}")

        return result


class LegacyLayerChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Legacy Layers"

    @property
    def description(self) -> str:
        return "Migrated features do not contain adapters/ports/storage/usecases"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            for layer_name in sorted(_LEGACY_LAYER_NAMES):
                if (feature_dir / layer_name).exists():
                    result.append(f"{feature_dir.name}/{layer_name}")
        return result


class DeepRelativeImportChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Deep Relative Imports"

    @property
    def description(self) -> str:
        return "Feature modules may not use relative imports above the parent folder"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            for py_file in sorted(feature_dir.rglob("*.py")):
                tree = self._parse_file(py_file)
                if tree is None:
                    continue

                module = self._file_to_module(py_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.level > 2:
                        result.append(
                            f"{module}:{node.lineno} uses {'.' * node.level}{node.module or ''}"
                        )
        return result


def build_pipeline() -> ArchChecker:
    head = FeatureIsolationChecker()
    head.set_next(SharedIndependenceChecker()).set_next(
        LayerOrderChecker()
    ).set_next(
        DomainBoundaryChecker()
    ).set_next(
        UiImportSurfaceChecker()
    ).set_next(
        PackageSurfaceChecker()
    ).set_next(
        LegacyLayerChecker()
    ).set_next(
        DeepRelativeImportChecker()
    )
    return head


def test_architecture() -> None:
    print()
    failed = build_pipeline().run()
    if failed:
        pytest.fail("Architecture violations detected (see above)", pytrace=False)


if __name__ == "__main__":
    failed = build_pipeline().run()
    print()
    sys.exit(1 if failed else 0)