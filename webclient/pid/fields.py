from dal import autocomplete
from pid.verificators import verify_doi, verify_orcid, verify_ror, verify_wikidata
from pid.views import DoiAutocompleteView, OrcidAutocompleteView, RorAutocompleteView, WikiDataAutocompleteView


class PidAutocompleteField(autocomplete.Select2ListChoiceField):
    """Implementuje komponentu ``PidAutocompleteField`` v rámci aplikace."""

    autocomplete_class = None
    attribute_name = None

    def __init__(self, **kwargs):
        """
        Inicializuje instanci třídy.

        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        self.instance = kwargs.pop("instance", None)
        self.initial_value = kwargs.pop("initial_value", None)
        super().__init__(**kwargs)
        self._set_initial_values()

    def _get_initial_value_from_instance(self):
        """
        Vrací initial value from instance.

        :return: Vrací načtená data odpovídající vstupním parametrům.
        """
        return getattr(self.instance, self.attribute_name)

    def _set_initial_values(self):
        """
        Nastaví initial values.

        :return: Vrací výsledek provedené operace.
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
    """Implementuje komponentu ``DoiAutocompleteField`` v rámci aplikace."""

    autocomplete_class = DoiAutocompleteView
    attribute_name = "doi"

    def valid_value(self, value):
        """
        Provádí operaci valid value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_doi(value)

    def validate(self, value):
        """
        Validuje hodnotu. v aplikaci.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_doi(value)


class OrcidAutocompleteField(PidAutocompleteField):
    """Implementuje komponentu ``OrcidAutocompleteField`` v rámci aplikace."""

    autocomplete_class = OrcidAutocompleteView
    attribute_name = "orcid"

    def _get_initial_value_from_instance(self):
        """
        Vrací initial value from instance.

        :return: Vrací načtená data odpovídající vstupním parametrům.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://orcid.org/", "") if value else None
        return value

    def prepare_value(self, value):
        """
        Provádí operaci prepare value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return value.replace("https://orcid.org/", "") if value else None

    def valid_value(self, value):
        """
        Provádí operaci valid value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_orcid(value)

    def validate(self, value):
        """
        Validuje hodnotu. v aplikaci.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_orcid(value)


class RorAutocompleteField(PidAutocompleteField):
    """Implementuje komponentu ``RorAutocompleteField`` v rámci aplikace."""

    autocomplete_class = RorAutocompleteView
    attribute_name = "ror"

    def valid_value(self, value):
        """
        Provádí operaci valid value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_ror(value)

    def validate(self, value):
        """
        Validuje hodnotu. v aplikaci.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_ror(value)


class WikiDataAutocompleteField(PidAutocompleteField):
    """Implementuje komponentu ``WikiDataAutocompleteField`` v rámci aplikace."""

    autocomplete_class = WikiDataAutocompleteView
    attribute_name = "wikidata"

    def _get_initial_value_from_instance(self):
        """
        Vrací initial value from instance.

        :return: Vrací načtená data odpovídající vstupním parametrům.
        """
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://www.wikidata.org/entity/", "") if value else None
        return value

    def prepare_value(self, value):
        """
        Provádí operaci prepare value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return value.replace("https://www.wikidata.org/entity/", "") if value else None

    def valid_value(self, value):
        """
        Provádí operaci valid value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_wikidata(value)

    def validate(self, value):
        """
        Validuje hodnotu. v aplikaci.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
        return verify_wikidata(value)
