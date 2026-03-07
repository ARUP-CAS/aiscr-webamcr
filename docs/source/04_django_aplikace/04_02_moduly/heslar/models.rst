HESLAR modely
=============

Definice modelů.

Třídy
------

.. py:class:: Heslar

   Databázový model hesláře.

   **Metody:**

   .. py:method:: dokument_typ_material_rada()

      Provádí operaci dokument typ material rada.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: podrazena_hesla()

      Provádí operaci podrazena hesla.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: nadrazena_hesla()

      Provádí operaci nadrazena hesla.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``self._state.adding and (not FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'heslar'))``.


.. py:class:: HeslarDatace

   Databázový model datace hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: HeslarDokumentTypMaterialRada

   Databázový model vazby typu dokumentu, materiálu a řady.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: HeslarHierarchie

   Databázový model hierarchie hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: HeslarNazev

   Databázový model názvu hesláře.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.


.. py:class:: HeslarOdkaz

   Databázový model odkazu hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: RuianKatastr

   Databázový model katastru RÚIAN.

   **Metody:**

   .. py:method:: pian_ident_cely()

      Provádí operaci pian ident cely.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'ruian_katastr')``.


.. py:class:: RuianKraj

   Databázový model kraje RÚIAN.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'ruian_kraj')``.


.. py:class:: RuianOkres

   Databázový model okresu RÚIAN.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací atribut objektu.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

      :raises ValidationError: Vyvolá se při splnění podmínky ``not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'ruian_okres')``.

