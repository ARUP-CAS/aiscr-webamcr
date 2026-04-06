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

      :param sha1_hash: Parametr ``sha1_hash`` se předává do volání ``encode()``.
      :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
      :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.

          :return: Vrací proměnná ``pass_hash``.

   .. py:method:: encode()

      Provádí operaci encode.

      :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      :param salt: Parametr `salt` používaný při výpočtu hashe hesla.
      :param iterations: Parametr `iterations` používaný při výpočtu hashe hesla.

          :return: Vrací výsledek volání ``encode_sha1_hash()``.

