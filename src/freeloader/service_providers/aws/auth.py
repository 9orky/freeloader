import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlencode
from ..base import ServiceProvider, Credentials
from freeloader.secrets.checkers import CredentialStatus, register
import httpx


@register
class AWSChecker(ServiceProvider):
    @property
    def name(self) -> str:
        return "aws"

    @property
    def credential_keys(self) -> list[str]:
        return ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

    def check_credentials(self, credentials: Credentials) -> None:
        access_key = credentials.kv.get("AWS_ACCESS_KEY_ID", "")
        secret_key = credentials.kv.get("AWS_SECRET_ACCESS_KEY", "")

        now = datetime.now(timezone.utc)
        datestamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        region = "us-east-1"
        service = "sts"
        host = "sts.amazonaws.com"

        params = urlencode({
            "Action": "GetCallerIdentity",
            "Version": "2011-06-15",
        })

        canonical_request = f"GET\n/\n{params}\nhost:{host}\nx-amz-date:{amz_date}\n\nhost;x-amz-date\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        scope = f"{datestamp}/{region}/{service}/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        k_date = _sign(f"AWS4{secret_key}".encode(), datestamp)
        k_region = _sign(k_date, region)
        k_service = _sign(k_region, service)
        k_signing = _sign(k_service, "aws4_request")
        signature = hmac.new(
            k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

        auth = f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, SignedHeaders=host;x-amz-date, Signature={signature}"

        resp = httpx.get(
            f"https://{host}/?{params}",
            headers={"Authorization": auth,
                     "X-Amz-Date": amz_date, "Host": host},
            timeout=10.0,
        )
        if resp.status_code == 200:
            text = resp.text
            arn_start = text.find("<Arn>")
            arn_end = text.find("</Arn>")
            arn = text[arn_start + 5:arn_end] if arn_start != - \
                1 else "authenticated"
            return CredentialStatus(valid=True, identity=arn)
        return CredentialStatus(valid=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}")
