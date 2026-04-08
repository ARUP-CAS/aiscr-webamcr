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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: hlavni_role()

             Provádí operaci hlavni role.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: user_str()

      Provádí operaci user str.

      :return: Vrací proměnná ``retezec``.

   .. py:method:: user_str_en()

      Provádí operaci user str en.

      :return: Vrací proměnná ``retezec``.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: display_name()

      Textová reprezentace uživatele pro tabulky a autocomplete pole.

      :param viewer: Uživatel nebo osoba ``viewer``, v jejímž kontextu se operace provádí.

      :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``base``.

   .. py:method:: moje_spolupracujici_organizace()

      Provádí operaci moje spolupracujici organizace.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``moje_spolupracujici_organizace``, výsledek volání ``all()``.

   .. py:method:: moje_stavy_pruzkumnych_projektu()

      Provádí operaci moje stavy pruzkumnych projektu.

      :return: Vrací n-tici.

   .. py:method:: email_user()

      Provádí operaci email user.

      :param args: Parametr ``args`` se předává do volání ``send_mail()``, ``format()``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``email_user``.

   .. py:method:: name_and_id()

      Vrátí jméno uživatele včetně jeho plného identifikátoru.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: is_archiver_or_more()

      Určí, zda archiver or more.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: is_archeolog_or_more()

      Určí, zda archeolog or more.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

   .. py:method:: metadata()

      Provádí operaci metadata.

      :return: Vrací výsledek volání ``get_metadata()``.

   .. py:method:: save_metadata()

      Uloží metadata uživatele do Fedora repozitáře a případně uzavře transakci.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``isinstance()``, ``debug()``, pracuje se s atributy ``uid``, ``add_updated_ident_cely``, ovlivňuje větvení podmínek.
      :param close_transaction: Parametr ``close_transaction`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata``.

   .. py:method:: record_deletion()

      Zaznamená smazání uživatele v repozitáři a uzavře transakci dle potřeby.

      :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``isinstance()``, ``FedoraRepositoryConnector()``, pracuje se s atributy ``mark_transaction_as_closed``, ovlivňuje větvení podmínek.
      :param close_transaction: Parametr ``close_transaction`` ovlivňuje větvení podmínek.

      :raises ValueError: Vyvolá se s textem "No Fedora transaction"; nebo s textem "fedora_transaction must be a FedoraTransaction class object".

   .. py:method:: can_see_users_details()

      Provádí operaci can see users details.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: full_details()

      Provádí operaci full details.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: anonymous_details()

      Provádí operaci anonymous details.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: can_see_ours_item()

      Provádí operaci can see ours item.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací proměnná ``self``.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací n-tici.


.. py:class:: UzivatelPrihlaseniLog

   Implementuje komponentu ``UzivatelPrihlaseniLog`` v rámci aplikace.


.. py:class:: Organizace

   Databázový model organizace.

   **Metody:**

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'organizace')``.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: get_nazev()

      Vrací název organizace ve formátu používaném v aplikaci.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.


.. py:class:: Osoba

   Databázový model osoby.

   **Metody:**

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'osoba')``.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.


.. py:class:: UserNotificationType

   Databázový model typu uživatelské notifikace.

   **Metody:**

   .. py:method:: _get_settings_dict()

      Vrací settings dict.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: zasilat_neaktivnim()

             Provádí operaci zasilat neaktivnim.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: predmet()

             Provádí operaci predmet.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: cesta_sablony()

             Provádí operaci cesta sablony.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: is_groups()

      Určí, zda groups.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``str()``, atribut objektu.


.. py:class:: NotificationsLog

   Databázový model logu notifikací.


Funkce
------

.. py:function:: only_notification_groups()

   Provádí operaci only notification groups.

   :return: Vrací výsledek volání ``all()``.

.. py:function:: get_default_licence()

   Vrací default licence.

   :return: Vrací proměnná ``DOKUMENT_LICENCE_NEZNAMA``.
