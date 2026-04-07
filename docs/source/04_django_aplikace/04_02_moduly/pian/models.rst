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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: pristupnost_pom()

      Provádí operaci pristupnost pom.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``first()``, výsledek volání ``get()``.

   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

      :return: Vrací atribut objektu.

   .. py:method:: evaluate_pristupnost_change()

      Provádí operaci evaluate pristupnost change.

      :param added_pristupnost_id: Identifikátor objektu ``added_pristupnost``.
      :param skip_zaznam_id: Identifikátor objektu ``skip_zaznam``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``first()``, výsledek volání ``get()``.

   .. py:method:: __str__()

             Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :param request: Parametr ``request`` předává se do volání ``error()``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_absolute_url()``, výsledek volání ``reverse()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací proměnná ``self``.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``my_list``, n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``our_list``, n-tici.

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního identifikátoru pro PIAN.

      Metoda vrátí identifikátor podle sekvence PIAN.

      :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``sequence.sekvence < maximum``.

   .. py:method:: set_vymezeny()

      Metoda pro nastavení stavu vymezený.

      :param user: Parametr ``user`` se předává do volání ``zaznamenej_zapsani()``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: zaznamenej_zapsani()

      Metoda pro uložení změny do historie pro pianu.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.


.. py:class:: Kladyzm

   Databázový model kladu ZM.


.. py:class:: PianSekvence

   Databázový model sekvence PIAN podle kladu ZM 50 a katastru.


Funkce
------

.. py:function:: vytvor_pian(katastr, fedora_transaction)

   Funkce pro vytvoření pianu v DB podle katastru.

   :param katastr: Parametr ``katastr`` předává se do volání ``get_ZM_from_point()``, pracuje se s atributy ``definicni_bod``, ``hranice``.
   :param fedora_transaction: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``vytvor_pian``.

   :return: Vrací proměnná ``pian``.
   :raises Exception: Vyvolá se s textem "zm10s.not_found"; nebo s textem "zm50s.not_found".
   :raises ObjectDoesNotExist: Vyvolá se při zpracování zachycené výjimky typu ``ObjectDoesNotExist``.

.. py:function:: get_ZM_from_point(point)

   Vrací ZM from point.

   :param point: Parametr ``point`` předává se do volání ``list()``, ``filter()``.

   :return: Vrací n-tici.
