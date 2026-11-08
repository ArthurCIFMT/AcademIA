from secrets import token_urlsafe

from pwdlib import PasswordHash


class Passwords:
    def __init__(self) -> None:
        self._codec = PasswordHash.recommended()
        self._dummy_hash = self._codec.hash(token_urlsafe(32))

    def hash(self, value: str) -> str:
        if not 10 <= len(value) <= 128:
            raise ValueError("A senha deve ter de 10 a 128 caracteres.")
        return self._codec.hash(value)

    def verify(self, value: str, stored_hash: str | None) -> bool:
        usable = stored_hash is not None and stored_hash.startswith("$argon2id$")
        verified = self._codec.verify(
            value, stored_hash if usable and stored_hash else self._dummy_hash
        )
        return usable and verified
