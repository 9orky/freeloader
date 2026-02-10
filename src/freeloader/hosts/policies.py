import subprocess
from pathlib import Path

from freeloader.hosts.models import HostEntry
from freeloader.hosts.store import HostStore


def check_reachability(entry: HostEntry) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o", "ConnectTimeout=5",
                "-o", "BatchMode=yes",
                "-o", "StrictHostKeyChecking=no",
                "-p", str(entry.port),
                "-i", str(Path(entry.identity_file).expanduser()),
                f"{entry.user}@{entry.host}",
                "echo ok",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip() or f"exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "Connection timed out"
    except FileNotFoundError:
        return False, "ssh binary not found"


def resolve_entry(alias: str, store: HostStore) -> HostEntry | None:
    return store.get(alias)
