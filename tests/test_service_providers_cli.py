from typer.testing import CliRunner

from freeloader.cli import app
from freeloader.service_providers.domain import (
    AuthSpec,
    AuthorizationResult,
    BillingCheckCost,
    BillingLineItem,
    BillingReport,
    BillingSpec,
    CredentialKey,
    FreeTierUsage,
    LocalRequirement,
    ObtainCredentialAction,
    ObtainCredentialStep,
    ServiceProvider,
)


def test_list_command_renders_clean_domain_columns(monkeypatch) -> None:
    import freeloader.service_providers.ui.cli as service_providers_cli

    monkeypatch.setattr(
        service_providers_cli.application,
        "list_provider_items",
        lambda: [
            service_providers_cli.application.ProviderListItem(
                provider=ServiceProvider(
                    name="docker",
                    support=(LocalRequirement("docker"),),
                ),
                authorized=None,
            ),
            service_providers_cli.application.ProviderListItem(
                provider=ServiceProvider(
                    name="github",
                    auth=AuthSpec((CredentialKey("GITHUB_TOKEN"),)),
                    billing=BillingSpec(BillingCheckCost.free),
                ),
                authorized=True,
            ),
        ],
    )

    result = CliRunner().invoke(app, ["service-providers", "ls"])

    assert result.exit_code == 0
    assert "Authorized" in result.output
    assert "docker" in result.output
    assert "github" in result.output
    assert "remote" in result.output
    assert "free" in result.output
    assert "yes" in result.output


def test_list_command_marks_missing_credentials_as_not_authorized(monkeypatch) -> None:
    import freeloader.service_providers.ui.cli as service_providers_cli

    monkeypatch.setattr(
        service_providers_cli.application,
        "list_provider_items",
        lambda: [
            service_providers_cli.application.ProviderListItem(
                provider=ServiceProvider(
                    name="github",
                    auth=AuthSpec((CredentialKey("GITHUB_TOKEN"),)),
                ),
                authorized=False,
            ),
        ],
    )

    result = CliRunner().invoke(app, ["service-providers", "ls"])

    assert result.exit_code == 0
    assert "no" in result.output


def test_auth_command_collects_obtain_steps_and_prompts_remaining_keys(monkeypatch) -> None:
    import freeloader.service_providers.ui.cli as service_providers_cli

    provider = ServiceProvider(
        name="coolify",
        auth=AuthSpec(
            credential_keys=(
                CredentialKey("COOLIFY_TOKEN"),
                CredentialKey("COOLIFY_ENDPOINT"),
            ),
            obtain_steps=(
                ObtainCredentialStep(
                    action=ObtainCredentialAction.input,
                    value="COOLIFY_ENDPOINT",
                ),
            ),
        ),
    )
    captured: dict[str, str] = {}

    monkeypatch.setattr(service_providers_cli.application,
                        "get_provider", lambda _: provider)

    def fake_authorize_provider(name: str, credentials: dict[str, str]) -> AuthorizationResult:
        captured.update(credentials)
        return AuthorizationResult(
            provider=name,
            stored_credentials=(
                CredentialKey("COOLIFY_ENDPOINT"),
                CredentialKey("COOLIFY_TOKEN"),
            ),
        )

    monkeypatch.setattr(
        service_providers_cli.application,
        "authorize_provider",
        fake_authorize_provider,
    )

    result = CliRunner().invoke(
        app,
        ["service-providers", "auth", "coolify"],
        input="https://coolify.example\nsecret-token\n",
    )

    assert result.exit_code == 0
    assert captured == {
        "COOLIFY_ENDPOINT": "https://coolify.example",
        "COOLIFY_TOKEN": "secret-token",
    }
    assert "Stored credentials for coolify" in result.output


def test_billing_command_renders_summary_tables(monkeypatch) -> None:
    import freeloader.service_providers.ui.cli as service_providers_cli

    provider = ServiceProvider(
        name="github",
        auth=AuthSpec((CredentialKey("GITHUB_TOKEN"),)),
        billing=BillingSpec(BillingCheckCost.free),
    )
    report = BillingReport(
        provider="github",
        total_usd=1.25,
        period="2026-03",
        items=(BillingLineItem(service="Actions", amount_usd=1.25),),
        free_tier_usage=(
            FreeTierUsage(
                service="Storage",
                metric="storage",
                used=1.0,
                limit=5.0,
                unit="GB",
            ),
        ),
    )

    monkeypatch.setattr(service_providers_cli.application,
                        "get_provider", lambda _: provider)
    monkeypatch.setattr(service_providers_cli.application,
                        "check_billing", lambda _: report)

    result = CliRunner().invoke(
        app, ["service-providers", "billing", "github"])

    assert result.exit_code == 0
    assert "Billing Summary" in result.output
    assert "Billed Services" in result.output
    assert "Free Tier Usage" in result.output
    assert "Actions" in result.output
    assert "Storage" in result.output


def test_billing_command_reports_unsupported_provider(monkeypatch) -> None:
    import freeloader.service_providers.ui.cli as service_providers_cli

    provider = ServiceProvider(
        name="docker",
        support=(LocalRequirement("docker"),),
    )

    monkeypatch.setattr(service_providers_cli.application,
                        "get_provider", lambda _: provider)

    result = CliRunner().invoke(
        app, ["service-providers", "billing", "docker"])

    assert result.exit_code == 1
    assert "does not support billing checks" in result.output
