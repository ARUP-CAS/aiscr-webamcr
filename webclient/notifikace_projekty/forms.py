import logging
from itertools import groupby

from core.widgets import AutocompleteListSelect2
from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _
from heslar.models import RuianKatastr, RuianKraj, RuianOkres
from uzivatel.models import User, UserNotificationType

from .models import Pes

logger = logging.getLogger(__name__)

KRAJ_CONTENT_TYPE = "ruiankraj"
OKRES_CONTENT_TYPE = "ruianokres"
KATASTR_CONTENT_TYPE = "ruiankatastr"
CONTENT_TYPES = [KRAJ_CONTENT_TYPE, OKRES_CONTENT_TYPE, KATASTR_CONTENT_TYPE]
PES_NOTIFICATIONS = [
    "S-E-P-02a",
    "S-E-P-02b",
    "S-E-P-02c",
]


def build_katastr_label_choices(object_id):
    """
    Vrátí volbu (``pk``, ``název (okres)``) pro jeden vybraný katastr kvůli popisku ve výběru.

    Slouží jen k vykreslení už zvoleného katastru u existujícího psa; nový formulář žádný
    katastr vybraný nemá. Nahrazuje načítání celého číselníku katastrů.

    :param object_id: Primární klíč zvoleného katastru, nebo ``None``/prázdná hodnota.

        :return: Seznam s jednou dvojicí, nebo prázdný seznam, není-li katastr vybrán.
    """
    if not object_id:
        return []
    return list(
        RuianKatastr.objects.filter(pk=object_id)
        .annotate(
            full_name=Concat(
                "nazev",
                Value(" ("),
                "okres__nazev",
                Value(")"),
                output_field=CharField(),
            )
        )
        .values_list("pk", "full_name")
    )


class KatastrAutocompleteChoiceField(forms.ChoiceField):
    """
    ``ChoiceField`` pro katastr s AJAX autocomplete – validuje proti databázi, ne proti ``choices``.

    Standardní ``ChoiceField`` ověřuje odeslanou hodnotu proti seznamu ``choices``, což by
    vynutilo načtení všech katastrů. Místo toho ověříme existenci jediného odeslaného ``pk``
    přímo v databázi (indexovaný dotaz).
    """

    def valid_value(self, value):
        """
        Ověří, že hodnota odpovídá existujícímu katastru.

        :param value: Odeslaný primární klíč katastru.

            :return: ``True``, pokud katastr s daným ``pk`` existuje.
        """
        return RuianKatastr.objects.filter(pk=value).exists()


def create_pes_form(not_readonly=True, model_typ=None):
    """
    Funkce která vrací formulář hlídacího psa pro formset.

    :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
    :param model_typ: Parametr ``model_typ`` slouží jako vstup pro logiku funkce ``create_pes_form``.

        :return: Vrací proměnná ``PesForm``.
    """

    class PesForm(forms.ModelForm):
        """Implementuje komponentu ``PesForm`` v rámci aplikace."""

        admin_app = False

        class Meta:
            """Implementuje komponentu ``Meta`` v rámci aplikace."""

            model = Pes
            fields = ["object_id"]

        def __init__(self, *args, **kwargs):
            """
            Inicializuje instanci třídy.

            :param args: Parametr ``args`` se předává do volání ``__init__()``.
            :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
            """
            super(PesForm, self).__init__(*args, **kwargs)
            self.model_typ = model_typ
            if model_typ == KRAJ_CONTENT_TYPE:
                choices = list(RuianKraj.objects.values_list("id", "nazev"))
                if self.instance.pk is None:
                    choices = [("", "")] + choices
                self.fields["object_id"] = forms.ChoiceField(
                    choices=choices,
                    label=_("notifikaceProjekty.forms.pesForm.kraj.label"),
                    help_text=_("notifikaceProjekty.forms.pesForm.kraj.tooltip"),
                    required=True,
                    widget=forms.Select(
                        attrs={
                            "class": "selectpicker",
                            "data-multiple-separator": "; ",
                            "data-live-search": "true",
                        }
                    ),
                )
            elif model_typ == OKRES_CONTENT_TYPE:
                okresy = RuianOkres.objects.select_related("kraj").order_by("kraj__nazev", "nazev")
                choices = [
                    (kraj_nazev, tuple((okres.pk, okres.nazev) for okres in skupina))
                    for kraj_nazev, skupina in groupby(okresy, key=lambda okres: okres.kraj.nazev)
                ]
                if self.instance.pk is None:
                    choices = [("", "")] + choices
                self.fields["object_id"] = forms.ChoiceField(
                    choices=choices,
                    label=_("notifikaceProjekty.forms.pesForm.okres.label"),
                    help_text=_("notifikaceProjekty.forms.pesForm.okres.tooltip"),
                    required=True,
                    widget=forms.Select(
                        attrs={
                            "class": "selectpicker",
                            "data-multiple-separator": "; ",
                            "data-live-search": "true",
                        }
                    ),
                )
            elif model_typ == KATASTR_CONTENT_TYPE:
                self.fields["object_id"] = KatastrAutocompleteChoiceField(
                    label=_("notifikaceProjekty.forms.pesForm.katastr.label"),
                    help_text=_("notifikaceProjekty.forms.pesForm.katastr.tooltip"),
                    widget=AutocompleteListSelect2(url="heslar:katastr-autocomplete"),
                    choices=build_katastr_label_choices(self.instance.object_id if self.instance.pk else None),
                    required=True,
                )
            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[key].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""

        def save(self, commit=True):
            """
            Uloží změny objektu.

            :param commit: Pokud ``True``, změny se uloží do databáze.

                :return: Vrací proměnná ``instance``.
            """
            instance = super(PesForm, self).save(commit=False)
            if self.admin_app:
                instance.suppress_signal = True
            try:
                instance.content_type
            except ContentType.DoesNotExist:
                instance.content_type = ContentType.objects.get(model=self.model_typ)
            if commit:
                instance.save()
            return instance

        def clean(self, *args, **kwargs):
            """
            Provádí operaci clean.

            :param args: Parametr ``args`` se předává do volání ``clean()``.
            :param kwargs: Parametr ``kwargs`` se předává do volání ``clean()``.

                :raises forms.ValidationError: Vyvolá se při splnění podmínky ``duplicates.exists()``.
            """
            super().clean(*args, **kwargs)
            object_id = self.cleaned_data.get("object_id")
            if object_id in (None, ""):
                return self.cleaned_data

            duplicates = Pes.objects.filter(
                object_id=object_id,
                content_type=ContentType.objects.get(model=self.model_typ),
                user=self.instance.user,
            )
            if self.instance.pk:  # pokud je instance už v databázi, je potřeba vyloučit sama sebe ze seznamu duplicit
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(_("notifikaceProjekty.forms.pesForm.stejnaJendotka.error"))

    return PesForm


