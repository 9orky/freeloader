from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


PACKAGE_NAME = "freeloader"
IGNORED_FEATURE_PACKAGES = {"shared", "block_old"}


@dataclass
class ArchitectureContext:
    repo_root: Path
    src_root: Path
    freeloader_root: Path
    shared_root: Path
    package_name: str = PACKAGE_NAME
    _ast_cache: dict[Path, ast.AST | None] = field(
        default_factory=dict, init=False, repr=False)

    @classmethod
    def for_repo_root(cls, repo_root: Path) -> "ArchitectureContext":
        resolved_root = repo_root.resolve()
        src_root = resolved_root / "src"
        freeloader_root = src_root / PACKAGE_NAME
        return cls(
            repo_root=resolved_root,
            src_root=src_root,
            freeloader_root=freeloader_root,
            shared_root=freeloader_root / "shared",
        )

    def is_package(self, path: Path) -> bool:
        return path.is_dir() and (path / "__init__.py").exists()

    def feature_packages(self) -> list[Path]:
        return sorted(
            directory
            for directory in self.freeloader_root.iterdir()
            if self.is_package(directory) and directory.name not in IGNORED_FEATURE_PACKAGES
        )

    def shared_subpackages(self) -> list[Path]:
        return sorted(directory for directory in self.shared_root.iterdir() if self.is_package(directory))

    def file_to_module(self, py_file: Path) -> str:
        parts = list(py_file.relative_to(self.src_root).parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        return ".".join(parts)

    def pkg_parts(self, py_file: Path, module: str) -> list[str]:
        if py_file.name == "__init__.py":
            return module.split(".")
        return module.split(".")[:-1]

    def resolve_relative(self, py_file: Path, base_module: str, level: int, name: str) -> str:
        pkg = self.pkg_parts(py_file, base_module)
        ancestor = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg
        return ".".join(ancestor + name.split(".")) if name else ".".join(ancestor)

    def parse_file(self, py_file: Path) -> ast.AST | None:
        if py_file not in self._ast_cache:
            try:
                self._ast_cache[py_file] = ast.parse(py_file.read_text())
            except SyntaxError:
                self._ast_cache[py_file] = None
        return self._ast_cache[py_file]

    def imports_in_file(self, py_file: Path) -> list[str]:
        tree = self.parse_file(py_file)
        if tree is None:
            return []

        base_module = self.file_to_module(py_file)
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

                base = self.resolve_relative(
                    py_file, base_module, node.level, node.module or "")
                if node.module:
                    result.append(base)
                else:
                    for alias in node.names:
                        result.append(f"{base}.{alias.name}")
        return result

    def package_imports(self, pkg_dir: Path) -> list[tuple[str, str]]:
        return [
            (from_mod, imported)
            for py_file in sorted(pkg_dir.rglob("*.py"))
            for from_mod in [self.file_to_module(py_file)]
            for imported in self.imports_in_file(py_file)
        ]

    def string_list_assignment(self, py_file: Path, name: str) -> list[str] | None:
        tree = self.parse_file(py_file)
        if tree is None:
            return None

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
