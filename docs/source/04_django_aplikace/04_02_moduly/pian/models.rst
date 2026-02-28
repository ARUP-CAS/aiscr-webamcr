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

      :return: Vrací výsledek provedené operace.

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

      :param user: Popis parametru ``user``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený.

      :param user: Popis parametru ``user``.
      :param old_ident: Popis parametru ``old_ident``.

   .. py:method:: zaznamenej_zapsani()

      Metoda pro uložení změny do historie pro pianu.

      :param user: Popis parametru ``user``.


.. py:class:: Kladyzm

   Databázový model kladu ZM.


.. py:class:: PianSekvence

   Databázový model sekvence PIAN podle kladu ZM 50 a katastru.


Funkce
------

.. py:function:: vytvor_pian(katastr, fedora_transaction)

   Funkce pro vytvoření pianu v DB podle katastru.

   :param katastr: Popis parametru ``katastr``.
   :param fedora_transaction: Popis parametru ``fedora_transaction``.

.. py:function:: get_ZM_from_point(point)

   Vrací ZM from point.

   :param point: Vstupní hodnota ``point`` pro danou operaci.
