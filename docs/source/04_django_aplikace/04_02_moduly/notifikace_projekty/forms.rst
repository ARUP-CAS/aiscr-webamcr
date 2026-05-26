NOTIFIKACE_PROJEKTY formuláře
=============================

Definice formulářů.

Třídy
------

.. py:class:: KatastrAutocompleteChoiceField

   ``ChoiceField`` pro katastr s AJAX autocomplete – validuje proti databázi, ne proti ``choices``.

   Standardní ``ChoiceField`` ověřuje odeslanou hodnotu proti seznamu ``choices``, což by
   vynutilo načtení všech katastrů. Místo toho ověříme existenci jediného odeslaného ``pk``
   přímo v databázi (indexovaný dotaz).

   **Metody:**

   .. py:method:: valid_value()

      Ověří, že hodnota odpovídá existujícímu katastru.

      :param value: Odeslaný primární klíč katastru.

      :return: ``True``, pokud katastr s daným ``pk`` existuje.


.. py:class:: PesFormSetHelper

   Implementuje komponentu ``PesFormSetHelper`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: PesNotificationsForm

   Formulář pro správu typu notifikací.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param pes_object_count: Parametr ``pes_object_count`` slouží jako vstup pro logiku funkce ``__init__``.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací proměnná ``cleaned_data``.


.. py:class:: PesInlineFormSet

   Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean()

      Ověří, že formset neobsahuje dvě shodné jednotky (stejné ``object_id``).

      Per-form ``clean`` kontroluje duplicity jen vůči databázi, takže dva nové
      shodné hlídací psy odeslané najednou by jinak prošly a druhý ``INSERT`` by
      spadl na unikátní omezení ``unique_pes`` (``user``, ``content_type``,
      ``object_id``). ``user`` ani ``content_type`` nejsou poli formuláře, proto
      je standardní ``validate_unique`` neumí ochránit.

      :raises forms.ValidationError: Vyvolá se při nalezení duplicitního ``object_id``.

   .. py:method:: count_non_empty_forms()

      Provádí operaci count non empty forms.

      :return: Vrací proměnná ``non_empty_count``.


Funkce
------

.. py:function:: build_katastr_label_choices(object_id)

   Vrátí volbu (``pk``, ``název (okres)``) pro jeden vybraný katastr kvůli popisku ve výběru.

   Slouží jen k vykreslení už zvoleného katastru u existujícího psa; nový formulář žádný
   katastr vybraný nemá. Nahrazuje načítání celého číselníku katastrů.

   :param object_id: Primární klíč zvoleného katastru, nebo ``None``/prázdná hodnota.

   :return: Seznam s jednou dvojicí, nebo prázdný seznam, není-li katastr vybrán.

.. py:function:: create_pes_form(not_readonly, model_typ)

   Funkce která vrací formulář hlídacího psa pro formset.

   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
   :param model_typ: Parametr ``model_typ`` slouží jako vstup pro logiku funkce ``create_pes_form``.

   :return: Vrací proměnná ``PesForm``.
