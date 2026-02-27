import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    """Třída `PBKDF2WrappedSHA1PasswordHasher` v modulu `webclient.webclient.hashers`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        """Funkce `PBKDF2WrappedSHA1PasswordHasher.encode_sha1_hash` v modulu `webclient.webclient.hashers`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param sha1_hash: Vstupní hodnota používaná při zpracování.
        :param salt: Vstupní hodnota používaná při zpracování.
        :param iterations: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        pass_hash = super().encode(sha1_hash, salt, iterations)
        return pass_hash

    def encode(self, password, salt, iterations=None):
        """Funkce `PBKDF2WrappedSHA1PasswordHasher.encode` v modulu `webclient.webclient.hashers`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param password: Vstupní hodnota používaná při zpracování.
        :param salt: Vstupní hodnota používaná při zpracování.
        :param iterations: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)
