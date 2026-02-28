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

      :param name: Vstupní hodnota ``name`` pro danou operaci.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: SectionNameWithAccessor

   Implementuje komponentu ``SectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: PianSectionNameWithAccessor

   Implementuje komponentu ``PianSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: OznamovatelSectionNameWithAccessor

   Implementuje komponentu ``OznamovatelSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: Field

   Implementuje komponentu ``Field`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Vstupní hodnota ``label`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.

   .. py:method:: __repr__()

      Vrací reprezentaci objektu pro ladění.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.

   .. py:method:: get_label()

      Vrací label. v aplikaci.


.. py:class:: SouborField

   Implementuje komponentu ``SouborField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Vstupní hodnota ``label`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param key_name: Vstupní hodnota ``key_name`` pro danou operaci.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: SouborDownloadField

   Implementuje komponentu ``SouborDownloadField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: Model3dKomponentaField

   Implementuje komponentu ``Model3dKomponentaField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: Model3dKomponentaAktivityField

   Implementuje komponentu ``Model3dKomponentaAktivityField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ChooseField

   Implementuje komponentu ``ChooseField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: StatusField

   Implementuje komponentu ``StatusField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ZjisteniField

   Implementuje komponentu ``ZjisteniField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignField

   Implementuje komponentu ``ForeignField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: GeomGmlField

   Implementuje komponentu ``GeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: GeomWktField

   Implementuje komponentu ``GeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignGeomGmlField

   Implementuje komponentu ``ForeignGeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignGeomWktField

   Implementuje komponentu ``ForeignGeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ManyToManyField

   Implementuje komponentu ``ManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignManyToManyField

   Implementuje komponentu ``ForeignManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: DoubleField

   Implementuje komponentu ``DoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: DoubleFieldNum

   Implementuje komponentu ``DoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignDoubleField

   Implementuje komponentu ``ForeignDoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: ForeignDoubleFieldNum

   Implementuje komponentu ``ForeignDoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: RepeatableField

   Implementuje komponentu ``RepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
      :param template_name: Vstupní hodnota ``template_name`` pro danou operaci.
      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.

   .. py:method:: get_related_manager()

      Vrací related manager.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: VbRepeatableField

   Implementuje komponentu ``VbRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: HistorieRepeatableField

   Implementuje komponentu ``HistorieRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_related_manager()

      Vrací related manager.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: RepeatableSectionField

   Implementuje komponentu ``RepeatableSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_label()

      Vrací label. v aplikaci.

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.


.. py:class:: SectionField

   Implementuje komponentu ``SectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.


.. py:class:: RepeatableSectionNameWithAccessor

   Implementuje komponentu ``RepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: SouboryRepeatableSectionNameWithAccessor

   Implementuje komponentu ``SouboryRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: KomponentaRepeatableSectionNameWithAccessor

   Implementuje komponentu ``KomponentaRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: SubSectionField

   Implementuje komponentu ``SubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param config: Vstupní hodnota ``config`` pro danou operaci.
      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.

   .. py:method:: get_config()

      Vrací config. v aplikaci.

   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: NeidentAkceSubSectionField

   Implementuje komponentu ``NeidentAkceSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      :param instance: Vstupní hodnota ``instance`` pro danou operaci.


.. py:class:: HistorieSubSectionField

   Implementuje komponentu ``HistorieSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
      :param label_key: Vstupní hodnota ``label_key`` pro danou operaci.

   .. py:method:: get_config()

      Vrací config. v aplikaci.


Funkce
------

.. py:function:: get_model(name)

   Vrací model. v aplikaci.

   :param name: Vstupní hodnota ``name`` pro danou operaci.

.. py:function:: get_gml(geom)

   Vrací gml. v aplikaci.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.

.. py:function:: get_wkt(geom)

   Vrací wkt. v aplikaci.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.

.. py:function:: get_historie_config(label_key)

   Vrací historie config.

   :param label_key: Vstupní hodnota ``label_key`` pro danou operaci.
