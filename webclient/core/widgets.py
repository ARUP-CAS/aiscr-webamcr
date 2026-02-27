from dal.autocomplete import ListSelect2, ModelSelect2, ModelSelect2Multiple, Select2Multiple
from dal_select2.widgets import Select2WidgetMixin
from django import forms
from django.utils.translation import gettext as _


class ForeignKeyReadOnlyTextInput(forms.TextInput):
    """
    Widget pro textinput pro vazbu cizí klíč.
    """

    def __init__(self, value=None, attrs=None):
        """Funkce `ForeignKeyReadOnlyTextInput.__init__` v modulu `webclient.core.widgets`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :param attrs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        if attrs is None:
            attrs = {}
        attrs["readonly"] = True
        super().__init__(attrs)
        self.value = None

    def format_value(self, value):
        """Funkce `ForeignKeyReadOnlyTextInput.format_value` v modulu `webclient.core.widgets`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return str(self.value)


class AutocompleteSelect2WidgetMixin(Select2WidgetMixin):
    """Třída `AutocompleteSelect2WidgetMixin` v modulu `webclient.core.widgets`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def build_attrs(self, *args, **kwargs):
        """Nastaveni placeholderu pro pole, pokud neni poskytnuto a zmena zakladni tridy."""
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
    """Třída `AutocompleteListSelect2` v modulu `webclient.core.widgets`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass


class AutocompleteSelect2Multiple(AutocompleteSelect2WidgetMixin, Select2Multiple):
    """Třída `AutocompleteSelect2Multiple` v modulu `webclient.core.widgets`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass


class AutocompleteModelSelect2(AutocompleteSelect2WidgetMixin, ModelSelect2):
    """Třída `AutocompleteModelSelect2` v modulu `webclient.core.widgets`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass


class AutocompleteModelSelect2Multiple(AutocompleteSelect2WidgetMixin, ModelSelect2Multiple):
    """Třída `AutocompleteModelSelect2Multiple` v modulu `webclient.core.widgets`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass
