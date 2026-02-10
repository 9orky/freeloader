from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SSHConfigHost:
    alias: str
    hostname: str = ""
    user: str = "root"
    port: int = 22
    identity_file: str = ""


@dataclass
class SSHKey:
    path: Path
    algorithm: str = "unknown"
    referenced_by: list[str] = field(default_factory=list)


@dataclass
class KnownHost:
    hostname: str
    is_hashed: bool = False
    in_config: bool = False


@dataclass
class ScanResult:
    config_hosts: list[SSHConfigHost]
    keys: list[SSHKey]
    known_hosts: list[KnownHost]
    orphan_keys: list[SSHKey]
    orphan_known_hosts: list[KnownHost]


class SSHScanner:
    def __init__(self, ssh_dir: Path | None = None) -> None:
        self._ssh_dir = ssh_dir or Path.home() / ".ssh"

    def scan(self) -> ScanResult:
        config_hosts = self._parse_config()
        keys = self._discover_keys()
        known = self._parse_known_hosts()

        config_hostnames = {h.hostname for h in config_hosts}
        config_identity_files = set()
        for h in config_hosts:
            if h.identity_file:
                config_identity_files.add(
                    self._resolve_key_path(h.identity_file))

        for key in keys:
            for h in config_hosts:
                if h.identity_file and self._resolve_key_path(h.identity_file) == key.path:
                    key.referenced_by.append(h.alias)

        for kh in known:
            kh.in_config = kh.hostname in config_hostnames

        orphan_keys = [k for k in keys if not k.referenced_by]
        orphan_known = [
            kh for kh in known if not kh.in_config and not kh.is_hashed]

        return ScanResult(
            config_hosts=config_hosts,
            keys=keys,
            known_hosts=known,
            orphan_keys=orphan_keys,
            orphan_known_hosts=orphan_known,
        )

    def _parse_config(self) -> list[SSHConfigHost]:
        config_path = self._ssh_dir / "config"
        if not config_path.exists():
            return []

        hosts: list[SSHConfigHost] = []
        current: SSHConfigHost | None = None

        for line in config_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            match = re.match(r"^Host\s+(.+)$", stripped, re.IGNORECASE)
            if match:
                if current and current.alias != "*":
                    hosts.append(current)
                alias = match.group(1).strip()
                current = SSHConfigHost(alias=alias)
                continue

            if current is None:
                continue

            key_match = re.match(r"^(\w+)\s+(.+)$", stripped)
            if not key_match:
                continue

            key, value = key_match.group(1).lower(), key_match.group(2).strip()
            if key == "hostname":
                current.hostname = value
            elif key == "user":
                current.user = value
            elif key == "port":
                current.port = int(value)
            elif key == "identityfile":
                current.identity_file = value

        if current and current.alias != "*":
            hosts.append(current)

        return hosts

    def _discover_keys(self) -> list[SSHKey]:
        if not self._ssh_dir.exists():
            return []

        keys: list[SSHKey] = []
        skip_suffixes = {".pub", ".known_hosts", ".config"}
        skip_names = {"config", "known_hosts",
                      "authorized_keys", "environment"}

        for path in sorted(self._ssh_dir.iterdir()):
            if not path.is_file():
                continue
            if path.suffix in skip_suffixes:
                continue
            if path.name in skip_names:
                continue
            if path.name.startswith("known_hosts"):
                continue

            algo = self._detect_key_algorithm(path)
            if algo:
                keys.append(SSHKey(path=path, algorithm=algo))

        return keys

    def _detect_key_algorithm(self, path: Path) -> str | None:
        try:
            first_line = path.read_text(errors="ignore").split("\n", 1)[0]
        except (OSError, UnicodeDecodeError):
            return None

        if "OPENSSH PRIVATE KEY" in first_line:
            name = path.name.lower()
            if "ed25519" in name:
                return "ed25519"
            if "ecdsa" in name:
                return "ecdsa"
            if "rsa" in name:
                return "rsa"
            if "dsa" in name:
                return "dsa"
            return "openssh"

        if "RSA PRIVATE KEY" in first_line:
            return "rsa"
        if "EC PRIVATE KEY" in first_line:
            return "ecdsa"
        if "DSA PRIVATE KEY" in first_line:
            return "dsa"

        return None

    def _parse_known_hosts(self) -> list[KnownHost]:
        kh_path = self._ssh_dir / "known_hosts"
        if not kh_path.exists():
            return []

        hosts: list[KnownHost] = []
        seen: set[str] = set()

        for line in kh_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            host_part = stripped.split()[0] if stripped.split() else ""
            if not host_part:
                continue

            is_hashed = host_part.startswith("|1|")

            if is_hashed:
                key = host_part
                if key not in seen:
                    seen.add(key)
                    hosts.append(
                        KnownHost(hostname="(hashed)", is_hashed=True))
            else:
                for entry in host_part.split(","):
                    entry = entry.strip().strip("[]")
                    if entry and entry not in seen:
                        seen.add(entry)
                        hosts.append(KnownHost(hostname=entry))

        return hosts

    def _resolve_key_path(self, identity_file: str) -> Path:
        return Path(identity_file).expanduser().resolve()
