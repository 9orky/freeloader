from .pipeline import RulePipeline
from .rules import (
    DeepRelativeImportRule,
    DomainBoundaryRule,
    FeatureIsolationRule,
    LayerOrderRule,
    LegacyLayerRule,
    PackageSurfaceRule,
    SharedIndependenceRule,
    UiImportSurfaceRule,
)
from .rules.base import ArchitectureRule


def default_rules() -> tuple[ArchitectureRule, ...]:
    return (
        FeatureIsolationRule(),
        SharedIndependenceRule(),
        LayerOrderRule(),
        DomainBoundaryRule(),
        UiImportSurfaceRule(),
        PackageSurfaceRule(),
        LegacyLayerRule(),
        DeepRelativeImportRule(),
    )


def build_default_pipeline() -> RulePipeline:
    return RulePipeline(default_rules())
