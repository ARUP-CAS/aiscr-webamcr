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

   .. py:method:: create_superuser()

      Create and save a SuperUser with the given email and password.

      :param email: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
      :param password: Heslo ``password`` používané při vytváření nebo aktualizaci účtu.
      :param extra_fields: Kolekce ``extra_fields`` zpracovávaná touto funkcí.

