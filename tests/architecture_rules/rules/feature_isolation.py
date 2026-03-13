from ..context import ArchitectureContext
from .base import ArchitectureRule


class FeatureIsolationRule(ArchitectureRule):
    rule_id = "feature_isolation"
    title = "Feature Isolation"
    description = "Features may only import other features through package roots"

    def violations(self, context: ArchitectureContext):
        result = []
        features = context.feature_packages()
        for feature_dir in features:
            for from_mod, imported in context.package_imports(feature_dir):
                for other_dir in features:
                    if other_dir == feature_dir:
                        continue
                    other_pkg = f"{context.package_name}.{other_dir.name}"
                    if imported.startswith(other_pkg + "."):
                        result.append(self.violation(
                            f"{from_mod} -> {imported}"))
        return result
