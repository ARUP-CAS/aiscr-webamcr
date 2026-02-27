ARCH_Z filtry
=============

Definice filtrů.

Třídy
------

.. py:class:: NumberRangeWidget

   Implementuje komponentu ``NumberRangeWidget`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param attrs: Vstupní hodnota ``attrs`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: decompress()

      Provádí operaci decompress.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: NumberRangeField

   Implementuje komponentu ``NumberRangeField`` v rámci aplikace.


.. py:class:: NumberRangeFilter

   Implementuje komponentu ``NumberRangeFilter`` v rámci aplikace.


.. py:class:: ArchZaznamFilter

   Třída pro zakladní filtrování archeologických záznamů a jejich potomků.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle hlavního i vedlejšího katastru.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle hlavního i vedlejšího kraje.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle hlavního i vedlejšího okresu.

   .. py:method:: filter_dj_zjisteni()

      Metoda pro filtrování podle dj_zjisteni.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu predmětu.

   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AkceFilter

   Class pro filtrování akce.

   **Metody:**

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

   .. py:method:: filtr_vedouci()

      Metoda pro filtrování podle hlavního a vedlejšiho vedoucího akce.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, upřesnení, uložení, označení akce.

   .. py:method:: filtr_zahrnout_projektove()

      Metoda pro filtrování mezi projektovými a samostatnými akcemi.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle toho či akce má pozitivní DJ.

   .. py:method:: filter_adb_popisne_udaje()

      Metoda pro filtrování podle popisných údajů ADB.

   .. py:method:: filtr_adb_autori()

      Metoda pro filtrování podle autorů revize a popisu ADB.

   .. py:method:: filter_adb_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

   .. py:method:: filter_by_z_range()

      Filtruje by z range.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AkceFilterFormHelper

   Class pro form helper pro zobrazení formuláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

