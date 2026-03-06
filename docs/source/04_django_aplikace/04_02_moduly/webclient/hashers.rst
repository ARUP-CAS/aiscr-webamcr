WEBCLIENT hashers
=================

Modul hashers.

Třídy
------

.. py:class:: PBKDF2WrappedSHA1PasswordHasher

   Implementuje komponentu ``PBKDF2WrappedSHA1PasswordHasher`` v rámci aplikace.

   **Metody:**

   .. py:method:: encode_sha1_hash()

      Provádí operaci encode sha1 hash.

      :param sha1_hash: Číselná nebo geometrická hodnota `sha1_hash` použitá při výpočtu nebo transformaci.
      :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
      :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.

   .. py:method:: encode()

      Provádí operaci encode.

      :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
      :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.

