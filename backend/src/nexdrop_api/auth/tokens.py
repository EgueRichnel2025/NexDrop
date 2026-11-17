"""Short-lived signed access tokens and opaque refresh-token primitives."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt


class InvalidAccessTokenError(ValueError):
    """Raised when an access token is invalid or fails claim validation."""


def create_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    secret: str,
    issuer: str,
    audience: str,
    lifetime: timedelta = timedelta(minutes=15),
) -> str:
    """Create a minimal HS256 access token with explicit issuer and audience."""
    if len(secret.encode("utf-8")) < 32:
        raise ValueError("JWT signing secret must contain at least 32 bytes.")
    if lifetime <= timedelta(0):
        raise ValueError("Access-token lifetime must be positive.")

    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "sid": str(session_id),
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime,
        "jti": secrets.token_urlsafe(16),
        "typ": "access",
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def decode_access_token(
    token: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
) -> dict[str, object]:
    """Validate algorithm, signature, issuer, audience and registered claims."""
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            audience=audience,
            options={
                "require": ["sub", "sid", "iss", "aud", "iat", "nbf", "exp", "jti"],
            },
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessTokenError("Invalid access token.") from exc

    if claims.get("typ") != "access":
        raise InvalidAccessTokenError("Invalid access token type.")

    try:
        UUID(str(claims["sub"]))
        UUID(str(claims["sid"]))
    except (KeyError, ValueError) as exc:
        raise InvalidAccessTokenError("Invalid access-token subject.") from exc

    return claims


def generate_refresh_token() -> str:
    """Generate a high-entropy opaque token; persist only its SHA-256 digest."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> bytes:
    """Return the fixed-length digest expected by the persistence model."""
    return hashlib.sha256(token.encode("utf-8")).digest()
