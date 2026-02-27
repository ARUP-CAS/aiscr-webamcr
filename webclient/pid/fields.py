from dal import autocomplete
from pid.verificators import verify_doi, verify_orcid, verify_ror, verify_wikidata
from pid.views import DoiAutocompleteView, OrcidAutocompleteView, RorAutocompleteView, WikiDataAutocompleteView


class PidAutocompleteField(autocomplete.Select2ListChoiceField):
    """Zapouzdřuje chování třídy ``PidAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = None
    attribute_name = None

    def __init__(self, **kwargs):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.instance = kwargs.pop("instance", None)
        self.initial_value = kwargs.pop("initial_value", None)
        super().__init__(**kwargs)
        self._set_initial_values()

    def _get_initial_value_from_instance(self):
        """Zajišťuje logiku funkce ``_get_initial_value_from_instance``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return getattr(self.instance, self.attribute_name)

    def _set_initial_values(self):
        """Zajišťuje logiku funkce ``_set_initial_values``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
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
    """Zapouzdřuje chování třídy ``DoiAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = DoiAutocompleteView
    attribute_name = "doi"

    def valid_value(self, value):
        """Zajišťuje logiku funkce ``valid_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_doi(value)

    def validate(self, value):
        """Zajišťuje logiku funkce ``validate``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_doi(value)


class OrcidAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``OrcidAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = OrcidAutocompleteView
    attribute_name = "orcid"

    def _get_initial_value_from_instance(self):
        """Zajišťuje logiku funkce ``_get_initial_value_from_instance``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://orcid.org/", "") if value else None
        return value

    def prepare_value(self, value):
        """Zajišťuje logiku funkce ``prepare_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return value.replace("https://orcid.org/", "") if value else None

    def valid_value(self, value):
        """Zajišťuje logiku funkce ``valid_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_orcid(value)

    def validate(self, value):
        """Zajišťuje logiku funkce ``validate``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_orcid(value)


class RorAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``RorAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = RorAutocompleteView
    attribute_name = "ror"

    def valid_value(self, value):
        """Zajišťuje logiku funkce ``valid_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_ror(value)

    def validate(self, value):
        """Zajišťuje logiku funkce ``validate``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_ror(value)


class WikiDataAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``WikiDataAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = WikiDataAutocompleteView
    attribute_name = "wikidata"

    def _get_initial_value_from_instance(self):
        """Zajišťuje logiku funkce ``_get_initial_value_from_instance``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://www.wikidata.org/entity/", "") if value else None
        return value

    def prepare_value(self, value):
        """Zajišťuje logiku funkce ``prepare_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return value.replace("https://www.wikidata.org/entity/", "") if value else None

    def valid_value(self, value):
        """Zajišťuje logiku funkce ``valid_value``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_wikidata(value)

    def validate(self, value):
        """Zajišťuje logiku funkce ``validate``.
        
        :param value: Vstupní hodnota parametru ``value`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return verify_wikidata(value)
