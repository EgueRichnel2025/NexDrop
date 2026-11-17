"""Unit tests for authentication security primitives."""

from datetime import timedelta
from uuid import uuid4

import pytest

from nexdrop_api.auth.passwords import (
    hash_password,
    password_hash_needs_rehash,
    verify_password,
)
from nexdrop_api.auth.tokens import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


def test_argon2id_password_hash_round_trip() -> None:
    password = "NexDrop-Secure-Passphrase-2026"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)
    assert not password_hash_needs_rehash(password_hash)


def test_password_policy_rejects_short_password() -> None:
    with pytest.raises(ValueError, match="at least 12"):
        hash_password("too-short")


def test_password_policy_rejects_excessive_utf8_size() -> None:
    with pytest.raises(ValueError, match="too long"):
        hash_password("é" * 600)


def test_password_verification_handles_invalid_hash() -> None:
    assert not verify_password("anything", "not-an-argon-hash")


def test_access_token_round_trip_and_claims() -> None:
    user_id = uuid4()
    session_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        session_id=session_id,
        secret="x" * 48,
        issuer="https://api.nexdrop.local",
        audience="nexdrop-client",
    )

    claims = decode_access_token(
        token,
        secret="x" * 48,
        issuer="https://api.nexdrop.local",
        audience="nexdrop-client",
    )

    assert claims["sub"] == str(user_id)
    assert claims["sid"] == str(session_id)
    assert claims["typ"] == "access"


def test_access_token_rejects_wrong_secret_and_audience() -> None:
    token = create_access_token(
        user_id=uuid4(),
        session_id=uuid4(),
        secret="x" * 48,
        issuer="nexdrop",
        audience="desktop",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, secret="y" * 48, issuer="nexdrop", audience="desktop")
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, secret="x" * 48, issuer="nexdrop", audience="other")


def test_access_token_requires_strong_secret() -> None:
    with pytest.raises(ValueError, match="at least 32"):
        create_access_token(
            user_id=uuid4(),
            session_id=uuid4(),
            secret="short",
            issuer="nexdrop",
            audience="desktop",
        )


def test_access_token_rejects_non_positive_lifetime() -> None:
    with pytest.raises(ValueError, match="positive"):
        create_access_token(
            user_id=uuid4(),
            session_id=uuid4(),
            secret="x" * 48,
            issuer="nexdrop",
            audience="desktop",
            lifetime=timedelta(0),
        )


def test_refresh_token_is_random_and_stored_as_digest() -> None:
    first = generate_refresh_token()
    second = generate_refresh_token()

    assert first != second
    assert len(first) >= 60
    assert len(hash_refresh_token(first)) == 32
    assert hash_refresh_token(first) != hash_refresh_token(second)
