import os
from cryptography.fernet import Fernet, InvalidToken
from app.services.errors import NeedsInput


def cipher():
    try:
        return Fernet(os.environ["OAUTH_ENCRYPTION_KEY"].encode())
    except (KeyError, ValueError):
        raise NeedsInput("Configure a valid local OAUTH_ENCRYPTION_KEY before connecting Google.") from None


def encrypt(value: str):
    return cipher().encrypt(value.encode()).decode()


def decrypt(value: str):
    try:
        return cipher().decrypt(value.encode()).decode()
    except InvalidToken:
        raise NeedsInput("Stored OAuth data cannot be decrypted with the current key. Restore the original encryption key.") from None
