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

      :param email: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
      :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      :param extra_fields: Kolekce ``extra_fields`` zpracovávaná touto funkcí.

          :return: Vrací proměnná ``user``.
          :raises ValueError: Vyvolá se při splnění podmínky ``not email``.

   .. py:method:: create_superuser()

      Create and save a SuperUser with the given email and password.

      :param email: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
      :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      :param extra_fields: Kolekce ``extra_fields`` zpracovávaná touto funkcí.

          :return: Vrací výsledek volání ``create_user()``.
          :raises ValueError: Vyvolá se při splnění podmínky ``extra_fields.get('is_staff') is not True``; nebo při splnění podmínky ``extra_fields.get('is_superuser') is not True``.

