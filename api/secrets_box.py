"""
Cifra e decifra segredos dos usuários (a chave da API da Anthropic) com Fernet.

A chave do servidor vem de APP_ENCRYPTION_KEY; sem ela, é gerada uma vez e
guardada em api/.app_key (fora do git, permissão 600). Perder esse arquivo
não quebra nada além das chaves já salvas: cada pessoa só precisa colar a
sua de novo nas Configurações.
"""

import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from config import settings

KEY_FILE = Path(__file__).resolve().parent / ".app_key"


class SecretUnreadable(Exception):
    """O segredo foi cifrado com outra chave do servidor (ou está corrompido)."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = settings.app_encryption_key.strip()
    if not key:
        if KEY_FILE.exists():
            key = KEY_FILE.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            # Cria já com permissão 600 (sem janela em que outros usuários leem)
            fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(key + "\n")
    return Fernet(key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise SecretUnreadable from exc
