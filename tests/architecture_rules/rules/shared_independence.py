from ..context import ArchitectureContext
from .base import ArchitectureRule


class SharedIndependenceRule(ArchitectureRule):
    rule_id = "shared_independence"
    title = "Shared Independence"
    description = "Shared subpackages do not import each other"

    def violations(self, context: ArchitectureContext):
        result = []
        subpackages = context.shared_subpackages()
        for pkg_dir in subpackages:
            for from_mod, imported in context.package_imports(pkg_dir):
                for other_dir in subpackages:
                    if other_dir == pkg_dir:
                        continue
                    other_name = f"{context.package_name}.shared.{other_dir.name}"
                    if imported == other_name or imported.startswith(other_name + "."):
                        result.append(self.violation(
                            f"{from_mod} -> {imported}"))
        return result
