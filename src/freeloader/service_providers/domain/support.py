from __future__ import annotations

from dataclasses import dataclass, field

from .errors import ProviderDefinitionError
from .value_object import LocalCommand, ProviderName


@dataclass(frozen=True)
class LocalRequirement:
    command: LocalCommand | str

    def __post_init__(self) -> None:
        command = LocalCommand(str(self.command))
        object.__setattr__(self, "command", command)

    @property
    def identity(self) -> str:
        return str(self.command)


@dataclass(frozen=True)
class DriverSupportReport:
    driver: ProviderName | str
    missing_local_commands: tuple[LocalCommand, ...] = ()
    reasons: tuple[str, ...] = ()
    definitive: bool = True
    supported: bool = field(init=False)

    def __post_init__(self) -> None:
        driver = ProviderName(str(self.driver))
        missing_local_commands = tuple(dict.fromkeys(LocalCommand(
            str(command)) for command in self.missing_local_commands))
        reasons = tuple(dict.fromkeys(reason.strip()
                        for reason in self.reasons if reason.strip()))

        object.__setattr__(self, "driver", driver)
        object.__setattr__(self, "missing_local_commands",
                           missing_local_commands)
        object.__setattr__(self, "reasons", reasons)
        object.__setattr__(
            self,
            "supported",
            self.definitive and not missing_local_commands,
        )

    @property
    def degraded(self) -> bool:
        return not self.definitive


@dataclass(frozen=True)
class BlockSupportReport:
    driver_reports: tuple[DriverSupportReport, ...]
    checked_provider_names: tuple[ProviderName, ...] = field(init=False)
    unsupported_provider_names: tuple[ProviderName, ...] = field(init=False)
    supported: bool = field(init=False)
    definitive: bool = field(init=False)
    degraded: bool = field(init=False)
    missing_local_commands: tuple[LocalCommand, ...] = field(init=False)
    reasons: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        driver_reports = tuple(self.driver_reports)
        driver_names = tuple(str(report.driver) for report in driver_reports)
        if len(dict.fromkeys(driver_names)) != len(driver_names):
            raise ProviderDefinitionError(
                "Block support report cannot contain duplicate drivers.")

        missing_local_commands = tuple(
            dict.fromkeys(
                command
                for report in driver_reports
                for command in report.missing_local_commands
            )
        )
        reasons = tuple(dict.fromkeys(
            reason for report in driver_reports for reason in report.reasons))
        checked_provider_names = tuple(report.driver for report in driver_reports)
        unsupported_provider_names = tuple(
            report.driver for report in driver_reports if not report.supported
        )

        object.__setattr__(self, "driver_reports", driver_reports)
        object.__setattr__(self, "checked_provider_names",
                           checked_provider_names)
        object.__setattr__(self, "unsupported_provider_names",
                           unsupported_provider_names)
        object.__setattr__(self, "missing_local_commands",
                           missing_local_commands)
        object.__setattr__(self, "reasons", reasons)
        object.__setattr__(
            self,
            "definitive",
            all(report.definitive for report in driver_reports),
        )
        object.__setattr__(self, "degraded", not self.definitive)
        object.__setattr__(self, "supported", all(
            report.supported for report in driver_reports))
