import typer

from freeloader.shared import console

from . import application


service_providers_app = typer.Typer(
    name="service-providers",
    help="Manage service provider integrations",
    no_args_is_help=True,
)


def _run_obtain_steps(steps: list) -> dict[str, str]:
    context: dict[str, str] = {}
    for step in steps:
        match step.action:
            case "input":
                context[step.value] = typer.prompt(step.value)
            case "info":
                console.info(step.value.format(**context))
            case "open_url":
                console.info(f"Open: {step.value.format(**context)}")
    return context


@service_providers_app.command("ls", help="List installed service providers")
@console.handle_errors
def list_service_providers() -> None:
    providers = application.list_providers()
    headers = [
        "Name",
        "Requires Auth",
        "Requires Tech Stack",
        "Supports Billing",
        "Billing Check Cost",
    ]
    rows = [
        [
            provider.name,
            provider.requires_auth,
            provider.requires_tech_stack,
            provider.supports_billing,
            provider.billing_check_cost.value if provider.billing_check_cost else "-",
        ]
        for provider in providers
    ]
    console.print_table("Installed Providers", headers, rows)


@service_providers_app.command(help="Validate and store provider credentials")
@console.handle_errors
def auth(name: str = typer.Argument(..., help="Service provider name")) -> None:
    info = application.get_provider(name)
    collected = _run_obtain_steps(info.obtain_token_steps)
    remaining = [key for key in info.auth_keys if key not in collected]

    credentials = dict(collected)
    if remaining:
        credentials.update(console.prompter(remaining, True))

    result = application.authorize_provider(name, credentials)
    if result.stored_credentials:
        stored = ", ".join(result.stored_credentials)
        console.ok(f"Stored credentials for {result.provider}: {stored}")
        return

    console.ok(
        f"{result.provider} is available and requires no stored credentials.")


@service_providers_app.command(help="Fetch current billing for a provider")
@console.handle_errors
def billing(name: str = typer.Argument(..., help="Service provider name")) -> None:
    info = application.get_provider(name)
    if not info.supports_billing:
        raise ValueError(f"Provider '{name}' does not support billing checks")

    if info.billing_check_cost and info.billing_check_cost.value == "paid":
        console.warn("This billing check may incur provider charges.")

    result = application.check_billing(name)
    if result.report is None:
        raise ValueError(f"No billing report returned for provider '{name}'")

    report = result.report
    console.print_dict(
        {
            "provider": report.provider,
            "period": report.period,
            "total_usd": f"{report.total_usd:.4f}",
            "currency": report.currency,
            "check_cost": result.billing_check_cost.value if result.billing_check_cost else "unknown",
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
