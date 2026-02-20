from pathlib import Path

import typer

from freeloader.factory import Factory
from freeloader.shared.console import error, handle_errors, info, print_table, success, warn


hosts_app = typer.Typer(
    name="hosts", help="Manage SSH host inventory", no_args_is_help=True)


@hosts_app.command(help="Discover hosts from ~/.ssh/config and keys")
@handle_errors
def scan() -> None:
    uc = Factory().hosts.usecases()
    result = uc.scan()

    if result.key_count:
        info(f"Found {result.key_count} SSH key(s) in ~/.ssh/")

    if result.config_hosts:
        rows = []
        for h in result.config_hosts:
            host_str = h.hostname or h.alias
            if h.port != 22:
                host_str += f":{h.port}"
            key = Path(h.identity_file).name if h.identity_file else "—"
            rows.append([h.alias, host_str, h.user, key])
        print_table(
            f"SSH Config — {len(result.config_hosts)} host(s)",
            ["Alias", "Host", "User", "Key"],
            rows,
        )
    else:
        info("No hosts found in ~/.ssh/config")

    if result.orphan_key_names:
        warn(
            f"Orphan keys (not referenced by any host): {', '.join(result.orphan_key_names)}")

    if result.orphan_known_hosts:
        warn(
            f"IPs in known_hosts but not in config: {', '.join(result.orphan_known_hosts[:10])}")

    if result.hashed_count:
        info(f"{result.hashed_count} hashed entries in known_hosts (cannot resolve)")

    if result.config_hosts:
        info("Import with: fl hosts import <alias>  (or 'all' for everything)")


@hosts_app.command("import", help="Import a host from SSH config into inventory")
@handle_errors
def import_host(
    alias: str = typer.Argument(...,
                                help="SSH config alias to import, or 'all'"),
) -> None:
    uc = Factory().hosts.usecases()
    scan_result = uc.scan()

    if alias == "all":
        for h in scan_result.config_hosts:
            result = uc.import_host(h)
            tag = "updated" if result.replaced else "imported"
            success(f"{result.alias} → {result.host} ({tag})")
        return

    matched = next(
        (h for h in scan_result.config_hosts if h.alias == alias), None)
    if not matched:
        error(f"No host '{alias}' found in SSH config")
        raise typer.Exit(1)

    result = uc.import_host(matched)
    tag = "updated" if result.replaced else "imported"
    success(f"{result.alias} → {result.host} ({tag})")


@hosts_app.command(help="List registered hosts")
@handle_errors
def list() -> None:
    uc = Factory().hosts.usecases()
    result = uc.list()
    if not result.hosts:
        info("No hosts registered. Run 'fl hosts scan' to discover them.")
        return
    rows = []
    for h in result.hosts:
        host_str = h.host
        if h.port != 22:
            host_str += f":{h.port}"
        key = Path(h.identity_file).name
        tags = ", ".join(h.tags) if h.tags else "—"
        rows.append([h.alias, host_str, h.user, key, tags])
    print_table("Host Inventory", [
                "Alias", "Host", "User", "Key", "Tags"], rows)


@hosts_app.command(help="Register a host manually")
@handle_errors
def add(
    alias: str = typer.Argument(..., help="Short name for the host"),
    host: str = typer.Argument(..., help="IP address or hostname"),
    user: str = typer.Option("root", help="SSH user"),
    port: int = typer.Option(22, help="SSH port"),
    identity_file: str = typer.Option(
        "~/.ssh/id_ed25519", "--key", help="Path to private key"),
    tags: str = typer.Option("", help="Comma-separated tags"),
) -> None:
    tag_list = [t.strip()
                for t in tags.split(",") if t.strip()] if tags else []
    uc = Factory().hosts.usecases()
    result = uc.add(alias, host, user, port, identity_file, tag_list)
    tag = "updated" if result.replaced else "added"
    success(f"{result.alias} → {result.host} ({tag})")


@hosts_app.command(help="Remove a host from inventory")
@handle_errors
def remove(alias: str = typer.Argument(..., help="Host alias to remove")) -> None:
    uc = Factory().hosts.usecases()
    result = uc.remove(alias)
    if result.found:
        success(f"Removed '{result.alias}'")
    else:
        error(f"Host '{result.alias}' not found")
        raise typer.Exit(1)


@hosts_app.command(help="Check if hosts are reachable via SSH")
@handle_errors
def check(
    alias: str = typer.Argument(
        None, help="Host alias to check (omit for all)"),
) -> None:
    uc = Factory().hosts.usecases()
    if alias:
        result = uc.check(alias)
        if result.reachable:
            success(f"{result.alias} ({result.host}) — reachable")
        else:
            error(f"{result.alias} ({result.host}) — {result.error}")
            raise typer.Exit(1)
    else:
        all_hosts = uc.list()
        if not all_hosts.hosts:
            info("No hosts registered")
            return
        for h in all_hosts.hosts:
            result = uc.check(h.alias)
            if result.reachable:
                success(f"{result.alias} ({result.host}) — reachable")
            else:
                error(f"{result.alias} ({result.host}) — {result.error}")
