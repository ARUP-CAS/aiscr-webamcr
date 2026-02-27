import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    """Implementuje komponentu ``PBKDF2WrappedSHA1PasswordHasher`` v rámci aplikace."""
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        """Provádí operaci encode sha1 hash.
        
        :param sha1_hash: Vstupní hodnota ``sha1_hash`` pro danou operaci.
        :param salt: Vstupní hodnota ``salt`` pro danou operaci.
        :param iterations: Vstupní hodnota ``iterations`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        pass_hash = super().encode(sha1_hash, salt, iterations)
        return pass_hash

    def encode(self, password, salt, iterations=None):
        """Provádí operaci encode.
        
        :param password: Vstupní hodnota ``password`` pro danou operaci.
        :param salt: Vstupní hodnota ``salt`` pro danou operaci.
        :param iterations: Vstupní hodnota ``iterations`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
