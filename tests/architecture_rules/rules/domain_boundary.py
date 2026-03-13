from ..context import ArchitectureContext
from .base import ArchitectureRule


class DomainBoundaryRule(ArchitectureRule):
    rule_id = "domain_boundary"
    title = "Domain Boundary"
    description = "Domain imports stay within local domain modules or freeloader.shared"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            feature_pkg = f"{context.package_name}.{feature_dir.name}"
            domain_dir = feature_dir / "domain"
            if not domain_dir.exists():
                continue

            for from_mod, imported in context.package_imports(domain_dir):
                if not imported.startswith(f"{context.package_name}."):
                    continue
                if imported == f"{context.package_name}.shared" or imported.startswith(
                    f"{context.package_name}.shared."
                ):
                    continue
                if imported == f"{feature_pkg}.domain" or imported.startswith(f"{feature_pkg}.domain."):
                    continue
                result.append(self.violation(f"{from_mod} -> {imported}"))
        return result
