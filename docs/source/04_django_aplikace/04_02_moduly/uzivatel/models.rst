UZIVATEL modely
===============

Definice modelů.

Třídy
------

.. py:class:: User

   Class pro db model user.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: hlavni_role()

   .. py:method:: user_str()

   .. py:method:: user_str_en()

   .. py:method:: __str__()

   .. py:method:: display_name()

      Textová reprezentace uživatele pro tabulky a autocomplete pole.

   .. py:method:: moje_spolupracujici_organizace()

   .. py:method:: moje_stavy_pruzkumnych_projektu()

   .. py:method:: email_user()

   .. py:method:: name_and_id()

   .. py:method:: is_archiver_or_more()

   .. py:method:: is_archeolog_or_more()

   .. py:method:: save()

      save metoda pro přidělení identu celý.

   .. py:method:: metadata()

   .. py:method:: save_metadata()

   .. py:method:: record_deletion()

   .. py:method:: can_see_users_details()

   .. py:method:: full_details()

   .. py:method:: anonymous_details()

   .. py:method:: can_see_ours_item()

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()


.. py:class:: UzivatelPrihlaseniLog

   Popis není k dispozici.


.. py:class:: Organizace

   Class pro db model organizace.

   **Metody:**

   .. py:method:: save()

      save metoda pro přidělení identu celý.

   .. py:method:: __str__()

   .. py:method:: get_nazev()


.. py:class:: Osoba

   Class pro db model osoba.

   **Metody:**

   .. py:method:: save()

      save metoda pro přidělení identu celý.

   .. py:method:: __str__()


.. py:class:: UserNotificationType

   Class pro db model typ user notifikace.

   **Metody:**

   .. py:method:: _get_settings_dict()

   .. py:method:: zasilat_neaktivnim()

   .. py:method:: predmet()

   .. py:method:: cesta_sablony()

   .. py:method:: is_groups()

   .. py:method:: __str__()


.. py:class:: NotificationsLog

   Class pro db model logu notifikací.


Funkce
------

.. py:function:: only_notification_groups()

   Popis není k dispozici.

.. py:function:: get_default_licence()

   Popis není k dispozici.
