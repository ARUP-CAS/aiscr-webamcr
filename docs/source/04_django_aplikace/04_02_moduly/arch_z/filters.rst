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

   .. py:method:: decompress()

      Provádí operaci decompress.

      :param value: Vstupní hodnota ``value`` pro danou operaci.


.. py:class:: NumberRangeField

   Implementuje komponentu ``NumberRangeField`` v rámci aplikace.


.. py:class:: NumberRangeFilter

   Implementuje komponentu ``NumberRangeFilter`` v rámci aplikace.


.. py:class:: ArchZaznamFilter

   Třída pro zakladní filtrování archeologických záznamů a jejich potomků.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle hlavního i vedlejšího katastru.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle hlavního i vedlejšího kraje.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle hlavního i vedlejšího okresu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_dj_zjisteni()

      Metoda pro filtrování podle dj_zjisteni.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu predmětu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AkceFilter

   Class pro filtrování akce.

   **Metody:**

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_vedouci()

      Metoda pro filtrování podle hlavního a vedlejšiho vedoucího akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, upřesnení, uložení, označení akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_zahrnout_projektove()

      Metoda pro filtrování mezi projektovými a samostatnými akcemi.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle toho či akce má pozitivní DJ.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_adb_popisne_udaje()

      Metoda pro filtrování podle popisných údajů ADB.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_adb_autori()

      Metoda pro filtrování podle autorů revize a popisu ADB.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_adb_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_by_z_range()

      Filtruje by z range.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AkceFilterFormHelper

   Class pro form helper pro zobrazení formuláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

