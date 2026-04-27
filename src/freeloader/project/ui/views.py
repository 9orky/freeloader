from typing import Protocol

from pydantic import BaseModel, Field

from freeloader.shared.types import ConfigValue


class ProjectStatusView(BaseModel):
    is_managed: bool
    details: dict[str, str] = Field(default_factory=dict)


class ManageProjectView(BaseModel):
    tech_stack: dict | None = None
    block_configs: dict[str, dict[str, ConfigValue]] = Field(default_factory=dict)
    planning: "PlanningDiagnosticsView | None" = None


class ReasonLike(Protocol):
    code: str
    message: str


class DecisionLike(Protocol):
    block_id: str
    selected: bool
    reasons: tuple[ReasonLike, ...]


class SelectionReportLike(Protocol):
    decisions: tuple[DecisionLike, ...]


class PlanningDiagnosticsView(BaseModel):
    selected_blocks: list[str] = Field(default_factory=list)
    excluded_blocks: dict[str, list[str]] = Field(default_factory=dict)


def planning_diagnostics_view(report: SelectionReportLike) -> PlanningDiagnosticsView:
    return PlanningDiagnosticsView(
        selected_blocks=[
            decision.block_id
            for decision in report.decisions
            if decision.selected
        ],
        excluded_blocks={
            decision.block_id: [reason.message for reason in decision.reasons]
            for decision in report.decisions
            if not decision.selected
        },
    )
