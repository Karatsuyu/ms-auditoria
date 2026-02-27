# =============================================================================
# ms-auditoria | tests/test_security.py
# =============================================================================
# Tests unitarios para el módulo de cifrado AES-256.
# =============================================================================

from app.core.security import aes_cipher


class TestAESCipher:
    """Tests para cifrado y descifrado AES-256-GCM."""

    def test_encrypt_decrypt_roundtrip(self):
        """Verifica que cifrar y descifrar retorna el texto original."""
        original = "Datos sensibles de auditoría: usuario admin accedió al módulo financiero"
        encrypted = aes_cipher.encrypt(original)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """Verifica que cifrar el mismo texto produce resultados diferentes (por el nonce)."""
        text = "Mismo texto"
        encrypted1 = aes_cipher.encrypt(text)
        encrypted2 = aes_cipher.encrypt(text)
        assert encrypted1 != encrypted2  # Nonce diferente cada vez

    def test_encrypt_not_plaintext(self):
        """Verifica que el texto cifrado no contiene el texto plano."""
        text = "Información confidencial"
        encrypted = aes_cipher.encrypt(text)
        assert text not in encrypted

    def test_empty_string(self):
        """Verifica cifrado/descifrado de cadena vacía."""
        encrypted = aes_cipher.encrypt("")
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == ""

    def test_unicode_characters(self):
        """Verifica cifrado/descifrado con caracteres Unicode."""
        text = "Auditoría: acción válida con ñ, ü, é, 中文, 日本語"
        encrypted = aes_cipher.encrypt(text)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == text
