from __future__ import annotations

import shutil

from freeloader.service_providers.domain import (
    BillingReport,
    Credentials,
    DriverSupportReport,
    LocalCommand,
    LocalRequirement,
    ProviderCapabilityError,
    ServiceProvider,
)
from freeloader.service_providers.domain.repository import ProviderDriver


class TerraformDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="terraform",
            support=(LocalRequirement("terraform"),),
        )

    def check_local_support(self) -> DriverSupportReport:
        if shutil.which("terraform"):
            return DriverSupportReport(driver=self.provider.name)
        return DriverSupportReport(
            driver=self.provider.name,
            missing_local_commands=(LocalCommand("terraform"),),
            reasons=("Terraform CLI not found in PATH.",),
        )

    def validate_credentials(self, credentials: Credentials) -> None:
        return None

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        raise ProviderCapabilityError(str(self.provider.name), "billing")
