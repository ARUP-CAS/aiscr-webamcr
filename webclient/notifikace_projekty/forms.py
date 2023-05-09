import logging
from django import forms

from .models import Pes
from heslar.models import RuianKatastr, RuianKraj, RuianOkres
from django.contrib.contenttypes.models import ContentType
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from django.utils.translation import gettext_lazy as _
from dal import autocomplete
from crispy_forms.helper import FormHelper

logger = logging.getLogger(__name__)

KRAJ_CONTENT_TYPE = "ruiankraj"
OKRES_CONTENT_TYPE = "ruianokres"
KATASTR_CONTENT_TYPE = "ruiankatastr"
CONTENT_TYPES = [KRAJ_CONTENT_TYPE, OKRES_CONTENT_TYPE, KATASTR_CONTENT_TYPE]


def create_pes_form(not_readonly=True, model_typ=None):
    """
    Funkce která vrací formulář hlídacího psa pro formset.
    """
    class PesForm(forms.ModelForm):
        class Meta:
            model = Pes
            fields = ["object_id"]

        def __init__(self, *args, **kwargs):
            super(PesForm, self).__init__(*args, **kwargs)
            self.model_typ = model_typ
            if model_typ == KRAJ_CONTENT_TYPE:
                self.fields["object_id"] = forms.ChoiceField(
                    choices=[("", "")]
                    + list(RuianKraj.objects.all().values_list("id", "nazev")),
                    label=_("notifikaceProjekty.form.kraj.label"),
                    help_text=_("notifikaceProjekty.form.kraj.tooltip"),
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
                    label=_("notifikaceProjekty.form.okres.label"),
                    help_text=_("notifikaceProjekty.form.okres.tooltip"),
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
                    label=_("notifikaceProjekty.form.katastr.label"),
                    help_text=_("notifikaceProjekty.form.katastr.tooltip"),
                    widget=autocomplete.ListSelect2(url="heslar:katastr-autocomplete"),
                    choices=katastre_choices,
                    required=True,
                )
            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""

        def save(self, commit=True):
            instance = super(PesForm, self).save(commit=False)
            try:
                instance.content_type
            except ContentType.DoesNotExist:
                instance.content_type = ContentType.objects.get(model=self.model_typ)
            if commit:
                instance.save()
            return instance

        def clean(self, *args, **kwargs):
            super().clean(*args, **kwargs)
            # Get the values and check duplicates

            # Find the duplicates
            duplicates = Pes.objects.filter(
                object_id=self.cleaned_data["object_id"],
                content_type=ContentType.objects.get(model=self.model_typ),
                user=self.instance.user,
            )
            if (
                self.instance.pk
            ):  # if the instance is already in the database, make sure to exclude self from list of duplicates
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    _("notifikaceProjekty.form.stejnaJendotka.error")
                )

    return PesForm


class PesFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "pes"