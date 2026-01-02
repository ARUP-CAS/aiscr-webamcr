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

   .. py:method:: create_superuser()

      Create and save a SuperUser with the given email and password.
