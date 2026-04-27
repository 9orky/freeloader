from dataclasses import dataclass
import dataclasses
from pathlib import Path
from typing import Protocol

from freeloader.project.domain.entity import CandidateBlock, TechStack
from freeloader.project.domain.repository import BlockGateway
from freeloader.secrets import Secrets
from freeloader.service_providers import ServiceProviders
from freeloader.shared.types import ConfigValue


@dataclass(frozen=True)
class SelectionContext:
    name: str
    folder: Path
    tech_stack: TechStack
    full_manifest: bool


@dataclass(frozen=True)
class PlanningReason:
    code: str
    message: str


@dataclass(frozen=True)
class SelectionDecision:
    block_id: str
    config: dict[str, ConfigValue]
    selected: bool
    reasons: tuple[PlanningReason, ...] = ()


@dataclass(frozen=True)
class SelectionReport:
    decisions: tuple[SelectionDecision, ...]

    @property
    def selected_configs(self) -> dict[str, dict[str, ConfigValue]]:
        return {
            decision.block_id: decision.config
            for decision in self.decisions
            if decision.selected
        }


class ProviderSupportReport(Protocol):
    supported: bool
    degraded: bool
    reasons: tuple[str, ...]


class SecretAvailability(Protocol):
    missing_keys: tuple[str, ...]
    available: bool


class ProjectPlanner:
    def __init__(
        self,
        block_gateway: BlockGateway,
        service_providers: ServiceProviders,
        secrets: Secrets,
    ) -> None:
        self._block_gateway = block_gateway
        self._service_providers = service_providers
        self._secrets = secrets

    def plan(self, context: SelectionContext) -> SelectionReport:
        candidates = self._block_gateway.get_manifest_candidates(
            context.folder,
            context.tech_stack,
            context.full_manifest,
            context.name,
        )
        return self._select_supported_blocks(candidates, context.tech_stack)

    def _select_supported_blocks(
        self,
        candidates: tuple[CandidateBlock, ...],
        tech_stack: TechStack,
    ) -> SelectionReport:
        support_cache: dict[str, ProviderSupportReport] = {}
        decisions: list[SelectionDecision] = []

        for candidate in candidates:
            missing_tech_fields = _missing_tech_fields(candidate, tech_stack)
            if missing_tech_fields:
                decisions.append(
                    SelectionDecision(
                        block_id=candidate.block_id,
                        config=candidate.config,
                        selected=False,
                        reasons=(_missing_tech_reason(missing_tech_fields),),
                    )
                )
                continue

            secret_availability = self._secret_availability(candidate)
            if not secret_availability.available:
                decisions.append(
                    SelectionDecision(
                        block_id=candidate.block_id,
                        config=candidate.config,
                        selected=False,
                        reasons=(_missing_secrets_reason(secret_availability),),
                    )
                )
                continue

            provider_name = candidate.provider
            if provider_name not in support_cache:
                support_cache[provider_name] = self._service_providers.check_block_support([provider_name])

            support_report = support_cache[provider_name]
            decisions.append(
                SelectionDecision(
                    block_id=candidate.block_id,
                    config=candidate.config,
                    selected=support_report.supported,
                    reasons=()
                    if support_report.supported
                    else (_unsupported_provider_reason(provider_name, support_report),),
                )
            )

        return SelectionReport(decisions=tuple(decisions))

    def _secret_availability(self, candidate: CandidateBlock) -> SecretAvailability:
        return self._secrets.check_availability(list(candidate.required_secret_keys))


def _missing_tech_fields(
    candidate: CandidateBlock,
    tech_stack: TechStack,
) -> tuple[str, ...]:
    if not candidate.required_tech_stack:
        return ()
    stack_values = dataclasses.asdict(tech_stack)
    return tuple(
        field_name
        for field_name in candidate.required_tech_fields
        if stack_values.get(field_name) is None
    )

def _unsupported_provider_reason(
    provider_name: str,
    support_report: ProviderSupportReport,
) -> PlanningReason:
    if support_report.reasons:
        message = "; ".join(support_report.reasons)
    elif support_report.degraded:
        message = f"Provider '{provider_name}' support could not be checked definitively"
    else:
        message = f"Provider '{provider_name}' is not supported in this environment"
    return PlanningReason(
        code="provider_unsupported",
        message=message,
    )


def _missing_secrets_reason(secret_availability: SecretAvailability) -> PlanningReason:
    missing = ", ".join(secret_availability.missing_keys)
    return PlanningReason(
        code="missing_secrets",
        message=f"Missing required secrets: {missing}",
    )


def _missing_tech_reason(missing_fields: tuple[str, ...]) -> PlanningReason:
    missing = ", ".join(missing_fields)
    return PlanningReason(
        code="missing_tech",
        message=f"Missing required tech facts: {missing}",
    )
