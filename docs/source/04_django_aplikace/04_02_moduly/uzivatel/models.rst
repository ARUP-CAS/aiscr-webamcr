UZIVATEL modely
===============

Definice modelů.

Třídy
------

.. py:class:: User

   Databázový model uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: hlavni_role()

      Provádí operaci hlavni role.

      :return: Vrací výsledek provedené operace.

   .. py:method:: user_str()

      Provádí operaci user str.

      :return: Vrací výsledek provedené operace.

   .. py:method:: user_str_en()

      Provádí operaci user str en.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: display_name()

      Textová reprezentace uživatele pro tabulky a autocomplete pole.

   .. py:method:: moje_spolupracujici_organizace()

      Provádí operaci moje spolupracujici organizace.

      :return: Vrací výsledek provedené operace.

   .. py:method:: moje_stavy_pruzkumnych_projektu()

      Provádí operaci moje stavy pruzkumnych projektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: email_user()

      Provádí operaci email user.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: name_and_id()

      Vrátí jméno uživatele včetně jeho plného identifikátoru.

   .. py:method:: is_archiver_or_more()

      Určí, zda archiver or more.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: is_archeolog_or_more()

      Určí, zda archeolog or more.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: metadata()

      Provádí operaci metadata.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save_metadata()

      Uloží metadata.

      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: record_deletion()

      Zaznamená smazání uživatele v repozitáři a uzavře transakci dle potřeby.

   .. py:method:: can_see_users_details()

      Provádí operaci can see users details.

      :return: Vrací výsledek provedené operace.

   .. py:method:: full_details()

      Provádí operaci full details.

      :return: Vrací výsledek provedené operace.

   .. py:method:: anonymous_details()

      Provádí operaci anonymous details.

      :return: Vrací výsledek provedené operace.

   .. py:method:: can_see_ours_item()

      Provádí operaci can see ours item.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: UzivatelPrihlaseniLog

   Implementuje komponentu ``UzivatelPrihlaseniLog`` v rámci aplikace.


.. py:class:: Organizace

   Databázový model organizace.

   **Metody:**

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_nazev()

      Vrací nazev.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: Osoba

   Databázový model osoby.

   **Metody:**

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: UserNotificationType

   Databázový model typu uživatelské notifikace.

   **Metody:**

   .. py:method:: _get_settings_dict()

      Vrací settings dict.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: zasilat_neaktivnim()

      Provádí operaci zasilat neaktivnim.

      :return: Vrací výsledek provedené operace.

   .. py:method:: predmet()

      Provádí operaci predmet.

      :return: Vrací výsledek provedené operace.

   .. py:method:: cesta_sablony()

      Provádí operaci cesta sablony.

      :return: Vrací výsledek provedené operace.

   .. py:method:: is_groups()

      Určí, zda groups.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: NotificationsLog

   Databázový model logu notifikací.


Funkce
------

.. py:function:: only_notification_groups()

   Provádí operaci only notification groups.

   :return: Vrací výsledek provedené operace.

.. py:function:: get_default_licence()

   Vrací default licence.

   :return: Vrací načtená data odpovídající vstupním parametrům.
