import logging

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


def create_pes_form(not_readonly=True, model_typ=None):
    """
    Funkce která vrací formulář hlídacího psa pro formset.

    :param not_readonly: Popis parametru ``not_readonly``.
    :param model_typ: Popis parametru ``model_typ``.
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

            :param args: Dodatečné poziční argumenty předané voláním.
            :param kwargs: Dodatečné pojmenované argumenty předané voláním.
            """
            super(PesForm, self).__init__(*args, **kwargs)
            self.model_typ = model_typ
            if model_typ == KRAJ_CONTENT_TYPE:
                if self.instance.pk is not None:
                    new_choices = list(RuianKraj.objects.all().values_list("id", "nazev"))
                else:
                    new_choices = [("", "")] + list(RuianKraj.objects.all().values_list("id", "nazev"))
                self.fields["object_id"] = forms.ChoiceField(
                    choices=new_choices,
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
                if self.instance.pk is not None:
                    okresy_choices = []
                else:
                    okresy_choices = [("", "")]
                kraje = RuianKraj.objects.all()
                for kraj in kraje:
                    kraj_group = []
                    okresy = RuianOkres.objects.filter(kraj=kraj)
                    for okres in okresy:
                        kraj_group.append((okres.pk, okres.nazev))
                    kraj_group = (kraj.nazev, tuple(kraj_group))
                    okresy_choices.append(kraj_group)
                self.fields["object_id"] = forms.ChoiceField(
                    choices=okresy_choices,
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
                katastre_choices = RuianKatastr.objects.annotate(
                    full_name=Concat(
                        "nazev",
                        Value(" ("),
                        "okres__nazev",
                        Value(")"),
                        output_field=CharField(),
                    )
                ).values_list("pk", "full_name")
                self.fields["object_id"] = forms.ChoiceField(
                    label=_("notifikaceProjekty.forms.pesForm.katastr.label"),
                    help_text=_("notifikaceProjekty.forms.pesForm.katastr.tooltip"),
                    widget=AutocompleteListSelect2(url="heslar:katastr-autocomplete"),
                    choices=katastre_choices,
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

            :param commit: Vstupní hodnota ``commit`` pro danou operaci.
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

            :param args: Dodatečné poziční argumenty předané voláním.
            :param kwargs: Dodatečné pojmenované argumenty předané voláním.
            """
            super().clean(*args, **kwargs)
            # Načte hodnoty a zkontroluje duplicity.

            # Najde duplicitní záznamy.
            duplicates = Pes.objects.filter(
                object_id=self.cleaned_data["object_id"],
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

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
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

        :param pes_object_count: Vstupní hodnota ``pes_object_count`` pro danou operaci.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.pes_object_count = pes_object_count

    def clean(self):
        """Provádí operaci clean."""
        cleaned_data = super().clean()
        if self.pes_object_count == 0 or not cleaned_data.get("notification_types"):
            self.add_error(
                "notification_types", _("notifikaceProjekty.forms.PesNotificationsForm.pes_object_count.error")
            )
        return cleaned_data


class PesInlineFormSet(forms.BaseInlineFormSet):
    """Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace."""

    def count_non_empty_forms(self):
        """Provádí operaci count non empty forms."""
        non_empty_count = 0
        for form in self.forms:
            if any(field_value for field_value in form.cleaned_data.values()):
                non_empty_count += 1
        return non_empty_count
