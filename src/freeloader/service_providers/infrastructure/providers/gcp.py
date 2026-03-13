from __future__ import annotations

import base64
import json
import time
from typing import Mapping, cast

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from freeloader.service_providers.domain import (
    AuthSpec,
    BillingReport,
    CredentialKey,
    Credentials,
    DriverSupportReport,
    ObtainCredentialAction,
    ObtainCredentialStep,
    ProviderAuthError,
    ProviderCapabilityError,
    ServiceProvider,
)
from freeloader.service_providers.domain.repository import ProviderDriver


_DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
_JWT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"
_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


class GCPDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="gcp",
            auth=AuthSpec(
                credential_keys=(CredentialKey("GCP_SERVICE_ACCOUNT_JSON"),),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Create a Google Cloud service account key and store the raw JSON in your vault as a string value.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://console.cloud.google.com/iam-admin/serviceaccounts",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.input,
                        value="GCP_SERVICE_ACCOUNT_JSON",
                    ),
                ),
            ),
        )

    def check_local_support(self) -> DriverSupportReport:
        return DriverSupportReport(driver=self.provider.name)

    def validate_credentials(self, credentials: Credentials) -> None:
        auth = self.provider.auth
        assert auth is not None
        credentials = credentials.require(
            auth.credential_keys,
            provider_name=str(self.provider.name),
        )

        service_account = _load_service_account(
            credentials["GCP_SERVICE_ACCOUNT_JSON"])
        token_uri = str(service_account.get("token_uri") or _DEFAULT_TOKEN_URI)
        assertion = _build_jwt_assertion(service_account, token_uri)

        try:
            response = httpx.post(
                token_uri,
                data={
                    "grant_type": _JWT_GRANT_TYPE,
                    "assertion": assertion,
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderAuthError(
                "gcp", "Unable to reach the Google OAuth token endpoint."
            ) from exc

        if response.status_code >= 400:
            raise ProviderAuthError("gcp", _google_error_message(response))

        access_token = response.json().get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise ProviderAuthError(
                "gcp", "Google OAuth token exchange returned no access token."
            )

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        raise ProviderCapabilityError(str(self.provider.name), "billing")


def _load_service_account(raw: str) -> dict[str, str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderAuthError(
            "gcp", "Service account JSON value does not contain valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ProviderAuthError(
            "gcp", "Service account JSON value must contain a JSON object."
        )

    client_email = payload.get("client_email")
    private_key = payload.get("private_key")
    if not isinstance(client_email, str) or not client_email.strip():
        raise ProviderAuthError(
            "gcp", "Service account JSON is missing 'client_email'."
        )
    if not isinstance(private_key, str) or not private_key.strip():
        raise ProviderAuthError(
            "gcp", "Service account JSON is missing 'private_key'."
        )

    return {
        "client_email": client_email,
        "private_key": private_key,
        "private_key_id": str(payload.get("private_key_id") or ""),
        "token_uri": str(payload.get("token_uri") or _DEFAULT_TOKEN_URI),
    }


def _build_jwt_assertion(service_account: dict[str, str], token_uri: str) -> str:
    now = int(time.time())
    header = {
        "alg": "RS256",
        "typ": "JWT",
    }
    if service_account["private_key_id"]:
        header["kid"] = service_account["private_key_id"]

    claims = {
        "iss": service_account["client_email"],
        "sub": service_account["client_email"],
        "aud": token_uri,
        "scope": _CLOUD_PLATFORM_SCOPE,
        "iat": now,
        "exp": now + 3600,
    }

    signing_input = (
        f"{_base64url_json(header)}.{_base64url_json(claims)}"
    )
    try:
        private_key = cast(
            RSAPrivateKey,
            load_pem_private_key(
                service_account["private_key"].encode("utf-8"),
                password=None,
            ),
        )
        signature = private_key.sign(
            signing_input.encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except (TypeError, ValueError) as exc:
        raise ProviderAuthError(
            "gcp", "Service account JSON contains an invalid private key."
        ) from exc

    return f"{signing_input}.{_base64url(signature)}"


def _base64url_json(payload: Mapping[str, str | int]) -> str:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return _base64url(encoded)


def _base64url(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _google_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        description = payload.get("error_description") or payload.get("error")
        if isinstance(description, str) and description.strip():
            return description.strip()

    if response.status_code == 401:
        return "Invalid Google Cloud service account credentials."
    return f"Google OAuth token exchange failed with status {response.status_code}."
