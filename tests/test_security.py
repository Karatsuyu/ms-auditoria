# =============================================================================
# ms-auditoria | tests/test_security.py
# =============================================================================
# Tests unitarios para el módulo de cifrado AES-256 y hash de tokens.
# =============================================================================

from app.core.security import aes_cipher
from app.core.auth import hash_token


class TestAESCipher:
    """Tests para cifrado y descifrado AES-256-GCM."""

    def test_encrypt_decrypt_roundtrip(self):
        """Cifrar y descifrar retorna el texto original."""
        original = "Datos sensibles de auditoría: usuario admin accedió al módulo"
        encrypted = aes_cipher.encrypt(original)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """El mismo texto produce resultados diferentes por el nonce."""
        text = "Mismo texto"
        encrypted1 = aes_cipher.encrypt(text)
        encrypted2 = aes_cipher.encrypt(text)
        assert encrypted1 != encrypted2

    def test_encrypt_not_plaintext(self):
        """El texto cifrado no contiene el texto plano."""
        text = "Información confidencial"
        encrypted = aes_cipher.encrypt(text)
        assert text not in encrypted

    def test_empty_string(self):
        """Cifrado/descifrado de cadena vacía."""
        encrypted = aes_cipher.encrypt("")
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == ""

    def test_unicode_characters(self):
        """Cifrado/descifrado con caracteres Unicode."""
        text = "Auditoría: acción válida con ñ, ü, é, 中文, 日本語"
        encrypted = aes_cipher.encrypt(text)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == text


class TestTokenHashing:
    """Tests para hash SHA-256 de tokens de aplicación."""

    def test_hash_token_consistent(self):
        """El mismo token siempre produce el mismo hash."""
        token = "dev-token-ms-reservas"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_different_tokens_different_hashes(self):
        """Tokens diferentes producen hashes diferentes."""
        h1 = hash_token("token-1")
        h2 = hash_token("token-2")
        assert h1 != h2

    def test_hash_length(self):
        """SHA-256 produce hash de 64 caracteres hex."""
        h = hash_token("any-token")
        assert len(h) == 64
