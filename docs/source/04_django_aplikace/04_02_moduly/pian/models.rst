PIAN modely
===========

Definice modelů.

Třídy
------

.. py:class:: Pian

   Class pro db model pian.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: pristupnost_pom()

   .. py:method:: pristupnost()

   .. py:method:: evaluate_pristupnost_change()

   .. py:method:: get_absolute_url()

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro pian.
      Metoda vráti ident podle sekvence pianu.

   .. py:method:: set_vymezeny()

      Metoda pro nastavení stavu vymezený.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený.

   .. py:method:: zaznamenej_zapsani()

      Metoda pro uložení změny do historie pro pianu.


.. py:class:: Kladyzm

   Class pro db model klady zm.


.. py:class:: PianSekvence

   Class pro db model sekvence pianu podle klady zm 50 a katastru.


Funkce
------

.. py:function:: vytvor_pian(katastr, fedora_transaction)

   Funkce pro vytvoření pianu v DB podle katastru.

.. py:function:: get_ZM_from_point(point)

   Popis není k dispozici.
