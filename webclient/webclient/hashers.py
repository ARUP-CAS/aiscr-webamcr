import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    """Implementuje komponentu ``PBKDF2WrappedSHA1PasswordHasher`` v rámci aplikace."""

    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        """
        Provádí operaci encode sha1 hash.

        :param sha1_hash: Číselná nebo geometrická hodnota `sha1_hash` použitá při výpočtu nebo transformaci.
        :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
        :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.
        """
        pass_hash = super().encode(sha1_hash, salt, iterations)
        return pass_hash

    def encode(self, password, salt, iterations=None):
        """
        Provádí operaci encode.

        :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
        :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
        :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.
        """
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
