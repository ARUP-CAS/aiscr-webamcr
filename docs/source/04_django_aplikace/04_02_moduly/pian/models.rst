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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: pristupnost_pom()

      Provádí operaci pristupnost pom.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``first()``, výsledek volání ``get()``.


   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: evaluate_pristupnost_change()

      Provádí operaci evaluate pristupnost change.

      **Parametry:**

      - ``added_pristupnost_id``: Identifikátor objektu ``added_pristupnost``.
      - ``skip_zaznam_id``: Identifikátor objektu ``skip_zaznam``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``first()``, výsledek volání ``get()``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: get_absolute_url()

      Vrací absolute url.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``error()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_absolute_url()``, výsledek volání ``reverse()``.


   .. py:method:: get_permission_object()

      Vrací permission object.

      **Návratová hodnota:**

      Vrací proměnná ``self``.


   .. py:method:: get_create_user()

      Vrací create user.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``my_list``, n-tici.


   .. py:method:: get_create_org()

      Vrací create org.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``our_list``, n-tici.


   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního identifikátoru pro PIAN.

      Metoda vrátí identifikátor podle sekvence PIAN.

      **Výjimky:**

      - ``MaximalIdentNumberError``: Vyvolá se při splnění podmínky ``sequence.sekvence < maximum``.


   .. py:method:: set_vymezeny()

      Metoda pro nastavení stavu vymezený.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``zaznamenej_zapsani()``.


   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzený.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``old_ident``: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.


   .. py:method:: zaznamenej_zapsani()

      Metoda pro uložení změny do historie pro pianu.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.



.. py:class:: Kladyzm

   Databázový model kladu ZM.


.. py:class:: PianSekvence

   Databázový model sekvence PIAN podle kladu ZM 50 a katastru.


Funkce
------

.. py:function:: vytvor_pian(katastr, fedora_transaction)

   Funkce pro vytvoření pianu v DB podle katastru.

   **Parametry:**

   - ``katastr``: Parametr ``katastr`` předává se do volání ``get_ZM_from_point()``, pracuje se s atributy ``definicni_bod``, ``hranice``.
   - ``fedora_transaction``: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``vytvor_pian``.

   **Návratová hodnota:**

   Vrací proměnná ``pian``.

   **Výjimky:**

   - ``Exception``: Vyvolá se s textem "zm10s.not_found"; nebo s textem "zm50s.not_found".
   - ``ObjectDoesNotExist``: Vyvolá se při zpracování zachycené výjimky typu ``ObjectDoesNotExist``.


.. py:function:: get_ZM_from_point(point)

   Vrací ZM from point.

   **Parametry:**

   - ``point``: Parametr ``point`` předává se do volání ``list()``, ``filter()``.

   **Návratová hodnota:**

   Vrací n-tici.

