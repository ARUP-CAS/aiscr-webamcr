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

      :param sha1_hash: Vstupní hodnota ``sha1_hash`` pro danou operaci.
      :param salt: Vstupní hodnota ``salt`` pro danou operaci.
      :param iterations: Vstupní hodnota ``iterations`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: encode()

      Provádí operaci encode.

      :param password: Vstupní hodnota ``password`` pro danou operaci.
      :param salt: Vstupní hodnota ``salt`` pro danou operaci.
      :param iterations: Vstupní hodnota ``iterations`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

