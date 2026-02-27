# =============================================================================
# ms-auditoria | core/security.py
# =============================================================================
# Módulo de cifrado AES-256 para datos sensibles de auditoría.
# Utiliza AES en modo GCM para cifrado autenticado.
# =============================================================================

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


class AESCipher:
    """Cifrado AES-256-GCM para proteger datos sensibles."""

    def __init__(self) -> None:
        self._key = bytes.fromhex(settings.AES_SECRET_KEY)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        """
        Cifra un texto plano y retorna Base64(nonce + ciphertext).
        El nonce de 12 bytes se antepone al ciphertext para poder descifrarlo.
        """
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted_b64: str) -> str:
        """
        Descifra un texto cifrado en Base64(nonce + ciphertext).
        """
        raw = base64.b64decode(encrypted_b64)
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")


# Singleton para reutilizar en toda la aplicación
aes_cipher = AESCipher()
