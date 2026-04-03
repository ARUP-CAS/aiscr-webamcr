from dal.autocomplete import ListSelect2, ModelSelect2, ModelSelect2Multiple, Select2Multiple
from dal_select2.widgets import Select2WidgetMixin
from django import forms
from django.utils.translation import gettext as _


class ForeignKeyReadOnlyTextInput(forms.TextInput):
    """Widget pro textinput pro vazbu cizí klíč."""

    def __init__(self, value=None, attrs=None):
        """
        Inicializuje instanci třídy.

        :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``__init__``.
        :param attrs: Kolekce ``attrs`` zpracovávaná touto funkcí.
        """
        if attrs is None:
            attrs = {}
        attrs["readonly"] = True
        super().__init__(attrs)
        self.value = None

    def format_value(self, value):
        """Formátuje hodnotu cizího klíče pro čtení jako textový popis.

        :param value: Primární klíč objektu k zobrazení.
        :return: Textový popis objektu.
        """
        return str(self.value)


class AutocompleteSelect2WidgetMixin(Select2WidgetMixin):
    """Implementuje komponentu ``AutocompleteSelect2WidgetMixin`` v rámci aplikace."""

    def build_attrs(self, *args, **kwargs):
        """
        Nastaveni placeholderu pro pole, pokud neni poskytnuto a zmena zakladni tridy.

        :param args: Parametr ``args`` se předává do volání ``build_attrs()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``build_attrs()``.

            :return: Vrací proměnná ``attrs``.
        """
        attrs = super(AutocompleteSelect2WidgetMixin, self).build_attrs(*args, **kwargs)
        attrs.setdefault("data-placeholder", _("core.widgets.AutocompleteSelect2WidgetMixin.data-placeholder"))

        class_replacements = {
            "autocompletemodelselect2multiple": "modelselect2multiple",
            "autocompletemodelselect2": "modelselect2",
            "autocompleteselect2multiple": "select2multiple",
            "autocompletelistselect2": "listselect2",
        }

        for old_class, new_class in class_replacements.items():
            if "class" in attrs and old_class in attrs["class"]:
                attrs["class"] = attrs["class"].replace(old_class, new_class)
                break

        return attrs


class AutocompleteListSelect2(AutocompleteSelect2WidgetMixin, ListSelect2):
    """Implementuje komponentu ``AutocompleteListSelect2`` v rámci aplikace."""

    pass


class AutocompleteSelect2Multiple(AutocompleteSelect2WidgetMixin, Select2Multiple):
    """Implementuje komponentu ``AutocompleteSelect2Multiple`` v rámci aplikace."""

    pass


class AutocompleteModelSelect2(AutocompleteSelect2WidgetMixin, ModelSelect2):
    """Implementuje komponentu ``AutocompleteModelSelect2`` v rámci aplikace."""

    pass


class AutocompleteModelSelect2Multiple(AutocompleteSelect2WidgetMixin, ModelSelect2Multiple):
    """Implementuje komponentu ``AutocompleteModelSelect2Multiple`` v rámci aplikace."""

    pass
