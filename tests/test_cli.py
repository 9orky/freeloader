from click.testing import CliRunner

from freeloader.cli import app


def test_cli_help_lists_registered_feature_groups() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "hosts" in result.output
    assert "project" in result.output
    assert "secrets" in result.output
    assert "service-providers" in result.output
