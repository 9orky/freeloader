from __future__ import annotations

from dataclasses import dataclass

from .auth import AuthSpec
from .billing import BillingSpec
from .errors import ProviderDefinitionError
from .support import LocalRequirement
from .value_object import ProviderName


@dataclass(frozen=True)
class ServiceProvider:
    name: ProviderName | str
    auth: AuthSpec | None = None
    support: tuple[LocalRequirement, ...] = ()
    billing: BillingSpec | None = None

    def __post_init__(self) -> None:
        name = ProviderName(str(self.name))
        support = tuple(self.support)
        support_identities = tuple(
            requirement.identity for requirement in support)
        if len(dict.fromkeys(support_identities)) != len(support_identities):
            raise ProviderDefinitionError(
                "Support requirements must be unique.", provider_name=str(name))
        if self.auth is not None and support:
            raise ProviderDefinitionError(
                "Authenticated providers cannot declare local support requirements.",
                provider_name=str(name),
            )
        if self.auth is None and not support:
            raise ProviderDefinitionError(
                "Local providers must declare at least one local support requirement.",
                provider_name=str(name),
            )

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "support", support)

    @property
    def requires_auth(self) -> bool:
        return self.auth is not None and self.auth.requires_auth

    @property
    def supports_billing(self) -> bool:
        return self.billing is not None

    @property
    def is_local(self) -> bool:
        return not self.requires_auth
