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
            not missing_local_commands,
        )


@dataclass(frozen=True)
class BlockSupportReport:
    driver_reports: tuple[DriverSupportReport, ...]
    supported: bool = field(init=False)
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

        object.__setattr__(self, "driver_reports", driver_reports)
        object.__setattr__(self, "missing_local_commands",
                           missing_local_commands)
        object.__setattr__(self, "reasons", reasons)
        object.__setattr__(self, "supported", all(
            report.supported for report in driver_reports))
