UZIVATEL managers
=================

Definice manažerů.

Třídy
------

.. py:class:: CustomUserManager

   Custom user model manager where email is the unique identifiers

   for authentication instead of usernames.
   https://testdriven.io/blog/django-custom-user-model/

   **Metody:**

   .. py:method:: create_user()

      Create and save a User with the given email and password.

      **Parametry:**

      - ``email``: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
      - ``password``: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      - ``extra_fields``: Kolekce ``extra_fields`` zpracovávaná touto funkcí.

      **Návratová hodnota:**

      Vrací proměnná ``user``.

      **Výjimky:**

      - ``ValueError``: Vyvolá se při splnění podmínky ``not email``.


   .. py:method:: create_superuser()

      Create and save a SuperUser with the given email and password.

      **Parametry:**

      - ``email``: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
      - ``password``: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      - ``extra_fields``: Kolekce ``extra_fields`` zpracovávaná touto funkcí.

      **Návratová hodnota:**

      Vrací výsledek volání ``create_user()``.

      **Výjimky:**

      - ``ValueError``: Vyvolá se při splnění podmínky ``extra_fields.get('is_staff') is not True``; nebo při splnění podmínky ``extra_fields.get('is_superuser') is not True``.


