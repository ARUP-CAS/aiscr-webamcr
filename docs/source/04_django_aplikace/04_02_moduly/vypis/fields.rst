VYPIS fields
============

Modul fields.

Třídy
------

.. py:class:: SimpleSectionTemplateName

   Implementuje komponentu ``SimpleSectionTemplateName`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` slouží jako vstup pro logiku funkce ``__init__``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` slouží jako vstup pro logiku funkce ``get_name``.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` slouží jako vstup pro logiku funkce ``get_permission``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.



.. py:class:: SectionNameWithAccessor

   Implementuje komponentu ``SectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``__init__()``.
      - ``accessor``: Parametr ``accessor`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.


   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, None.



.. py:class:: PianSectionNameWithAccessor

   Implementuje komponentu ``PianSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, None.



.. py:class:: OznamovatelSectionNameWithAccessor

   Implementuje komponentu ``OznamovatelSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_show_oznamovatel()``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` se předává do volání ``get_show_oznamovatel()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_show_oznamovatel()``.



.. py:class:: Field

   Implementuje komponentu ``Field`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``label``: Textový název nebo klíč ``label`` používaný v rámci operace.
      - ``accessor``: Parametr ``accessor`` slouží jako vstup pro logiku funkce ``__init__``.


   .. py:method:: __repr__()

      Vrací reprezentaci objektu pro ladění.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``strftime()``, hodnotu podle větve zpracování, výsledek volání ``getattr()``.


   .. py:method:: get_label()

      Vrací label. v aplikaci.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: SouborField

   Implementuje komponentu ``SouborField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``label``: Textový název nebo klíč ``label`` používaný v rámci operace.
      - ``accessor``: Parametr ``accessor`` se předává do volání ``__init__()``.
      - ``key_name``: Textový název nebo klíč ``key_name`` používaný v rámci operace.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ``reverse()``, pracuje se s atributy ``vazba``, ``id``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``reverse()``, None.



.. py:class:: SouborDownloadField

   Implementuje komponentu ``SouborDownloadField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ``reverse()``, pracuje se s atributy ``vazba``, ``id``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: slovník, None.



.. py:class:: Model3dKomponentaField

   Implementuje komponentu ``Model3dKomponentaField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, pracuje se s atributy ``casti``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací výsledek volání ``getattr()``.



.. py:class:: Model3dKomponentaAktivityField

   Implementuje komponentu ``Model3dKomponentaAktivityField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_value()``.
      - ``user``: Parametr ``user`` se předává do volání ``get_value()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.



.. py:class:: ChooseField

   Implementuje komponentu ``ChooseField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``mark_safe()``, None.



.. py:class:: StatusField

   Implementuje komponentu ``StatusField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací výsledek volání funkce.



.. py:class:: ZjisteniField

   Implementuje komponentu ``ZjisteniField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``_()``, výsledek volání funkce.



.. py:class:: ForeignField

   Implementuje komponentu ``ForeignField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``__init__()``.
      - ``accessor``: Parametr ``accessor`` se předává do volání ``__init__()``.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací výsledek volání ``mark_safe()``.



.. py:class:: GeomGmlField

   Implementuje komponentu ``GeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_gml()``, None.



.. py:class:: GeomWktField

   Implementuje komponentu ``GeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_wkt()``, None.



.. py:class:: ForeignGeomGmlField

   Implementuje komponentu ``ForeignGeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_gml()``, None.



.. py:class:: ForeignGeomWktField

   Implementuje komponentu ``ForeignGeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_wkt()``, None.



.. py:class:: ManyToManyField

   Implementuje komponentu ``ManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.



.. py:class:: ForeignManyToManyField

   Implementuje komponentu ``ForeignManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.



.. py:class:: DoubleField

   Implementuje komponentu ``DoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.



.. py:class:: DoubleFieldNum

   Implementuje komponentu ``DoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.



.. py:class:: ForeignDoubleField

   Implementuje komponentu ``ForeignDoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.



.. py:class:: ForeignDoubleFieldNum

   Implementuje komponentu ``ForeignDoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.



.. py:class:: RepeatableField

   Implementuje komponentu ``RepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``__init__()``.
      - ``accessor``: Parametr ``accessor`` se předává do volání ``__init__()``.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      - ``template_name``: Parametr ``template_name`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``model_name``: Název modelu používaný pro cílení operace.


   .. py:method:: get_related_manager()

      Vrací related manager.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, pracuje se s atributy ``_meta``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_related_manager()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``data``, None.



