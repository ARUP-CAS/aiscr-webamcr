PIAN modely
===========

Definice modelů.

Třídy
------

.. py:class:: Pian

   Databázový model PIAN.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: pristupnost_pom()

      Provádí operaci pristupnost pom.

   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

   .. py:method:: evaluate_pristupnost_change()

      Provádí operaci evaluate pristupnost change.

      :param added_pristupnost_id: Identifikátor objektu ``added_pristupnost``.
      :param skip_zaznam_id: Identifikátor objektu ``skip_zaznam``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního identifikátoru pro PIAN.

      Metoda vrátí identifikátor podle sekvence PIAN.

   .. py:method:: set_vymezeny()

      Metoda pro nastavení stavu vymezený.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: zaznamenej_zapsani()

      Metoda pro uložení změny do historie pro pianu.

      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: Kladyzm

   Databázový model kladu ZM.


.. py:class:: PianSekvence

   Databázový model sekvence PIAN podle kladu ZM 50 a katastru.


Funkce
------

.. py:function:: vytvor_pian(katastr, fedora_transaction)

   Funkce pro vytvoření pianu v DB podle katastru.

   :param katastr: Doménový objekt `katastr`, se kterým funkce pracuje.
   :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.

.. py:function:: get_ZM_from_point(point)

   Vrací ZM from point.

   :param point: Doménový objekt `point`, se kterým funkce pracuje.
