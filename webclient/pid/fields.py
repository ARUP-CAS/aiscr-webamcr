from dal import autocomplete
from pid.verificators import verify_doi, verify_orcid, verify_ror, verify_wikidata
from pid.views import DoiAutocompleteView, OrcidAutocompleteView, RorAutocompleteView, WikiDataAutocompleteView


class PidAutocompleteField(autocomplete.Select2ListChoiceField):
    autocomplete_class = None
    attribute_name = None

    def __init__(self, **kwargs):
        self.instance = kwargs.pop("instance", None)
        self.initial_value = kwargs.pop("initial_value", None)
        super().__init__(**kwargs)
        self._set_initial_values()

    def _get_initial_value_from_instance(self):
        return getattr(self.instance, self.attribute_name)

    def _set_initial_values(self):
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
    autocomplete_class = DoiAutocompleteView
    attribute_name = "doi"

    def valid_value(self, value):
        return verify_doi(value)

    def validate(self, value):
        return verify_doi(value)


class OrcidAutocompleteField(PidAutocompleteField):
    autocomplete_class = OrcidAutocompleteView
    attribute_name = "orcid"

    def _get_initial_value_from_instance(self):
        value = super()._get_initial_value_from_instance()
        value = value.replace("https://orcid.org/", "")
        return value

    def prepare_value(self, value):
        return value.replace("https://orcid.org/", "")

    def valid_value(self, value):
        return verify_orcid(value)

    def validate(self, value):
        return verify_orcid(value)


class RorAutocompleteField(PidAutocompleteField):
    autocomplete_class = RorAutocompleteView
    attribute_name = "ror"

    def valid_value(self, value):
        return verify_ror(value)

    def validate(self, value):
        return verify_ror(value)


class WikiDataAutocompleteField(PidAutocompleteField):
    autocomplete_class = WikiDataAutocompleteView
    attribute_name = "wikidata"

    def valid_value(self, value):
        return verify_wikidata(value)

    def validate(self, value):
        return verify_wikidata(value)
