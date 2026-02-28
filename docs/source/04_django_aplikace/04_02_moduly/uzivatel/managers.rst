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

      :param email: Hodnota parametru ``email`` použitého touto operací.
      :param password: Hodnota parametru ``password`` použitého touto operací.
      :param extra_fields: Hodnota parametru ``extra_fields`` použitého touto operací.

   .. py:method:: create_superuser()

      Create and save a SuperUser with the given email and password.

      :param email: Hodnota parametru ``email`` použitého touto operací.
      :param password: Hodnota parametru ``password`` použitého touto operací.
      :param extra_fields: Hodnota parametru ``extra_fields`` použitého touto operací.

