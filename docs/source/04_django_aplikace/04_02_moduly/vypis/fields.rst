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

      :param name: Název nebo identifikátor používaný v rámci operace.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: SectionNameWithAccessor

   Implementuje komponentu ``SectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Název nebo identifikátor používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: PianSectionNameWithAccessor

   Implementuje komponentu ``PianSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: OznamovatelSectionNameWithAccessor

   Implementuje komponentu ``OznamovatelSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_permission()

      Vrací permission. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: Field

   Implementuje komponentu ``Field`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Textový název nebo klíč ``label`` používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.

   .. py:method:: __repr__()

      Vrací reprezentaci objektu pro ladění.

      Textová reprezentace objektu.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: get_label()

      Vrací label. v aplikaci.


.. py:class:: SouborField

   Implementuje komponentu ``SouborField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Textový název nebo klíč ``label`` používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param key_name: Textový název nebo klíč ``key_name`` používaný v rámci operace.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: SouborDownloadField

   Implementuje komponentu ``SouborDownloadField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: Model3dKomponentaField

   Implementuje komponentu ``Model3dKomponentaField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: Model3dKomponentaAktivityField

   Implementuje komponentu ``Model3dKomponentaAktivityField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ChooseField

   Implementuje komponentu ``ChooseField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: StatusField

   Implementuje komponentu ``StatusField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ZjisteniField

   Implementuje komponentu ``ZjisteniField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignField

   Implementuje komponentu ``ForeignField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Název nebo identifikátor používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: GeomGmlField

   Implementuje komponentu ``GeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: GeomWktField

   Implementuje komponentu ``GeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignGeomGmlField

   Implementuje komponentu ``ForeignGeomGmlField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignGeomWktField

   Implementuje komponentu ``ForeignGeomWktField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ManyToManyField

   Implementuje komponentu ``ManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignManyToManyField

   Implementuje komponentu ``ForeignManyToManyField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: DoubleField

   Implementuje komponentu ``DoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: DoubleFieldNum

   Implementuje komponentu ``DoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignDoubleField

   Implementuje komponentu ``ForeignDoubleField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: ForeignDoubleFieldNum

   Implementuje komponentu ``ForeignDoubleFieldNum`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: RepeatableField

   Implementuje komponentu ``RepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Název nebo identifikátor používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      :param template_name: Cesta, URL nebo název zdroje ``template_name``, ze kterého funkce čte nebo kam zapisuje.
      :param model_name: Název modelu používaný pro cílení operace.

   .. py:method:: get_related_manager()

      Vrací related manager.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: VbRepeatableField

   Implementuje komponentu ``VbRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: HistorieRepeatableField

   Implementuje komponentu ``HistorieRepeatableField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_related_manager()

      Vrací related manager.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: RepeatableSectionField

   Implementuje komponentu ``RepeatableSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_label()

      Vrací label. v aplikaci.

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_value()

      Vrací value. v aplikaci.

      :param instance: Instance modelu, které se operace týká.
      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: SectionField

   Implementuje komponentu ``SectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Název nebo identifikátor používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.


.. py:class:: RepeatableSectionNameWithAccessor

   Implementuje komponentu ``RepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param name: Název nebo identifikátor používaný v rámci operace.
      :param accessor: Číselná nebo geometrická hodnota `accessor` použitá při výpočtu nebo transformaci.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      :param model_name: Název modelu používaný pro cílení operace.

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: SouboryRepeatableSectionNameWithAccessor

   Implementuje komponentu ``SouboryRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_sections()

      Vrací sections. v aplikaci.

      :param instance: Instance modelu, které se operace týká.

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: KomponentaRepeatableSectionNameWithAccessor

   Implementuje komponentu ``KomponentaRepeatableSectionNameWithAccessor`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_name()

      Vrací name. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: SubSectionField

   Implementuje komponentu ``SubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param config: Konfigurační slovník používaný pro sestavení výstupu.
      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.

   .. py:method:: get_config()

      Vrací config. v aplikaci.

   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: NeidentAkceSubSectionField

   Implementuje komponentu ``NeidentAkceSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_instance()

      Vrací instance. v aplikaci.

      :param instance: Instance modelu, které se operace týká.


.. py:class:: HistorieSubSectionField

   Implementuje komponentu ``HistorieSubSectionField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param foreign_key: Textový název nebo klíč ``foreign_key`` používaný v rámci operace.
      :param label_key: Textový název nebo klíč ``label_key`` používaný v rámci operace.

   .. py:method:: get_config()

      Vrací config. v aplikaci.


Funkce
------

.. py:function:: get_model(name)

   Vrací model. v aplikaci.

   :param name: Název nebo identifikátor používaný v rámci operace.

.. py:function:: get_gml(geom)

   Vrací gml. v aplikaci.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.

.. py:function:: get_wkt(geom)

   Vrací wkt. v aplikaci.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.

.. py:function:: get_historie_config(label_key)

   Vrací historie config.

   :param label_key: Textový název nebo klíč ``label_key`` používaný v rámci operace.
