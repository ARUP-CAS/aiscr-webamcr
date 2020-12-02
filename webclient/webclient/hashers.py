import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        pass_hash = super().encode(sha1_hash, salt, iterations)
        return pass_hash

    def encode(self, password, salt, iterations=None):
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
