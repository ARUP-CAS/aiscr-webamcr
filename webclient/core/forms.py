import logging

from bs4 import BeautifulSoup
from core.constants import AZ_STAV_ODESLANY, D_STAV_ODESLANY
from core.message_constants import TRANSLATION_FILE_TOOSMALL, TRANSLATION_FILE_WRONG_FORMAT
from core.models import OdstavkaSystemu
from core.widgets import AutocompleteSelect2Multiple
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.conf import settings
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from dokument.models import Dokument
from heslar.models import Heslar
from polib import pofile

logger = logging.getLogger(__name__)


class SelectMultipleSeparator(forms.SelectMultiple):
    """Override nad widgetom na zobrazení multi selectu stejně v každém formuláři."""

    def __init__(
        self,
        attrs={
            "class": "selectpicker",
            "data-multiple-separator": "; ",
            "data-live-search": "true",
        },
        choices=(),
    ):
        """
        Inicializuje instanci třídy.

        :param attrs: Vstupní hodnota ``attrs`` pro danou operaci.
        :param choices: Vstupní hodnota ``choices`` pro danou operaci.
        """
        super().__init__(attrs, choices)


class TwoLevelSelectField(forms.CharField):
    """
    Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.
    """

    def to_python(self, selected_value):
        """
        Provádí operaci to python.

        :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        """
        Určí, zda changed.

        :param initial: Vstupní hodnota ``initial`` pro danou operaci.
        :param data: Vstupní hodnota ``data`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class HeslarChoiceFieldField(forms.ChoiceField):
    """
    Potrebná úprava metód pro ChoiceField ve formuláři, pro správně zobrazení a spracováni predmetu specifikace.
    """

    def clean(self, selected_value):
        """
        Provádí operaci clean.

        :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return super().clean(selected_value)

    def to_python(self, selected_value):
        """
        Provádí operaci to python.

        :param selected_value: Vstupní hodnota ``selected_value`` pro danou operaci.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        """
        Určí, zda changed.

        :param initial: Vstupní hodnota ``initial`` pro danou operaci.
        :param data: Vstupní hodnota ``data`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class CheckStavNotChangedForm(forms.Form):
    """
    Formulář pro kontrolu jestli se stav záznamu nezmenil mezi jeho načtením a odeslánim zmeny.

    Celá logika je v clean metóde.
    """

    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, db_stav=None, require_confirmation=False, dokument_warnings=None, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param db_stav: Vstupní hodnota ``db_stav`` pro danou operaci.
        :param require_confirmation: Vstupní hodnota ``require_confirmation`` pro danou operaci.
        :param dokument_warnings: Vstupní hodnota ``dokument_warnings`` pro danou operaci.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        self.db_stav = db_stav
        super(CheckStavNotChangedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        layout_blocks = [
            Div("old_stav", css_class="col-sm-12"),
        ]
        if require_confirmation:
            self.fields["confirm"] = forms.BooleanField(
                required=True, label=_("core.forms.CheckStavNotChangedForm.confirm")
            )
            layout_blocks.append(
                Div("confirm", css_class="col-sm-12"),
            )
        if dokument_warnings:
            self.fields["dokument_confirm"] = forms.BooleanField(
                required=True, label=_("core.forms.CheckStavNotChangedForm.dokument_confirm")
            )
            layout_blocks.append(
                HTML(
                    '<div class="alert alert-info" role="alert">'
                    + "<ul>{}</ul>".format("".join(f"<li>{item}</li>" for item in dokument_warnings))
                    + "</div>"
                )
            )
            layout_blocks.append(
                Div("dokument_confirm", css_class="col-sm-12"),
            )

        self.helper.layout = Layout(Div(*layout_blocks, css_class="app-card-form"))
        self.helper.form_tag = False

    def clean(self):
        """Provádí operaci clean."""
        cleaned_data = super().clean()
        old_stav = self.cleaned_data.get("old_stav")
        if str(self.db_stav) != str(old_stav):
            logger.debug(
                "core.forms.CheckStavNotChangedForm.clean.ValidationError",
                extra={
                    "value": "Stav zaznamu se zmenil mezi posunutim stavu.",
                    "stav": self.db_stav,
                    "stav_old": old_stav,
                },
            )
            raise forms.ValidationError("State_changed")
        return cleaned_data


class VratitForm(forms.Form):
    """Formulář pro vrácení záznamu. Obsahuje jen text pole pro zdůvodnění vrácení."""

    reason = forms.CharField(
        label=_("core.forms.VratitForm.reason.label"),
        required=True,
        help_text=_("core.forms.VratitForm.reason.tooltip"),
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super(VratitForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.include_media = False


class VratitFormDokument(VratitForm):
    """Implementuje komponentu ``VratitFormDokument`` v rámci aplikace."""

    ident_cely = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget = forms.Textarea(
            attrs={"rows": 3, "cols": 150, "required": "required", "class": "textinput form-control"}
        )


class VratitFormAZ(VratitForm):
    """
    Formulář pro vrácení záznamu Akce nebo Lokality. Obsahuje text pole pro zdůvodnění vrácení a výběr dokumentů pro vrácení.
    """

    dokument = forms.ModelMultipleChoiceField(
        queryset=Dokument.objects.none(),
        widget=AutocompleteSelect2Multiple,
        label=_("core.forms.VratitFormAZ.dokument.label"),
        help_text=_("core.forms.VratitFormAZ.dokument.tooltip"),
        required=False,
    )

    def __init__(self, *args, az, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param az: Vstupní hodnota ``az`` pro danou operaci.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super().__init__(*args, **kwargs)
        if az.stav != AZ_STAV_ODESLANY:
            self.fields.pop("dokument", None)
            self.helper.layout.fields.remove("dokument")
            return
        self.fields["dokument"].queryset = Dokument.objects.filter(
            stav=D_STAV_ODESLANY, casti__archeologicky_zaznam__ident_cely=az.ident_cely
        ).distinct()


class DecimalTextWideget(forms.widgets.TextInput):
    """Třida pro formátování hodnoty velikosti souboru na 3 desetiná místa."""

    def format_value(self, value):
        """
        Provádí operaci format value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        """
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
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = OdstavkaSystemu
        fields = (
            "info_od",
            "datum_odstavky",
            "cas_odstavky",
            "status",
        )

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super(OdstavkaSystemuForm, self).__init__(*args, **kwargs)
        with open("/vol/web/nginx/data/cs/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_cs"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/en/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_en"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/cs/oznameni/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_oznam_cs"].initial = soup.find("h1").string
        with open("/vol/web/nginx/data/en/oznameni/custom_503.html") as fp:
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
    """Implementuje komponentu ``PermissionImportForm`` v rámci aplikace."""

    file = forms.FileField(
        required=True,
        label=_("core.forms.permissionImport.file.label"),
        widget=forms.FileInput(
            attrs={
                "accept": (
                    ".csv,"
                    "application/csv,"
                    "text/csv,"
                    "application/vnd.ms-excel,"
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            }
        ),
    )


class PermissionSkipImportForm(forms.Form):
    """Implementuje komponentu ``PermissionSkipImportForm`` v rámci aplikace."""

    file = forms.FileField(
        required=True,
        label=_("core.forms.permissionSkipImport.file.label"),
        widget=forms.FileInput(attrs={"accept": ".csv"}),
    )


class BaseFilterForm(forms.Form):
    """Implementuje komponentu ``BaseFilterForm`` v rámci aplikace."""

    list_to_check = ["historie_datum_zmeny_od"]

    def clean(self):
        """Provádí operaci clean."""
        cleaned_data = super(BaseFilterForm, self).clean()
        error_list = []
        ERRORS = {
            "historie_datum_zmeny_od": _("core.forms.baseFilterForm.historie_datum_zmeny.error"),
            "planovane_zahajeni": _("core.forms.baseFilterForm.planovane_zahajeni.error"),
            "termin_odevzdani_nz": _("core.forms.baseFilterForm.termin_odevzdani_nz.error"),
            "datum_ukonceni": _("core.forms.baseFilterForm.datum_ukonceni.error"),
            "datum_zahajeni": _("core.forms.baseFilterForm.datum_zahajeni.error"),
            "akce_datum_ukonceni": _("core.forms.baseFilterForm.akce_datum_ukonceni.error"),
            "akce_datum_zahajeni": _("core.forms.baseFilterForm.akce_datum_zahajeni.error"),
            "datum_vzniku": _("core.forms.baseFilterForm.datum_vzniku.error"),
            "let_datum": _("core.forms.baseFilterForm.let_datum.error"),
            "datum_zverejneni": _("core.forms.baseFilterForm.datum_zverejneni.error"),
            "datum_nalezu": _("core.forms.baseFilterForm.datum_nalezu.error"),
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
    """Implementuje komponentu ``TransaltionImportForm`` v rámci aplikace."""

    file = forms.FileField(
        required=True,
        label=_("core.forms.TransaltionImportForm.file.label"),
        widget=forms.FileInput(attrs={"accept": ".po"}),
    )

    def clean(self):
        """Provádí operaci clean."""
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        if file.size < 1000:
            raise forms.ValidationError({"file": TRANSLATION_FILE_TOOSMALL})
        if file.name.split(".")[-1] != "po":
            raise forms.ValidationError({"file": TRANSLATION_FILE_WRONG_FORMAT})
        return cleaned_data


class ImportDataAdminForm(forms.Form):
    """Implementuje komponentu ``ImportDataAdminForm`` v rámci aplikace."""

    PERFORMED_ACTION_INSERT = "insert"
    PERFORMED_ACTION_UPDATE = "update"
    PERFORMED_ACTION_DELETE = "delete"

    data_file = forms.FileField(
        required=True,
        label=_("core.forms.ImportDataAdminForm.data_file.label"),
        widget=forms.FileInput(attrs={"accept": ("application/vnd.ms-excel, application/zip")}),
    )

    performed_action = forms.CharField(
        required=True,
        label=_("core.forms.ImportDataAdminForm.action.label"),
        widget=forms.Select(
            choices=[
                (PERFORMED_ACTION_INSERT, _("core.forms.ImportDataAdminForm.insert")),
                (PERFORMED_ACTION_UPDATE, _("core.forms.ImportDataAdminForm.update")),
                (PERFORMED_ACTION_DELETE, _("core.forms.ImportDataAdminForm.delete")),
            ]
        ),
    )
