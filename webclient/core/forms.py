import json
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

        :param attrs: Kolekce ``attrs`` zpracovávaná touto funkcí.
        :param choices: Parametr ``choices`` se předává do volání ``__init__()``.
        """
        super().__init__(attrs, choices)


class TwoLevelSelectField(forms.CharField):
    """
    Potrebná úprava metód pro Charfield ve formuláři, pokud se používa widget se zobrazením dvou-stupňového seznamu.
    """

    def to_python(self, selected_value):
        """
        Konvertuje vybranou hodnotu na Python objekt Heslar.

        :param selected_value: ID vybraného hesláře.
        :return: Instance Heslar objektu nebo None.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        """
        Určí, zda changed.

        :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
        :param data: Kolekce ``data`` zpracovávaná touto funkcí.
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
        Vrátí instanci Heslar objektu nebo spustí standardní vyčištění pole.

        :param selected_value: ID vybraného hesláře.
        :return: Instance Heslar objektu nebo výsledek ```super().clean()``.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return super().clean(selected_value)

    def to_python(self, selected_value):
        """
        Konvertuje vybranou hodnotu na Python objekt Heslar.

        :param selected_value: ID vybraného hesláře.
        :return: Instance Heslar objektu nebo None.
        """
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        """
        Určí, zda changed.

        :param initial: Stavová nebo časová hodnota `initial` používaná při rozhodování logiky.
        :param data: Kolekce ``data`` zpracovávaná touto funkcí.
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

        :param db_stav: Stavová hodnota načtená z databáze.
        :param require_confirmation: Parametr ``require_confirmation`` ovlivňuje větvení podmínek.
        :param dokument_warnings: Parametr ``dokument_warnings`` předává se do volání ``append()``, ``HTML()``, ovlivňuje větvení podmínek.
        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
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
        """
        Ověří, že se stav záznamu nezměnil mezi načtením a odesláním.

        :return: Ověřená data.
        :raises forms.ValidationError: Vyvolá se s textem "State_changed" pokud se stav změnil.
        """
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

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
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

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
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

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param az: Parametr ``az`` se předává do volání ``filter()``, pracuje se s atributy ``stav``, ``ident_cely``, ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
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
        Zformátuje hodnotu na 3 desetinná místa.

        :param value: Hodnota k zformátování.
        :return: Zformátovaná hodnota nebo None.
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

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(OdstavkaSystemuForm, self).__init__(*args, **kwargs)
        with open("/vol/web/nginx/data/cs/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_cs"].initial = soup.find("p").get_text() if soup.find("p") else ""
        with open("/vol/web/nginx/data/en/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_en"].initial = soup.find("p").get_text() if soup.find("p") else ""
        with open("/vol/web/nginx/data/cs/oznameni/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_oznam_cs"].initial = soup.find("p").string
        with open("/vol/web/nginx/data/en/oznameni/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
        self.fields["error_text_oznam_en"].initial = soup.find("p").string
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


class OptimisticLockingMixin:
    """
    Mixin pro detekci souběžných úprav záznamu (optimistické zamykání).

    Při inicializaci formuláře s existující instancí uloží aktuální hodnoty polí modelu
    do skrytého pole (výchozí název ``optimistic_lock_data``, lze přepsat atributem
    :attr:`optimistic_lock_field_name`). Při odeslání formuláře lze pomocí metody
    :meth:`get_conflicting_fields` zjistit, která pole byla mezitím změněna v databázi.

    Pokud je na jedné stránce více formulářů sdílejících jeden POST, je nutné v každé
    podtřídě nastavit unikátní :attr:`optimistic_lock_field_name`, aby nedošlo ke kolizi.

    Podtřída by měla skryté pole zahrnout do layoutu formuláře nebo ho vykreslit ručně v šabloně.
    """

    #: Název skrytého pole pro uložení snapshotu dat. Přepište v podtřídě při kolizi názvů.
    optimistic_lock_field_name = "optimistic_lock_data"

    #: Pole formuláře, která se přeskočí při porovnávání (seznam názvů polí).
    optimistic_lock_exclude = []

    #: Pole dostupná jako atributy instance, ale nikoli jako DB modelová pole (např. vlastnosti
    #: odvozené z geometrie). Hodnoty se čtou přes ``getattr(instance, field_name)``.
    optimistic_lock_instance_fields = []

    def __init__(self, *args, **kwargs):
        """
        Inicializuje mixin a přidá skryté pole pro optimistické zamykání.

        :param args: Parametry předané do nadřazeného ``__init__``.
        :param kwargs: Klíčové parametry předané do nadřazeného ``__init__``.
        """
        super().__init__(*args, **kwargs)
        self._secondary_locks = {}
        instance = kwargs.get("instance")
        if instance and instance.pk:
            self.fields[self.optimistic_lock_field_name] = forms.CharField(
                widget=forms.HiddenInput(),
                required=False,
                label="",
            )
            if not self.is_bound:
                self.initial[self.optimistic_lock_field_name] = self._serialize_instance_for_lock(instance)

    def _get_lock_fields(self):
        """
        Vrací seznam názvů polí formuláře zahrnutých do kontroly souběžných změn.

        Zahrnuje DB modelová pole i pole z :attr:`optimistic_lock_instance_fields`.

        :return: Seznam názvů polí, která jsou sledována a nejsou vyloučena.
        """
        result = []
        for field_name in self.fields:
            if field_name in self.optimistic_lock_exclude or field_name == self.optimistic_lock_field_name:
                continue
            try:
                self._meta.model._meta.get_field(field_name)
                result.append(field_name)
            except Exception:
                pass
        for field_name in self.optimistic_lock_instance_fields:
            if field_name not in result and field_name not in self.optimistic_lock_exclude:
                result.append(field_name)
        return result

    def _serialize_instance_for_lock(self, instance):
        """
        Serializuje hodnoty polí instance modelu do JSON řetězce.

        :param instance: Instance modelu, jehož hodnoty se serializují.
        :return: JSON řetězec s hodnotami polí pro pozdější porovnání.
        """
        from django.core.exceptions import FieldDoesNotExist

        data = {}
        for field_name in self._get_lock_fields():
            if field_name in self.optimistic_lock_instance_fields:
                value = getattr(instance, field_name, None)
                if value is None:
                    data[field_name] = None
                elif hasattr(value, "isoformat"):
                    data[field_name] = value.isoformat()
                else:
                    data[field_name] = value if isinstance(value, (int, float, bool)) else str(value)
                continue
            try:
                model_field = self._meta.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            if model_field.many_to_many:
                m2m_manager = getattr(instance, field_name, None)
                data[field_name] = sorted([obj.pk for obj in m2m_manager.all()]) if m2m_manager is not None else []
            elif model_field.is_relation:
                data[field_name] = getattr(instance, f"{field_name}_id", None)
            else:
                value = getattr(instance, field_name, None)
                if value is None:
                    data[field_name] = None
                elif hasattr(value, "isoformat"):
                    data[field_name] = value.isoformat()
                else:
                    data[field_name] = value if isinstance(value, (int, float, bool)) else str(value)
        return json.dumps(data, default=str)

    def get_conflicting_fields(self):
        """
        Porovná původní stav polí se stavem v databázi a vrátí seznam konfliktních polí.

        Načte čerstvý stav záznamu z databáze a porovná ho s hodnotami uloženými
        při renderování formuláře v poli :attr:`optimistic_lock_field_name`.

        :return: Seznam názvů polí, která byla mezitím změněna jinou úpravou.
        """
        if not self.instance or not self.instance.pk:
            return []
        lock_data_str = self.data.get(self.add_prefix(self.optimistic_lock_field_name), "")
        if not lock_data_str:
            return []
        try:
            original_data = json.loads(lock_data_str)
        except (json.JSONDecodeError, ValueError):
            return []
        try:
            fresh_instance = self._meta.model.objects.get(pk=self.instance.pk)
        except self._meta.model.DoesNotExist:
            return list(original_data.keys())
        current_data = json.loads(self._serialize_instance_for_lock(fresh_instance))
        return [
            field_name
            for field_name, original_value in original_data.items()
            if field_name in current_data and current_data[field_name] != original_value
        ]

    def add_secondary_lock(self, instance, field_name, lock_fields):
        """
        Přidá skryté pole se snapshotem stavu jiné instance modelu (secondary lock).

        Použití: formulář pro vytvoření PIANu chrání i editaci souvisejícího DJ.
        Lze volat opakovaně s různými ``field_name`` a uzamknout tak formulář
        proti více souvisejícím modelům najednou.

        :param instance: Instance modelu, jejíž stav má být sledován.
        :param field_name: Unikátní název skrytého pole pro snapshot.
        :param lock_fields: Seznam DB polí instance pro porovnání (FK se serializují přes ``*_id``).
        """
        if instance is None or instance.pk is None:
            return
        self._secondary_locks[field_name] = {
            "instance": instance,
            "lock_fields": list(lock_fields),
        }
        self.fields[field_name] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False,
            label="",
        )
        if not self.is_bound:
            self.initial[field_name] = self._serialize_fields_for_lock(instance, lock_fields)

    def _serialize_fields_for_lock(self, instance, lock_fields):
        """
        Serializuje vybraná DB pole instance modelu do JSON řetězce.

        Pole, která nejsou DB pole modelu, jsou ignorována. M2M pole se ukládají jako
        seřazený seznam PK, FK jako ``*_id`` hodnota, datetime přes ``isoformat()``.

        :param instance: Instance modelu, jehož pole se serializují.
        :param lock_fields: Seznam DB polí, která se mají serializovat.
        :return: JSON řetězec s hodnotami polí pro pozdější porovnání.
        """
        from django.core.exceptions import FieldDoesNotExist

        Model = type(instance)
        data = {}
        for field_name in lock_fields:
            try:
                model_field = Model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            if model_field.many_to_many:
                m2m_manager = getattr(instance, field_name, None)
                data[field_name] = sorted(m2m_manager.values_list("pk", flat=True)) if m2m_manager is not None else []
            elif model_field.is_relation:
                data[field_name] = getattr(instance, f"{field_name}_id", None)
            else:
                value = getattr(instance, field_name, None)
                if value is None:
                    data[field_name] = None
                elif hasattr(value, "isoformat"):
                    data[field_name] = value.isoformat()
                else:
                    data[field_name] = value if isinstance(value, (int, float, bool)) else str(value)
        return json.dumps(data, default=str)

    def get_secondary_conflicting_fields(self, field_name):
        """
        Vrátí seznam polí instance pod daným secondary lockem, která byla v DB mezitím změněna.

        :param field_name: Název skrytého pole použitý při :meth:`add_secondary_lock`.
        :return: Seznam názvů polí, která byla mezitím změněna jinou úpravou.
        """
        lock = self._secondary_locks.get(field_name)
        if not lock or not lock["instance"] or not lock["instance"].pk:
            return []
        lock_data_str = self.data.get(self.add_prefix(field_name), "")
        if not lock_data_str:
            return []
        try:
            original_data = json.loads(lock_data_str)
        except (json.JSONDecodeError, ValueError):
            return []
        Model = type(lock["instance"])
        try:
            fresh_instance = Model.objects.get(pk=lock["instance"].pk)
        except Model.DoesNotExist:
            return list(original_data.keys())
        current_data = json.loads(self._serialize_fields_for_lock(fresh_instance, lock["lock_fields"]))
        return [
            f for f, original_value in original_data.items() if f in current_data and current_data[f] != original_value
        ]


class BaseFilterForm(forms.Form):
    """Implementuje komponentu ``BaseFilterForm`` v rámci aplikace."""

    list_to_check = ["historie_datum_zmeny_od"]

    def clean(self):
        """
        Validuje rozmezí datumů v historii — startovní datum musí být dříve než koncové.

        :return: Slovník s očistěnými daty formuláře.
        :raises forms.ValidationError: Pokud je startovní datum pozdější než koncové.
        """
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
        """
        Validuje nahraný PO soubor — kontroluje velikost a formát.

        :return: Slovník s očistěnými daty formuláře.
        :raises forms.ValidationError: Pokud je soubor příliš malý (< 1000 B) nebo nemá příponu ``.po``.
        """
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
