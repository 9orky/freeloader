from pathlib import Path

import pytest

from freeloader.hosts.models import HostEntry
from freeloader.hosts.scanner import SSHScanner, SSHConfigHost
from freeloader.hosts.store import HostStore
from freeloader.hosts.usecases import HostUseCases


# ---------- Scanner tests ----------

class TestSSHScanner:
    def test_parse_config(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text(
            "Host pi\n"
            "  HostName 192.168.1.50\n"
            "  User pi\n"
            "  Port 22\n"
            "  IdentityFile ~/.ssh/id_ed25519\n"
            "\n"
            "Host gpu\n"
            "  HostName 10.0.0.5\n"
            "  User gorky\n"
            "  Port 2222\n"
            "  IdentityFile ~/.ssh/gpu_key\n"
        )
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.config_hosts) == 2
        assert result.config_hosts[0].alias == "pi"
        assert result.config_hosts[0].hostname == "192.168.1.50"
        assert result.config_hosts[0].user == "pi"
        assert result.config_hosts[1].alias == "gpu"
        assert result.config_hosts[1].port == 2222

    def test_parse_config_skips_wildcard(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text(
            "Host *\n"
            "  ServerAliveInterval 60\n"
            "\n"
            "Host mybox\n"
            "  HostName 1.2.3.4\n"
        )
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.config_hosts) == 1
        assert result.config_hosts[0].alias == "mybox"

    def test_empty_ssh_dir(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert result.config_hosts == []
        assert result.keys == []
        assert result.known_hosts == []

    def test_discover_keys(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n")
        (ssh_dir / "id_ed25519.pub").write_text("ssh-ed25519 AAAA... user@host\n")
        (ssh_dir / "id_rsa").write_text("-----BEGIN RSA PRIVATE KEY-----\nfake\n")
        (ssh_dir / "config").write_text("")
        (ssh_dir / "known_hosts").write_text("")
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.keys) == 2
        algos = {k.algorithm for k in result.keys}
        assert "ed25519" in algos
        assert "rsa" in algos

    def test_orphan_keys_detected(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n")
        (ssh_dir / "old_deploy_key").write_text("-----BEGIN RSA PRIVATE KEY-----\nfake\n")
        (ssh_dir / "config").write_text(
            "Host pi\n"
            "  HostName 192.168.1.50\n"
            f"  IdentityFile {ssh_dir / 'id_ed25519'}\n"
        )
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.orphan_keys) == 1
        assert result.orphan_keys[0].path.name == "old_deploy_key"

    def test_known_hosts_parsing(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "known_hosts").write_text(
            "192.168.1.50 ssh-ed25519 AAAA...\n"
            "10.0.0.5 ssh-rsa AAAA...\n"
            "|1|base64hash|base64hash ssh-ed25519 AAAA...\n"
        )
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.known_hosts) == 3
        hashed = [kh for kh in result.known_hosts if kh.is_hashed]
        assert len(hashed) == 1

    def test_orphan_known_hosts(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text(
            "Host pi\n  HostName 192.168.1.50\n"
        )
        (ssh_dir / "known_hosts").write_text(
            "192.168.1.50 ssh-ed25519 AAAA...\n"
            "10.99.99.99 ssh-rsa AAAA...\n"
        )
        scanner = SSHScanner(ssh_dir)
        result = scanner.scan()
        assert len(result.orphan_known_hosts) == 1
        assert result.orphan_known_hosts[0].hostname == "10.99.99.99"


# ---------- Store tests ----------

class TestHostStore:
    def test_add_and_list(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        store.add(HostEntry(alias="pi", host="192.168.1.50", user="pi"))
        store.add(HostEntry(alias="gpu", host="10.0.0.5",
                  user="gorky", port=2222))
        hosts = store.list_all()
        assert len(hosts) == 2
        assert hosts[0].alias == "pi"
        assert hosts[1].alias == "gpu"

    def test_add_replaces_existing(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        store.add(HostEntry(alias="pi", host="192.168.1.50"))
        store.add(HostEntry(alias="pi", host="192.168.1.100"))
        hosts = store.list_all()
        assert len(hosts) == 1
        assert hosts[0].host == "192.168.1.100"

    def test_remove(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        store.add(HostEntry(alias="pi", host="192.168.1.50"))
        assert store.remove("pi") is True
        assert store.list_all() == []

    def test_remove_nonexistent(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        assert store.remove("nope") is False

    def test_get(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        store.add(HostEntry(alias="pi", host="192.168.1.50"))
        entry = store.get("pi")
        assert entry is not None
        assert entry.host == "192.168.1.50"

    def test_get_nonexistent(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        assert store.get("nope") is None

    def test_empty_store(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        assert store.list_all() == []

    def test_tags_persisted(self, tmp_path: Path) -> None:
        store = HostStore(tmp_path / "hosts.yaml")
        store.add(
            HostEntry(alias="pi", host="192.168.1.50", tags=["arm", "home"]))
        entry = store.get("pi")
        assert entry is not None
        assert "arm" in entry.tags
        assert "home" in entry.tags


# ---------- UseCases tests ----------

class TestHostUseCases:
    def _make_uc(self, tmp_path: Path, ssh_dir: Path | None = None) -> HostUseCases:
        store = HostStore(tmp_path / "hosts.yaml")
        scanner = SSHScanner(ssh_dir) if ssh_dir else SSHScanner(
            tmp_path / "empty_ssh")
        return HostUseCases(store, scanner)

    def test_scan_returns_results(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text("Host pi\n  HostName 192.168.1.50\n  User pi\n")
        (ssh_dir / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n")
        uc = self._make_uc(tmp_path, ssh_dir)
        result = uc.scan()
        assert len(result.config_hosts) == 1
        assert result.key_count == 1

    def test_add_and_list(self, tmp_path: Path) -> None:
        uc = self._make_uc(tmp_path)
        uc.add("pi", "192.168.1.50", user="pi")
        uc.add("gpu", "10.0.0.5", port=2222, tags=["cuda"])
        result = uc.list()
        assert len(result.hosts) == 2

    def test_import_host(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text("Host pi\n  HostName 192.168.1.50\n  User pi\n")
        uc = self._make_uc(tmp_path, ssh_dir)
        scan = uc.scan()
        result = uc.import_host(scan.config_hosts[0])
        assert result.alias == "pi"
        assert result.host == "192.168.1.50"
        assert result.replaced is False

    def test_import_host_replaces(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "config").write_text("Host pi\n  HostName 192.168.1.50\n  User pi\n")
        uc = self._make_uc(tmp_path, ssh_dir)
        scan = uc.scan()
        uc.import_host(scan.config_hosts[0])
        result = uc.import_host(scan.config_hosts[0])
        assert result.replaced is True

    def test_remove(self, tmp_path: Path) -> None:
        uc = self._make_uc(tmp_path)
        uc.add("pi", "192.168.1.50")
        result = uc.remove("pi")
        assert result.found is True
        assert uc.list().hosts == []

    def test_remove_nonexistent(self, tmp_path: Path) -> None:
        uc = self._make_uc(tmp_path)
        result = uc.remove("nope")
        assert result.found is False

    def test_check_not_found(self, tmp_path: Path) -> None:
        uc = self._make_uc(tmp_path)
        result = uc.check("nope")
        assert result.reachable is False
        assert "not found" in result.error.lower()
