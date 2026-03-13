from ..context import ArchitectureContext
from .base import ArchitectureRule


LEGACY_LAYER_NAMES = {"adapters", "ports", "storage", "usecases"}


class LegacyLayerRule(ArchitectureRule):
    rule_id = "legacy_layers"
    title = "Legacy Layers"
    description = "Migrated features do not contain adapters/ports/storage/usecases"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            for layer_name in sorted(LEGACY_LAYER_NAMES):
                if (feature_dir / layer_name).exists():
                    result.append(self.violation(
                        f"{feature_dir.name}/{layer_name}"))
        return result
