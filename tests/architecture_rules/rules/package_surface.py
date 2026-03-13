from __future__ import annotations

import ast

from ..context import ArchitectureContext
from .base import ArchitectureRule


ROOT_REEXPORT_MODULES = {
    "application",
    "application.interface",
    "ui",
    "ui.cli",
}


class PackageSurfaceRule(ArchitectureRule):
    rule_id = "package_surface"
    title = "Package Surface"
    description = "Feature package roots re-export only an app and/or a facade"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            init_file = feature_dir / "__init__.py"
            tree = context.parse_file(init_file)
            if tree is None:
                result.append(self.violation(
                    f"{feature_dir.name}.__init__ has syntax errors"))
                continue

            module = context.file_to_module(init_file)
            feature_pkg = f"{context.package_name}.{feature_dir.name}"

            for node in getattr(tree, "body", []):
                if isinstance(node, ast.Import):
                    result.append(self.violation(
                        f"{module} uses plain import statements"))
                    continue
                if not isinstance(node, ast.ImportFrom):
                    continue

                imported_module = (
                    node.module
                    if node.level == 0
                    else context.resolve_relative(init_file, module, node.level, node.module or "")
                )

                if imported_module is None:
                    result.append(self.violation(
                        f"{module} has an import without a module target"))
                    continue
                if not imported_module.startswith(feature_pkg):
                    result.append(
                        self.violation(
                            f"{module} re-exports external module {imported_module}")
                    )
                    continue

                suffix = imported_module.removeprefix(feature_pkg + ".")
                if suffix not in ROOT_REEXPORT_MODULES:
                    result.append(
                        self.violation(
                            f"{module} re-exports forbidden module {imported_module}")
                    )

            exports = context.string_list_assignment(init_file, "__all__")
            if exports is None:
                result.append(self.violation(
                    f"{module} must define an explicit __all__"))
                continue

            if len(exports) > 2:
                result.append(self.violation(
                    f"{module} exports more than two names: {exports}"))

            app_exports = [name for name in exports if name.endswith("_app")]
            facade_exports = [
                name for name in exports if not name.endswith("_app")]

            if len(app_exports) > 1:
                result.append(self.violation(
                    f"{module} exports multiple CLI apps: {app_exports}"))
            if len(facade_exports) > 1:
                result.append(
                    self.violation(
                        f"{module} exports multiple non-app names: {facade_exports}")
                )
        return result
