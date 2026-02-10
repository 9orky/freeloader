from freeloader.hosts.scanner import SSHScanner
from freeloader.hosts.store import HostStore
from freeloader.hosts.usecases import HostUseCases
from freeloader.shared.paths import hosts_path


class HostsFactory:
    def usecases(self) -> HostUseCases:
        return HostUseCases(
            store=HostStore(hosts_path()),
            scanner=SSHScanner(),
        )
