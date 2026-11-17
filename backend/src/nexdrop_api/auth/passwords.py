"""Password hashing and verification using Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_password_hasher = PasswordHasher()
_MIN_PASSWORD_LENGTH = 12
_MAX_PASSWORD_BYTES = 1024


def hash_password(password: str) -> str:
    """Hash a password using Argon2id after enforcing basic input bounds."""
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must contain at least {_MIN_PASSWORD_LENGTH} characters.")
    if len(password.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise ValueError("Password is too long.")
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password without exposing malformed-hash details to callers."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_hash_needs_rehash(password_hash: str) -> bool:
    """Return whether a stored password hash should be upgraded."""
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except (VerificationError, InvalidHashError):
        return True
