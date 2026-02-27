from dal import autocomplete
from pid.verificators import verify_doi, verify_orcid, verify_ror, verify_wikidata
from pid.views import DoiAutocompleteView, OrcidAutocompleteView, RorAutocompleteView, WikiDataAutocompleteView


class PidAutocompleteField(autocomplete.Select2ListChoiceField):
    """Třída `PidAutocompleteField` v modulu `webclient.pid.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    autocomplete_class = None
    attribute_name = None

    def __init__(self, **kwargs):
        """Funkce `PidAutocompleteField.__init__` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param kwargs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.instance = kwargs.pop("instance", None)
        self.initial_value = kwargs.pop("initial_value", None)
        super().__init__(**kwargs)
        self._set_initial_values()

    def _get_initial_value_from_instance(self):
        """Funkce `PidAutocompleteField._get_initial_value_from_instance` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        return getattr(self.instance, self.attribute_name)

    def _set_initial_values(self):
        """Funkce `PidAutocompleteField._set_initial_values` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        if self.initial_value:
            result_list = self.autocomplete_class.api_call(self.initial_value, True)
        elif self.instance and getattr(self.instance, self.attribute_name, None):
            value = self._get_initial_value_from_instance()
            result_list = self.autocomplete_class.api_call(value)
        else:
            result_list = []
        if result_list:
            self.choices = [result_list[0]]


class DoiAutocompleteField(PidAutocompleteField):
    """Třída `DoiAutocompleteField` v modulu `webclient.pid.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    autocomplete_class = DoiAutocompleteView
    attribute_name = "doi"

    def valid_value(self, value):
        """Funkce `DoiAutocompleteField.valid_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_doi(value)

    def validate(self, value):
        """Funkce `DoiAutocompleteField.validate` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_doi(value)


class OrcidAutocompleteField(PidAutocompleteField):
    """Třída `OrcidAutocompleteField` v modulu `webclient.pid.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    autocomplete_class = OrcidAutocompleteView
    attribute_name = "orcid"

    def _get_initial_value_from_instance(self):
        """Funkce `OrcidAutocompleteField._get_initial_value_from_instance` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://orcid.org/", "") if value else None
        return value

    def prepare_value(self, value):
        """Funkce `OrcidAutocompleteField.prepare_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return value.replace("https://orcid.org/", "") if value else None

    def valid_value(self, value):
        """Funkce `OrcidAutocompleteField.valid_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_orcid(value)

    def validate(self, value):
        """Funkce `OrcidAutocompleteField.validate` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_orcid(value)


class RorAutocompleteField(PidAutocompleteField):
    """Třída `RorAutocompleteField` v modulu `webclient.pid.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    autocomplete_class = RorAutocompleteView
    attribute_name = "ror"

    def valid_value(self, value):
        """Funkce `RorAutocompleteField.valid_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_ror(value)

    def validate(self, value):
        """Funkce `RorAutocompleteField.validate` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_ror(value)


class WikiDataAutocompleteField(PidAutocompleteField):
    """Třída `WikiDataAutocompleteField` v modulu `webclient.pid.fields`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    autocomplete_class = WikiDataAutocompleteView
    attribute_name = "wikidata"

    def _get_initial_value_from_instance(self):
        """Funkce `WikiDataAutocompleteField._get_initial_value_from_instance` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://www.wikidata.org/entity/", "") if value else None
        return value

    def prepare_value(self, value):
        """Funkce `WikiDataAutocompleteField.prepare_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return value.replace("https://www.wikidata.org/entity/", "") if value else None

    def valid_value(self, value):
        """Funkce `WikiDataAutocompleteField.valid_value` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_wikidata(value)

    def validate(self, value):
        """Funkce `WikiDataAutocompleteField.validate` v modulu `webclient.pid.fields`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param value: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        return verify_wikidata(value)
