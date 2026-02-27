from dal import autocomplete
from pid.verificators import verify_doi, verify_orcid, verify_ror, verify_wikidata
from pid.views import DoiAutocompleteView, OrcidAutocompleteView, RorAutocompleteView, WikiDataAutocompleteView


class PidAutocompleteField(autocomplete.Select2ListChoiceField):
    """Zapouzdřuje chování třídy ``PidAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = None
    attribute_name = None

    def __init__(self, **kwargs):
        """Zpracuje volání ``PidAutocompleteField.__init__`` v rámci modulu ``webclient.pid.fields``."""
        self.instance = kwargs.pop("instance", None)
        self.initial_value = kwargs.pop("initial_value", None)
        super().__init__(**kwargs)
        self._set_initial_values()

    def _get_initial_value_from_instance(self):
        """Provádí funkci ``PidAutocompleteField._get_initial_value_from_instance`` v rámci modulu ``webclient.pid.fields``."""
        return getattr(self.instance, self.attribute_name)

    def _set_initial_values(self):
        """Provádí funkci ``PidAutocompleteField._set_initial_values`` v rámci modulu ``webclient.pid.fields``."""
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
        """Zpracuje volání ``DoiAutocompleteField.valid_value`` v rámci modulu ``webclient.pid.fields``."""
        return verify_doi(value)

    def validate(self, value):
        """Zpracuje volání ``DoiAutocompleteField.validate`` v rámci modulu ``webclient.pid.fields``."""
        return verify_doi(value)


class OrcidAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``OrcidAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = OrcidAutocompleteView
    attribute_name = "orcid"

    def _get_initial_value_from_instance(self):
        """Provádí funkci ``OrcidAutocompleteField._get_initial_value_from_instance`` v rámci modulu ``webclient.pid.fields``."""
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://orcid.org/", "") if value else None
        return value

    def prepare_value(self, value):
        """Zpracuje volání ``OrcidAutocompleteField.prepare_value`` v rámci modulu ``webclient.pid.fields``."""
        return value.replace("https://orcid.org/", "") if value else None

    def valid_value(self, value):
        """Zpracuje volání ``OrcidAutocompleteField.valid_value`` v rámci modulu ``webclient.pid.fields``."""
        return verify_orcid(value)

    def validate(self, value):
        """Zpracuje volání ``OrcidAutocompleteField.validate`` v rámci modulu ``webclient.pid.fields``."""
        return verify_orcid(value)


class RorAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``RorAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = RorAutocompleteView
    attribute_name = "ror"

    def valid_value(self, value):
        """Zpracuje volání ``RorAutocompleteField.valid_value`` v rámci modulu ``webclient.pid.fields``."""
        return verify_ror(value)

    def validate(self, value):
        """Zpracuje volání ``RorAutocompleteField.validate`` v rámci modulu ``webclient.pid.fields``."""
        return verify_ror(value)


class WikiDataAutocompleteField(PidAutocompleteField):
    """Zapouzdřuje chování třídy ``WikiDataAutocompleteField`` pro modul ``webclient.pid.fields``."""
    autocomplete_class = WikiDataAutocompleteView
    attribute_name = "wikidata"

    def _get_initial_value_from_instance(self):
        """Provádí funkci ``WikiDataAutocompleteField._get_initial_value_from_instance`` v rámci modulu ``webclient.pid.fields``."""
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://www.wikidata.org/entity/", "") if value else None
        return value

    def prepare_value(self, value):
        """Zpracuje volání ``WikiDataAutocompleteField.prepare_value`` v rámci modulu ``webclient.pid.fields``."""
        return value.replace("https://www.wikidata.org/entity/", "") if value else None

    def valid_value(self, value):
        """Zpracuje volání ``WikiDataAutocompleteField.valid_value`` v rámci modulu ``webclient.pid.fields``."""
        return verify_wikidata(value)

    def validate(self, value):
        """Zpracuje volání ``WikiDataAutocompleteField.validate`` v rámci modulu ``webclient.pid.fields``."""
        return verify_wikidata(value)
