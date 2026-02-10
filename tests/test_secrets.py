from freeloader.credentials.usecases.secrets import SecretUseCases


class TestSecretSet:
    def test_stores_and_returns_key(self, secret_usecases: SecretUseCases) -> None:
        result = secret_usecases.set("MY_KEY", "my_value")
        assert result.success
        assert result.key == "MY_KEY"

    def test_overwrites_existing(self, secret_usecases: SecretUseCases) -> None:
        secret_usecases.set("K", "v1")
        secret_usecases.set("K", "v2")
        assert secret_usecases.get("K").value == "v2"


class TestSecretGet:
    def test_retrieves_stored_value(self, secret_usecases: SecretUseCases) -> None:
        secret_usecases.set("K", "v")
        result = secret_usecases.get("K")
        assert result.success
        assert result.value == "v"

    def test_returns_error_for_missing(self, secret_usecases: SecretUseCases) -> None:
        result = secret_usecases.get("NOPE")
        assert not result.success
        assert "not found" in result.error


class TestSecretList:
    def test_empty_vault(self, secret_usecases: SecretUseCases) -> None:
        result = secret_usecases.list()
        assert result.success
        assert result.keys == []

    def test_lists_all_keys(self, secret_usecases: SecretUseCases) -> None:
        secret_usecases.set("A", "1")
        secret_usecases.set("B", "2")
        result = secret_usecases.list()
        assert sorted(result.keys) == ["A", "B"]


class TestSecretDelete:
    def test_deletes_existing(self, secret_usecases: SecretUseCases) -> None:
        secret_usecases.set("K", "v")
        result = secret_usecases.delete("K")
        assert result.success
        assert secret_usecases.get("K").success is False

    def test_returns_error_for_missing(self, secret_usecases: SecretUseCases) -> None:
        result = secret_usecases.delete("NOPE")
        assert not result.success
        assert "not found" in result.error