.. py:class:: VbRepeatableField

   Implementuje komponentu ``VbRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_related_manager()``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``data``, None.



.. py:class:: HistorieRepeatableField

   Implementuje komponentu ``HistorieRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_related_manager()

      Vrací related manager.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, pracuje se s atributy ``historie``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get_related_manager()``.
      - ``user``: Parametr ``user`` se předává do volání ``uzivatel_protected()``, pracuje se s atributy ``hlavni_role``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``data``, None.



.. py:class:: RepeatableSectionField

   Implementuje komponentu ``RepeatableSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_label()

      Vrací label. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_label()``.


   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, pracuje se s atributy ``_meta``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``related_manager``, None.


   .. py:method:: get_value()

      Vrací value. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, pracuje se s atributy ``_meta``.
      - ``user``: Parametr ``user`` slouží jako vstup pro logiku funkce ``get_value``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``data``, None.



.. py:class:: SectionField

   Implementuje komponentu ``SectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``__init__()``.
      - ``accessor``: Parametr ``accessor`` se předává do volání ``__init__()``.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.



.. py:class:: RepeatableSectionNameWithAccessor

   Implementuje komponentu ``RepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``__init__()``.
      - ``accessor``: Parametr ``accessor`` se předává do volání ``__init__()``.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      - ``model_name``: Název modelu používaný pro cílení operace.


   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``related_manager``, None.


   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``new_name``.



.. py:class:: SouboryRepeatableSectionNameWithAccessor

   Implementuje komponentu ``SouboryRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, pracuje se s atributy ``soubory``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``related_manager``, None.


   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``new_name``.



.. py:class:: KomponentaRepeatableSectionNameWithAccessor

   Implementuje komponentu ``KomponentaRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: SubSectionField

   Implementuje komponentu ``SubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``config``: Konfigurační slovník používaný pro sestavení výstupu.
      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.


   .. py:method:: get_config()

      Vrací config. v aplikaci.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``getattr()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``getattr()``, None, proměnná ``instance``.



.. py:class:: NeidentAkceSubSectionField

   Implementuje komponentu ``NeidentAkceSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      **Parametry:**

      - ``instance``: Parametr ``instance`` předává se do volání ``get()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``neident_akce``, None.



.. py:class:: HistorieSubSectionField

   Implementuje komponentu ``HistorieSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``foreign_key``: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      - ``label_key``: Textový název nebo klíč ``label_key`` používaný v rámci operace.


   .. py:method:: get_config()

      Vrací config. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_historie_config()``.



Funkce
------

.. py:function:: get_model(name)

   Vrací model. v aplikaci.

   **Parametry:**

   - ``name``: Parametr ``name`` předává se do volání ``get()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací výsledek volání ``get()``.


.. py:function:: get_gml(geom)

   Vrací gml. v aplikaci.

   **Parametry:**

   - ``geom``: Parametr ``geom`` předává se do volání ``execute()``, pracuje se s atributy ``wkt``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, None.


.. py:function:: get_wkt(geom)

   Vrací wkt. v aplikaci.

   **Parametry:**

   - ``geom``: Parametr ``geom`` předává se do volání ``execute()``, pracuje se s atributy ``wkt``.

   **Návratová hodnota:**

   Vrací vybranou hodnotu z kolekce.


.. py:function:: get_historie_config(label_key)

   Vrací historie config.

   **Parametry:**

   - ``label_key``: Textový název nebo klíč ``label_key`` používaný v rámci operace.

   **Návratová hodnota:**

   Vrací slovník.

