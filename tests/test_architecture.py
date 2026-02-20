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
    "storage": 1,
    "application": 2,
    "usecases": 3,
    "ports.interface": 4,
    "ports.cli": 5,
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
            for v in viols:
                print(f"  \u2717 {v}")
        else:
            print("  \u2713 ok")
        failed = bool(viols)
        if self._next:
            failed = self._next.run() or failed
        return failed

    def _is_package(self, path: Path) -> bool:
        return path.is_dir() and (path / "__init__.py").exists()

    def _feature_packages(self) -> list[Path]:
        return sorted(d for d in FREELOADER.iterdir() if self._is_package(d) and d.name != "shared")

    def _shared_subpackages(self) -> list[Path]:
        return sorted(d for d in SHARED.iterdir() if self._is_package(d))

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

    def _imports_in_file(self, py_file: Path) -> list[str]:
        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
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
                else:
                    base = self._resolve_relative(
                        py_file, base_module, node.level, node.module or "")
                    if node.module:
                        result.append(base)
                    else:
                        for alias in node.names:
                            result.append(f"{base}.{alias.name}")
        return result

    def _package_imports(self, pkg_dir: Path) -> list[tuple[str, str]]:
        return [
            (from_mod, imp)
            for py_file in sorted(pkg_dir.rglob("*.py"))
            for from_mod in [self._file_to_module(py_file)]
            for imp in self._imports_in_file(py_file)
        ]

    def _layer_rank(self, module: str, feature_pkg: str) -> int | None:
        suffix = module.removeprefix(feature_pkg + ".")
        for layer, rank in _LAYER_RANK.items():
            if suffix == layer or suffix.startswith(layer + "."):
                return rank
        return None


class FeatureIsolationChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Feature Isolation"

    @property
    def description(self) -> str:
        return "Features may only communicate through ports.interface"

    def violations(self) -> list[str]:
        result: list[str] = []
        features = self._feature_packages()
        for feature_dir in features:
            feature_pkg = f"{PKG}.{feature_dir.name}"
            for from_mod, imp in self._package_imports(feature_dir):
                for other_dir in features:
                    if other_dir == feature_dir:
                        continue
                    other_pkg = f"{PKG}.{other_dir.name}"
                    if not (imp == other_pkg or imp.startswith(other_pkg + ".")):
                        continue
                    allowed = f"{other_pkg}.ports.interface"
                    if imp != allowed and not imp.startswith(allowed + "."):
                        result.append(f"{from_mod} -> {imp}")
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
        subpkgs = self._shared_subpackages()
        for pkg_dir in subpkgs:
            for from_mod, imp in self._package_imports(pkg_dir):
                for other_dir in subpkgs:
                    if other_dir == pkg_dir:
                        continue
                    other_name = f"{PKG}.shared.{other_dir.name}"
                    if imp == other_name or imp.startswith(other_name + "."):
                        result.append(f"{from_mod} -> {imp}")
        return result


class LayerOrderChecker(ArchChecker):
    @property
    def title(self) -> str:
        return "Layer Order"

    @property
    def description(self) -> str:
        return "domain < storage < application < usecases < ports.interface < ports.cli"

    def violations(self) -> list[str]:
        result: list[str] = []
        for feature_dir in self._feature_packages():
            feature_pkg = f"{PKG}.{feature_dir.name}"
            for from_mod, imp in self._package_imports(feature_dir):
                if not (imp == feature_pkg or imp.startswith(feature_pkg + ".")):
                    continue
                from_rank = self._layer_rank(from_mod, feature_pkg)
                imp_rank = self._layer_rank(imp, feature_pkg)
                if from_rank is not None and imp_rank is not None and imp_rank > from_rank:
                    result.append(
                        f"{from_mod} (rank {from_rank}) -> {imp} (rank {imp_rank})")
        return result


def build_pipeline() -> ArchChecker:
    head = FeatureIsolationChecker()
    head.set_next(SharedIndependenceChecker()).set_next(LayerOrderChecker())
    return head


def test_architecture() -> None:
    print()
    failed = build_pipeline().run()
    if failed:
        pytest.fail("Architecture violations detected (see above)",
                    pytrace=False)


if __name__ == "__main__":
    failed = build_pipeline().run()
    print()
    sys.exit(1 if failed else 0)
