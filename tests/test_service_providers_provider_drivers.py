from __future__ import annotations

import json

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from freeloader.service_providers.domain import Credentials, ProviderAuthError
from freeloader.service_providers.infrastructure.providers.gcp import GCPDriver
from freeloader.service_providers.infrastructure.providers.render import RenderDriver
from freeloader.service_providers.infrastructure.providers.vercel import VercelDriver


def test_gcp_driver_validates_service_account_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, data: dict[str, str], timeout: float) -> httpx.Response:
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={"access_token": "token"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    GCPDriver().validate_credentials(
        Credentials({"GCP_SERVICE_ACCOUNT_JSON": json.dumps(
            _service_account_payload())})
    )

    assert captured["url"] == "https://oauth2.googleapis.com/token"
    assert captured["timeout"] == 10.0
    assert captured["data"] is not None
    assert captured["data"]["grant_type"] == "urn:ietf:params:oauth:grant-type:jwt-bearer"
    assert captured["data"]["assertion"]


def test_gcp_driver_rejects_invalid_service_account_json_value() -> None:
    with pytest.raises(
        ProviderAuthError,
        match="Service account JSON value does not contain valid JSON.",
    ):
        GCPDriver().validate_credentials(
            Credentials({"GCP_SERVICE_ACCOUNT_JSON": "not-json"})
        )


def test_vercel_driver_validates_token_with_authenticated_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_get(
        url: str,
        params: dict[str, int],
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        captured["timeout"] = timeout
        return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    VercelDriver().validate_credentials(
        Credentials({"VERCEL_TOKEN": "secret"}))

    assert captured["url"] == "https://api.vercel.com/v3/events"
    assert captured["params"] == {"limit": 1}
    assert captured["headers"] == {"Authorization": "Bearer secret"}
    assert captured["timeout"] == 10.0


def test_render_driver_rejects_invalid_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(
        url: str,
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        return httpx.Response(401, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(ProviderAuthError, match="Invalid Render API key."):
        RenderDriver().validate_credentials(
            Credentials({"RENDER_API_KEY": "bad"}))


def _service_account_payload() -> dict[str, str]:
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    ).decode("utf-8")
    return {
        "client_email": "freeloader-test@example.iam.gserviceaccount.com",
        "private_key": private_key_pem,
        "private_key_id": "test-key-id",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
