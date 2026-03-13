import typer

from freeloader.shared import console

from .. import application


service_providers_app = typer.Typer(
    name="service-providers",
    help="Manage service provider integrations",
    no_args_is_help=True,
)


def _run_obtain_steps(steps: tuple) -> dict[str, str]:
    context: dict[str, str] = {}
    for step in steps:
        match step.action.value:
            case "input":
                context[step.value] = typer.prompt(step.value)
            case "info":
                console.info(step.value.format(**context))
            case "open_url":
                console.info(f"Open: {step.value.format(**context)}")
    return context


def _support_description(provider) -> str:
    if provider.support:
        return ", ".join(str(requirement.command) for requirement in provider.support)
    return "remote"


def _billing_check_cost(provider) -> str:
    if provider.billing is None:
        return "-"

    check_cost = provider.billing.check_cost
    return check_cost.value if hasattr(check_cost, "value") else str(check_cost)


@service_providers_app.command("ls", help="List installed service providers")
@console.handle_errors
def list_service_providers() -> None:
    providers = application.list_providers()
    headers = [
        "Name",
        "Requires Auth",
        "Local Support",
        "Supports Billing",
        "Billing Check Cost",
    ]
    rows = [
        [
            str(provider.name),
            provider.requires_auth,
            _support_description(provider),
            provider.supports_billing,
            _billing_check_cost(provider),
        ]
        for provider in providers
    ]
    console.print_table("Installed Providers", headers, rows)


@service_providers_app.command(help="Validate and store provider credentials")
@console.handle_errors
def auth(name: str = typer.Argument(..., help="Service provider name")) -> None:
    provider = application.get_provider(name)
    auth_spec = provider.auth

    credentials: dict[str, str] = {}
    if auth_spec is not None:
        credentials.update(_run_obtain_steps(auth_spec.obtain_steps))
        remaining = [
            str(key)
            for key in auth_spec.credential_keys
            if str(key) not in credentials
        ]
        if remaining:
            credentials.update(console.prompter(remaining, True))

    result = application.authorize_provider(name, credentials)
    if result.stored_credentials:
        stored = ", ".join(str(key) for key in result.stored_credentials)
        console.ok(f"Stored credentials for {result.provider}: {stored}")
        return

    console.ok(
        f"{result.provider} is available and requires no stored credentials.")


@service_providers_app.command(help="Fetch current billing for a provider")
@console.handle_errors
def billing(name: str = typer.Argument(..., help="Service provider name")) -> None:
    provider = application.get_provider(name)
    if not provider.supports_billing:
        raise ValueError(f"Provider '{name}' does not support billing checks")

    check_cost = _billing_check_cost(provider)
    if check_cost == "paid":
        console.warn("This billing check may incur provider charges.")

    report = application.check_billing(name)
    console.print_dict(
        {
            "provider": str(report.provider),
            "period": report.period,
            "total_usd": f"{report.total_usd:.4f}",
            "currency": report.currency,
            "check_cost": check_cost,
        },
        title="Billing Summary",
        as_tree=False,
    )

    if report.items:
        console.print_table(
            "Billed Services",
            ["Service", "Amount", "Currency"],
            [
                [item.service, f"{item.amount_usd:.4f}", item.currency]
                for item in report.items
            ],
        )
    else:
        console.info("No billed line items found.")

    if report.free_tier_usage:
        console.print_table(
            "Free Tier Usage",
            ["Service", "Metric", "Used", "Limit", "Unit"],
            [
                [
                    usage.service,
                    usage.metric,
                    str(usage.used),
                    str(usage.limit),
                    usage.unit,
                ]
                for usage in report.free_tier_usage
            ],
        )
