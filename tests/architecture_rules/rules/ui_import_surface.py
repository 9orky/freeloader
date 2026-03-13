from __future__ import annotations

import ast

from ..context import ArchitectureContext
from .base import ArchitectureRule


class UiImportSurfaceRule(ArchitectureRule):
    rule_id = "ui_import_surface"
    title = "UI Import Surface"
    description = "UI imports the application package, not application submodules or lower layers"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            feature_pkg = f"{context.package_name}.{feature_dir.name}"
            ui_dir = feature_dir / "ui"
            if not ui_dir.exists():
                continue

            for from_mod, imported in context.package_imports(ui_dir):
                if imported.startswith(f"{feature_pkg}.application."):
                    result.append(self.violation(f"{from_mod} -> {imported}"))
                    continue
                if imported == f"{feature_pkg}.domain" or imported.startswith(f"{feature_pkg}.domain."):
                    result.append(self.violation(f"{from_mod} -> {imported}"))
                    continue
                if imported == f"{feature_pkg}.infrastructure" or imported.startswith(
                    f"{feature_pkg}.infrastructure."
                ):
                    result.append(self.violation(f"{from_mod} -> {imported}"))

            for py_file in sorted(ui_dir.rglob("*.py")):
                tree = context.parse_file(py_file)
                if tree is None:
                    continue

                module = context.file_to_module(py_file)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue

                    imported_module = (
                        node.module
                        if node.level == 0
                        else context.resolve_relative(py_file, module, node.level, node.module or "")
                    )
                    if imported_module != f"{feature_pkg}.application":
                        continue

                    result.append(
                        self.violation(
                            f"{module}:{node.lineno} imports names from {imported_module} instead of the module"
                        )
                    )
        return result
