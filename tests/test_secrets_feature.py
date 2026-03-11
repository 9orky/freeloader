from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from freeloader.cli import app
from freeloader.secrets.models import SecretEntry, SecretMutationResult
from freeloader.secrets.ports import interface
from freeloader.secrets.storage.models import DEFAULT_NAMESPACE


def test_secrets_package_and_interface_are_importable() -> None:
    importlib.import_module("freeloader.secrets")
    importlib.import_module("freeloader.secrets.ports.interface")


def test_secrets_help_lists_expected_commands() -> None:
    result = CliRunner().invoke(app, ["secrets", "--help"])

    assert result.exit_code == 0
    assert "ls" in result.output
    assert "reveal" in result.output
    assert "add" in result.output
    assert "remove" in result.output


def test_secrets_models_use_storage_default_namespace() -> None:
    assert SecretEntry(name="demo").namespace == DEFAULT_NAMESPACE
    assert SecretMutationResult(name="demo").name == "demo"


def test_secrets_port_reads_via_application_and_normalizes_names(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_read_secrets(names: list[str], namespace: str | None) -> dict[str, str]:
        captured["names"] = names
        captured["namespace"] = namespace
        return {"api_token": "secret"}

    monkeypatch.setattr(interface.application,
                        "read_secrets", fake_read_secrets)

    secrets = interface.Secrets(namespace="ops")
    result = secrets.read_secrets([" API_TOKEN "])

    assert result == {"api_token": "secret"}
    assert captured["names"] == ["api_token"]
    assert captured["namespace"] == "ops"


def test_secrets_port_writes_values_via_application_in_one_call(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_write_secrets(values: dict[str, str], namespace: str | None) -> None:
        captured["values"] = values
        captured["namespace"] = namespace

    monkeypatch.setattr(interface.application,
                        "write_secrets", fake_write_secrets)

    secrets = interface.Secrets(namespace="ops")
    secrets.write_secrets({" API_TOKEN ": "secret", " Deploy_Key ": "ssh-key"})

    assert captured["values"] == {
        "api_token": "secret", "deploy_key": "ssh-key"}
    assert captured["namespace"] == "ops"


def test_secrets_cli_add_calls_application_and_renders_result(monkeypatch) -> None:
    import freeloader.secrets.cli as secrets_cli

    prompts: list[tuple[str, bool]] = []
    outputs: list[str] = []
    calls: list[tuple[str, str, str | None, object]] = []

    monkeypatch.setattr(
        secrets_cli.typer,
        "prompt",
        lambda text, hide_input=False: prompts.append(
            (text, hide_input)) or "token-value",
    )
    monkeypatch.setattr(
        secrets_cli.application,
        "write_secret",
        lambda key, value, namespace: calls.append((key, value, namespace))
        or SecretMutationResult(name=key),
    )
    monkeypatch.setattr(secrets_cli.typer, "echo",
                        lambda message: outputs.append(message))

    result = CliRunner().invoke(
        app, ["secrets", "add", "API_TOKEN", "--namespace", "ops"])

    assert result.exit_code == 0
    assert prompts == [("Value for secret 'API_TOKEN'", True)]
    assert calls[0] == ("API_TOKEN", "token-value", "ops")
    assert outputs == ["Secret 'API_TOKEN' written."]


def test_secrets_cli_list_renders_entries(monkeypatch) -> None:
    import freeloader.secrets.cli as secrets_cli

    outputs: list[str] = []

    monkeypatch.setattr(
        secrets_cli.application,
        "list_secrets",
        lambda namespace: [
            SecretEntry(name="api_token", namespace="ops"),
            SecretEntry(name="deploy_key", namespace="ops"),
        ],
    )
    monkeypatch.setattr(secrets_cli.typer, "echo",
                        lambda message: outputs.append(message))

    result = CliRunner().invoke(app, ["secrets", "ls", "--namespace", "ops"])

    assert result.exit_code == 0
    assert outputs == ["ops/api_token", "ops/deploy_key"]


def test_secrets_cli_reuses_password_saved_in_freeloader_home(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("FREELOADER_VAULT_PASSWORD", raising=False)

    runner = CliRunner()
    env = {"FREELOADER_HOME": str(tmp_path)}
    (tmp_path / "vault-password").write_text("vault-pass")

    add_result = runner.invoke(
        app,
        ["secrets", "add", "API_TOKEN", "--namespace", "ops"],
        input="token-value\n",
        env=env,
    )
    list_result = runner.invoke(
        app,
        ["secrets", "ls", "--namespace", "ops"],
        env=env,
    )

    assert add_result.exit_code == 0, add_result.output
    assert list_result.exit_code == 0, list_result.output
    assert "Vault password" not in list_result.output
    assert "ops/API_TOKEN" in list_result.output


def test_secrets_storage_reads_legacy_session_password_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("FREELOADER_VAULT_PASSWORD", raising=False)
    monkeypatch.setenv("FREELOADER_HOME", str(tmp_path))

    from freeloader.secrets import application

    (tmp_path / "vault-password").write_text("vault-pass")
    application.write_secret("api_token", "secret", "ops")

    password_file = tmp_path / "vault-password"
    legacy_password_file = tmp_path / "sessions" / "session"
    password_file.unlink()
    legacy_password_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_password_file.write_text("vault-pass")

    assert application.read_secrets(["api_token"], "ops") == {
        "api_token": "secret"}
    assert password_file.read_text() == "vault-pass"
