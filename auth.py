
import base64
import hashlib
import hmac
import secrets


ITERATIONS = 600_000


def hash_password(password):
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    hash_text = base64.urlsafe_b64encode(
        password_hash
    ).decode("ascii")

    return (
        f"pbkdf2_sha256${ITERATIONS}$"
        f"{salt_text}${hash_text}"
    )


def verify_password(password, stored_hash):
    try:
        algorithm, iterations_text, salt_text, hash_text = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)

        # Reject malformed or unexpectedly expensive parameters.
        if not 100_000 <= iterations <= 2_000_000:
            return False

        salt = base64.urlsafe_b64decode(salt_text)
        expected_hash = base64.urlsafe_b64decode(hash_text)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            calculated_hash, expected_hash
        )

    except (ValueError, TypeError, AttributeError):
        return False
