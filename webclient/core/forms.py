import logging

from django.utils import formats

from django import forms
from crispy_forms.helper import FormHelper
from django.utils.translation import gettext_lazy as _
from core.models import OdstavkaSystemu
from heslar.models import Heslar
from bs4 import BeautifulSoup
from polib import pofile
from django.conf import settings

from core.message_constants import TRANSLATION_FILE_TOOSMALL, TRANSLATION_FILE_WRONG_FORMAT

logger = logging.getLogger(__name__)


class SelectMultipleSeparator(forms.SelectMultiple):
    """
    Override nad widgetom na zobrazení multi selectu stejně v každém formuláři.
    """

    def __init__(
        self,
        attrs={
            "class": "selectpicker",
            "data-multiple-separator": "; ",
            "data-live-search": "true",
        },
        choices=(),
    ):
        super().__init__(attrs, choices)


class TwoLevelSelectField(forms.CharField):
    """
    Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.
    """

    def to_python(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class HeslarChoiceFieldField(forms.ChoiceField):
    """
    Potrebná úprava metód pro ChoiceField ve formuláři, pro správne zobrazení a spracováni predmetu specifikace.
    """

    def clean(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return super().clean(selected_value)

    def to_python(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class CheckStavNotChangedForm(forms.Form):
    """
    Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.
    Celá logika je v clean metóde.
    """

    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, db_stav=None, *args, **kwargs):
        self.db_stav = db_stav
        super(CheckStavNotChangedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        old_stav = self.cleaned_data.get("old_stav")
        if str(self.db_stav) != str(old_stav):
            logger.debug(
                "core.forms.CheckStavNotChangedForm.clean.ValidationError",
                extra={
                    "message": "Stav zaznamu se zmenil mezi posunutim stavu.",
                    "db_stav": self.db_stav,
                    "old_stav": old_stav,
                },
            )
            raise forms.ValidationError("State_changed")
        return cleaned_data


class VratitForm(forms.Form):
    """
    Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení.
    """

    reason = forms.CharField(
        label=_("core.forms.VratitForm.reason.label"),
        required=True,
        help_text=_("core.forms.VratitForm.reason.tooltip"),
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(VratitForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class DecimalTextWideget(forms.widgets.TextInput):
    """
    Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa.
    """

    def format_value(self, value):
        if value == "" or value is None:
            return None
        if self.is_localized:
            return formats.localize_input(value)
        return str(round(value, 3))


class OdstavkaSystemuForm(forms.ModelForm):
    """
    Formulář pro nastavení a úpravu odstávky.
    Vrámci načítáni formuláře se doplní načítají hodnoty z template odstávky.
    """

    error_text_cs = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.errorTextCs.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )
    error_text_en = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.errorTextEn.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )
    error_text_oznam_cs = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.errorTextOznamCs.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )
    error_text_oznam_en = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.errorTextOznamEn.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )
    text_cs = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.textCs.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )
    text_en = forms.CharField(
        label=_("core.forms.OdstavkaSystemuForm.textEn.label"),
        widget=forms.Textarea(attrs={"rows": 10, "cols": 81}),
    )

    class Meta:
        model = OdstavkaSystemu
        fields = (
            "info_od",
            "datum_odstavky",
            "cas_odstavky",
            "status",
        )

    def __init__(self, *args, **kwargs):
        super(OdstavkaSystemuForm, self).__init__(*args, **kwargs)
        with open("/vol/web/nginx/data/cs/custom_50x.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_cs"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/en/custom_50x.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_en"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/cs/oznameni/custom_50x.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_oznam_cs"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/en/oznameni/custom_50x.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_oznam_en"].initial = soup.find("h1").string
        locale_path = settings.LOCALE_PATHS[0]
        languages = settings.LANGUAGES
        for code, lang in languages:
            path = locale_path + "/" + code + "/LC_MESSAGES/django.po"
            po_file = pofile(path)
            entry = po_file.find("base.odstavka.text")
            text = "text_" + code
            self.fields[text].initial = entry.msgstr


class PermissionImportForm(forms.Form):
    file = forms.FileField(
        required=True,
        label=_("core.forms.permissionImport.file.label"),
        widget=forms.FileInput(
            attrs={
                "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            }
        ),
    )


class PermissionSkipImportForm(forms.Form):
    file = forms.FileField(
        required=True,
        label=_("core.forms.permissionSkipImport.file.label"),
        widget=forms.FileInput(attrs={"accept": ".csv"}),
    )


class BaseFilterForm(forms.Form):
    list_to_check = ["historie_datum_zmeny_od"]

    def clean(self):
        cleaned_data = super(BaseFilterForm, self).clean()
        error_list = []
        ERRORS = {
        "historie_datum_zmeny_od":_("core.forms.baseFilterForm.historie_datum_zmeny.error"),
        "planovane_zahajeni":_("core.forms.baseFilterForm.planovane_zahajeni.error"),
        "termin_odevzdani_nz": _("core.forms.baseFilterForm.termin_odevzdani_nz.error"),
        "datum_ukonceni": _("core.forms.baseFilterForm.datum_ukonceni.error"),
        "datum_zahajeni": _("core.forms.baseFilterForm.datum_zahajeni.error"),
        "akce_datum_ukonceni": _("core.forms.baseFilterForm.akce_datum_ukonceni.error"),
        "akce_datum_zahajeni": _("core.forms.baseFilterForm.akce_datum_zahajeni.error"),
        "datum_vzniku": _("core.forms.baseFilterForm.datum_vzniku.error"),
        "let_datum": _("core.forms.baseFilterForm.let_datum.error"),
        "datum_zverejneni": _("core.forms.baseFilterForm.datum_zverejneni.error"),
        "datum_nalezu":_("core.forms.baseFilterForm.datum_nalezu.error"),
        }
        for field_name in self.list_to_check:
            if cleaned_data.get(field_name):
                start_date = cleaned_data.get(field_name).start
                end_date = cleaned_data.get(field_name).stop
                if start_date and end_date:
                    if start_date > end_date:
                        error_list.append(ERRORS[field_name])
        if error_list:
            raise forms.ValidationError(error_list)
        return cleaned_data
    
class TransaltionImportForm(forms.Form):
    file = forms.FileField(
        required=True,
        label=_("core.forms.TransaltionImportForm.file.label"),
        widget=forms.FileInput(attrs={"accept": ".po"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        if file.size < 1000:
            raise forms.ValidationError({"file":TRANSLATION_FILE_TOOSMALL})
        if file.name.split('.')[-1] != 'po':
            raise forms.ValidationError({"file":TRANSLATION_FILE_WRONG_FORMAT})
        return cleaned_data