class PesFormSetHelper(FormHelper):
    """Implementuje komponentu ``PesFormSetHelper`` v rámci aplikace."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "pes"


class PesNotificationsForm(forms.ModelForm):
    """Formulář pro správu typu notifikací."""

    notification_types = forms.ModelMultipleChoiceField(
        queryset=UserNotificationType.objects.filter(ident_cely__in=PES_NOTIFICATIONS),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("notifikaceProjekty.forms.PesNotificationsForm.notification_types.notification_types_label"),
        help_text=_("notifikaceProjekty.forms.PesNotificationsForm.notification_types.notification_types.tooltip"),
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ("notification_types",)

    def __init__(self, pes_object_count=0, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param pes_object_count: Parametr ``pes_object_count`` slouží jako vstup pro logiku funkce ``__init__``.
        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.pes_object_count = pes_object_count

    def clean(self):
        """
        Provádí operaci clean.

        :return: Vrací proměnná ``cleaned_data``.
        """
        cleaned_data = super().clean()
        if self.pes_object_count == 0 or not cleaned_data.get("notification_types"):
            self.add_error(
                "notification_types", _("notifikaceProjekty.forms.PesNotificationsForm.pes_object_count.error")
            )
        return cleaned_data


class PesInlineFormSet(forms.BaseInlineFormSet):
    """Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace."""

    def clean(self):
        """
        Ověří, že formset neobsahuje dvě shodné jednotky (stejné ``object_id``).

        Per-form ``clean`` kontroluje duplicity jen vůči databázi, takže dva nové
        shodné hlídací psy odeslané najednou by jinak prošly a druhý ``INSERT`` by
        spadl na unikátní omezení ``unique_pes`` (``user``, ``content_type``,
        ``object_id``). ``user`` ani ``content_type`` nejsou poli formuláře, proto
        je standardní ``validate_unique`` neumí ochránit.

        :raises forms.ValidationError: Vyvolá se při nalezení duplicitního ``object_id``.
        """
        super().clean()
        if any(self.errors):
            return
        seen_object_ids = set()
        for form in self.forms:
            if not getattr(form, "cleaned_data", None):
                continue
            if self.can_delete and self._should_delete_form(form):
                continue
            object_id = form.cleaned_data.get("object_id")
            if object_id in (None, ""):
                continue
            if object_id in seen_object_ids:
                raise forms.ValidationError(_("notifikaceProjekty.forms.pesForm.stejnaJendotka.error"))
            seen_object_ids.add(object_id)

    def count_non_empty_forms(self):
        """
        Provádí operaci count non empty forms.

        :return: Vrací proměnná ``non_empty_count``.
        """
        non_empty_count = 0
        for form in self.forms:
            if any(field_value for field_value in form.cleaned_data.values()):
                non_empty_count += 1
        return non_empty_count
