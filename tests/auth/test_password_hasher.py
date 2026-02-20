"""
Tests for Password Hasher (Argon2id)
"""


class TestPasswordHasher:
    """Test Argon2id password hashing"""

    def test_hash_password(self):
        """Test hashing a password"""
        from auth.password_hasher import PasswordHasher

        hasher = PasswordHasher()
        password = "SecurePassword123!"

        hash_value = hasher.hash(password)

        assert hash_value is not None
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_verify_correct_password(self):
        """Test verifying correct password"""
        from auth.password_hasher import PasswordHasher

        hasher = PasswordHasher()
        password = "SecurePassword123!"
        hash_value = hasher.hash(password)

        is_valid = hasher.verify(password, hash_value)

        assert is_valid is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password"""
        from auth.password_hasher import PasswordHasher

        hasher = PasswordHasher()
        password = "SecurePassword123!"
        hash_value = hasher.hash(password)

        is_valid = hasher.verify("WrongPassword", hash_value)

        assert is_valid is False

    def test_needs_rehash(self):
        """Test checking if rehash is needed"""
        from auth.password_hasher import PasswordHasher

        hasher = PasswordHasher()
        password = "SecurePassword123!"
        hash_value = hasher.hash(password)

        # Fresh hash should not need rehash
        needs_rehash = hasher.needs_rehash(hash_value)

        assert needs_rehash is False

    def test_hash_is_different_each_time(self):
        """Test that same password produces different hashes"""
        from auth.password_hasher import PasswordHasher

        hasher = PasswordHasher()
        password = "SecurePassword123!"

        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)

        assert hash1 != hash2  # Salts should be different
        assert hasher.verify(password, hash1) is True
        assert hasher.verify(password, hash2) is True
