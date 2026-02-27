import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    """Zapouzdřuje chování třídy ``PBKDF2WrappedSHA1PasswordHasher`` pro modul ``webclient.webclient.hashers``."""
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        """Zajišťuje logiku funkce ``encode_sha1_hash``.
        
        :param sha1_hash: Vstupní hodnota parametru ``sha1_hash`` použitého při zpracování.
        :param salt: Vstupní hodnota parametru ``salt`` použitého při zpracování.
        :param iterations: Vstupní hodnota parametru ``iterations`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        pass_hash = super().encode(sha1_hash, salt, iterations)
        return pass_hash

    def encode(self, password, salt, iterations=None):
        """Zajišťuje logiku funkce ``encode``.
        
        :param password: Vstupní hodnota parametru ``password`` použitého při zpracování.
        :param salt: Vstupní hodnota parametru ``salt`` použitého při zpracování.
        :param iterations: Vstupní hodnota parametru ``iterations`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
