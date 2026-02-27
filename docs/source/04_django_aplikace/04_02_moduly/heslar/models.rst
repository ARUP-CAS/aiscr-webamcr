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

      :return: Vrací výsledek provedené operace.

   .. py:method:: podrazena_hesla()

      Provádí operaci podrazena hesla.

      :return: Vrací výsledek provedené operace.

   .. py:method:: nadrazena_hesla()

      Provádí operaci nadrazena hesla.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: HeslarDatace

   Databázový model datace hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: HeslarDokumentTypMaterialRada

   Databázový model vazby typu dokumentu, materiálu a řady.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: HeslarHierarchie

   Databázový model hierarchie hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: HeslarNazev

   Databázový model názvu hesláře.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.


.. py:class:: HeslarOdkaz

   Databázový model odkazu hesláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: RuianKatastr

   Databázový model katastru RÚIAN.

   **Metody:**

   .. py:method:: pian_ident_cely()

      Provádí operaci pian ident cely.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: RuianKraj

   Databázový model kraje RÚIAN.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: RuianOkres

   Databázový model okresu RÚIAN.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: ident_cely()

      Provádí operaci ident cely.

      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

