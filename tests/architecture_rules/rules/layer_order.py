from ..context import ArchitectureContext
from .base import ArchitectureRule


LAYER_RANK: dict[str, int] = {
    "domain": 0,
    "infrastructure": 1,
    "application": 2,
    "ui": 3,
}


class LayerOrderRule(ArchitectureRule):
    rule_id = "layer_order"
    title = "Layer Order"
    description = "domain < infrastructure < application < ui"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            feature_pkg = f"{context.package_name}.{feature_dir.name}"
            for from_mod, imported in context.package_imports(feature_dir):
                if not (imported == feature_pkg or imported.startswith(feature_pkg + ".")):
                    continue
                from_rank = self._layer_rank(from_mod, feature_pkg)
                imported_rank = self._layer_rank(imported, feature_pkg)
                if from_rank is not None and imported_rank is not None and imported_rank > from_rank:
                    result.append(
                        self.violation(
                            f"{from_mod} (rank {from_rank}) -> {imported} (rank {imported_rank})"
                        )
                    )
        return result

    def _layer_rank(self, module: str, feature_pkg: str) -> int | None:
        suffix = module.removeprefix(feature_pkg + ".")
        for layer, rank in LAYER_RANK.items():
            if suffix == layer or suffix.startswith(layer + "."):
                return rank
        return None
