from __future__ import annotations

from dataclasses import dataclass

from freeloader.hosts.models import HostEntry
from freeloader.hosts.policies import check_reachability, resolve_entry
from freeloader.hosts.scanner import SSHConfigHost, SSHScanner
from freeloader.hosts.store import HostStore


@dataclass(frozen=True)
class ScanUseCaseResult:
    config_hosts: list[SSHConfigHost]
    key_count: int
    orphan_key_names: list[str]
    orphan_known_hosts: list[str]
    known_hosts_count: int
    hashed_count: int


@dataclass(frozen=True)
class AddResult:
    alias: str
    host: str
    replaced: bool


@dataclass(frozen=True)
class RemoveResult:
    alias: str
    found: bool


@dataclass(frozen=True)
class ListResult:
    hosts: list[HostEntry]


@dataclass(frozen=True)
class CheckResult:
    alias: str
    host: str
    reachable: bool
    error: str = ""


class HostUseCases:
    def __init__(self, store: HostStore, scanner: SSHScanner | None = None) -> None:
        self._store = store
        self._scanner = scanner or SSHScanner()

    def scan(self) -> ScanUseCaseResult:
        result = self._scanner.scan()
        hashed = sum(1 for kh in result.known_hosts if kh.is_hashed)
        return ScanUseCaseResult(
            config_hosts=result.config_hosts,
            key_count=len(result.keys),
            orphan_key_names=[k.path.name for k in result.orphan_keys],
            orphan_known_hosts=[
                kh.hostname for kh in result.orphan_known_hosts],
            known_hosts_count=len(result.known_hosts),
            hashed_count=hashed,
        )

    def import_host(self, ssh_host: SSHConfigHost) -> AddResult:
        existing = self._store.get(ssh_host.alias)
        entry = HostEntry(
            alias=ssh_host.alias,
            host=ssh_host.hostname or ssh_host.alias,
            user=ssh_host.user,
            port=ssh_host.port,
            identity_file=ssh_host.identity_file or "~/.ssh/id_ed25519",
        )
        self._store.add(entry)
        return AddResult(
            alias=entry.alias,
            host=entry.host,
            replaced=existing is not None,
        )

    def add(
        self,
        alias: str,
        host: str,
        user: str = "root",
        port: int = 22,
        identity_file: str = "~/.ssh/id_ed25519",
        tags: list[str] | None = None,
    ) -> AddResult:
        existing = self._store.get(alias)
        entry = HostEntry(
            alias=alias,
            host=host,
            user=user,
            port=port,
            identity_file=identity_file,
            tags=tags or [],
        )
        self._store.add(entry)
        return AddResult(alias=alias, host=host, replaced=existing is not None)

    def remove(self, alias: str) -> RemoveResult:
        found = self._store.remove(alias)
        return RemoveResult(alias=alias, found=found)

    def list(self) -> ListResult:
        return ListResult(hosts=self._store.list_all())

    def check(self, alias: str) -> CheckResult:
        entry = resolve_entry(alias, self._store)
        if not entry:
            return CheckResult(alias=alias, host="", reachable=False, error="Host not found")

        reachable, error = check_reachability(entry)
        return CheckResult(alias=alias, host=entry.host, reachable=reachable, error=error)
