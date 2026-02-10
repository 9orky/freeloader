from freeloader.credentials.usecases.providers import ProviderUseCases


class TestListRequiredSecrets:
    def test_returns_required_for_github(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.list_required_secrets("github")
        assert "GITHUB_TOKEN" in result.required
        assert "GITHUB_TOKEN" in result.missing_keys

    def test_no_missing_when_seeded(self, seeded_provider_usecases: ProviderUseCases) -> None:
        result = seeded_provider_usecases.list_required_secrets("github")
        assert "GITHUB_TOKEN" in result.required
        assert result.missing_keys == []

    def test_unknown_provider_returns_empty(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.list_required_secrets("nonexistent")
        assert result.required == {}


class TestAddProvider:
    def test_stores_secrets_and_validates(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.add("github", {"GITHUB_TOKEN": "ghp_new"})
        assert "GITHUB_TOKEN" in result.stored_keys
        assert result.credential_status.valid
        assert result.credential_status.identity == "github-user"

    def test_already_present_secrets_not_stored_again(self, seeded_provider_usecases: ProviderUseCases) -> None:
        result = seeded_provider_usecases.add("github", {})
        assert result.stored_keys == []
        assert "GITHUB_TOKEN" in result.already_present

    def test_aws_requires_two_secrets(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.add("aws", {
            "AWS_ACCESS_KEY_ID": "AKIA",
            "AWS_SECRET_ACCESS_KEY": "secret",
        })
        assert "AWS_ACCESS_KEY_ID" in result.stored_keys
        assert "AWS_SECRET_ACCESS_KEY" in result.stored_keys


class TestCheckProviders:
    def test_all_valid_when_seeded(self, seeded_provider_usecases: ProviderUseCases) -> None:
        result = seeded_provider_usecases.check()
        assert len(result.rows) > 0
        for row in result.rows:
            assert row.valid

    def test_invalid_when_empty_vault(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.check()
        for row in result.rows:
            assert not row.valid


class TestListProviders:
    def test_lists_all_providers(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.list()
        provider_names = {p.provider for p in result.providers}
        assert "github" in provider_names
        assert "gitlab" in provider_names
        assert "coolify" in provider_names
        assert "aws" in provider_names

    def test_shows_secret_presence(self, seeded_provider_usecases: ProviderUseCases) -> None:
        result = seeded_provider_usecases.list()
        github = next(p for p in result.providers if p.provider == "github")
        assert ("GITHUB_TOKEN", True) in github.secrets

    def test_shows_secret_absence(self, provider_usecases: ProviderUseCases) -> None:
        result = provider_usecases.list()
        github = next(p for p in result.providers if p.provider == "github")
        assert ("GITHUB_TOKEN", False) in github.secrets
