import logging

from arch_z.models import Akce, ArcheologickyZaznam
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django import forms
from django.db.models import Q
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_DJ_TYP, TYP_DJ_KATASTR, TYP_DJ_SONDA_ID, TYP_DJ_CAST, TYP_DJ_CELEK, TYP_DJ_LOKALITA
from heslar.models import Heslar, RuianKatastr

logger = logging.getLogger('python-logstash-logger')


class MyAutocompleteWidget(autocomplete.ModelSelect2):
    def media(self):
        return ()


class CreateDJForm(forms.ModelForm):
    ku_change = forms.CharField(
        max_length=50, required=False, widget=forms.HiddenInput()
    )
    pian_text = forms.CharField(
        max_length=100,
        required=False,
        disabled=True,
        label=_("PIAN"),
    )

    def get_typ_queryset(
        self,
        jednotky,
        instance: DokumentacniJednotka = None,
        typ_arch_z=None,
        typ_akce=None,
    ):
        queryset = Heslar.objects.filter(nazev_heslare=HESLAR_DJ_TYP)
        if typ_arch_z == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
            return queryset.filter(id__in=[TYP_DJ_LOKALITA,TYP_DJ_KATASTR])
        if (
            instance is not None
            and jednotky is not None
            and hasattr(instance, "typ")
            and instance.typ is not None
            and instance.typ.id == TYP_DJ_CAST
        ):
            queryset = queryset.filter(id=TYP_DJ_CAST)
        elif jednotky is not None:
            if jednotky.filter(typ__id=TYP_DJ_SONDA_ID).count() > 0:
                if not instance.ident_cely:
                    queryset = queryset.filter(id=TYP_DJ_SONDA_ID)
                elif (
                    jednotky.filter(
                        Q(typ__id=TYP_DJ_SONDA_ID)
                        & Q(ident_cely__lt=instance.ident_cely)
                    ).count()
                    > 0
                ) or jednotky.exclude(adb__isnull=True).count() > 0:
                    queryset = queryset.filter(id=TYP_DJ_SONDA_ID)
                elif jednotky.filter(typ__id=TYP_DJ_SONDA_ID).count() > 1:
                    queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID])
                elif typ_akce == Akce.TYP_AKCE_SAMOSTATNA:
                    queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID,TYP_DJ_KATASTR])
                else:
                    queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID])
            elif hasattr(instance, "typ") and instance.typ.id == TYP_DJ_CELEK:
                if typ_akce == Akce.TYP_AKCE_SAMOSTATNA and jednotky.filter(typ__id=TYP_DJ_CAST).count() == 0:
                    queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID,TYP_DJ_KATASTR])
                else:
                    queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID])
            elif hasattr(instance, "typ") and instance.typ == Heslar.objects.get(
                id=TYP_DJ_KATASTR
            ):
                queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID,TYP_DJ_KATASTR])
            elif jednotky.filter(typ__id=TYP_DJ_CELEK).count() > 0:
                queryset = queryset.filter(id=TYP_DJ_CAST)
            elif typ_akce == Akce.TYP_AKCE_SAMOSTATNA:
                queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID,TYP_DJ_KATASTR])
            else:
                queryset = queryset.filter(id__in=[TYP_DJ_CELEK, TYP_DJ_SONDA_ID])
        return queryset

    class Meta:
        model = DokumentacniJednotka
        fields = ("typ", "negativni_jednotka", "nazev", "pian")

        labels = {
            "typ": _("Typ"),
            "negativni_jednotka": _("Negativni jednotka"),
            "nazev": _("Název"),
            "pian": _("PIAN"),
        }

        widgets = {
            "typ": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            "nazev": forms.TextInput(),
            "pian": MyAutocompleteWidget(
                url="pian:pian-autocomplete",
            ),
            "negativni_jednotka": forms.Select(
                choices=[("False", _("Ne")), ("True", _("Ano"))],
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
        }
        help_texts = {
            "typ": _("dj.form.typ.tooltip"),
            "negativni_jednotka": _("dj.form.negativni_jednotka.tooltip"),
            "nazev": _("dj.form.nazev.tooltip"),
            "pian": _("dj.form.pian.tooltip"),
            "pian_text": _("dj.form.pian.tooltip"),
        }

    def __init__(
        self,
        *args,
        not_readonly=True,
        typ_arch_z=None,
        typ_akce=None,
        **kwargs,
    ):
        jednotky = kwargs.pop("jednotky", None)
        super(CreateDJForm, self).__init__(*args, **kwargs)
        if self.instance.ident_cely and typ_akce is None:
            try:
                typ_akce = self.instance.archeologicky_zaznam.akce.typ
            except Exception as e:
                pass
        self.fields["typ"] = forms.ModelChoiceField(
            queryset=self.get_typ_queryset(
                jednotky, self.instance, typ_arch_z, typ_akce
            ),
            help_text=_("dj.form.typ.tooltip"),
            widget=forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
        )
        if self.instance:
            self.fields["pian_text"].initial = self.instance.pian
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("typ", css_class="col-sm-2"),
                Div(
                    "pian", css_class="col-sm-2", style="display:none", id="pian_select"
                ),
                Div("pian_text", css_class="col-sm-2", id="pian_text"),
                Div("nazev", css_class="col-sm-4"),
                Div("negativni_jednotka", css_class="col-sm-2"),
                Div("ku_change", id="id_ku_change", css_class="hidden"),
                css_class="row",
            ),
        )
        self.fields["pian"].widget.attrs["disabled"] = "disabled"
        self.fields["pian"].widget.attrs["class"] = (
            self.fields["pian"].widget.attrs.get("class", "") + " pian_disabled"
        )
        self.fields["typ"].widget.attrs["id"] = "dj_typ_id"
        for key in self.fields.keys():
            self.fields[key].disabled = not not_readonly
            if (
                isinstance(self.fields[key].widget, forms.widgets.Select)
                and key != "pian"
            ):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
        self.fields["pian_text"].disabled = True


class ChangeKatastrForm(forms.Form):
    katastr = forms.ModelChoiceField(
        label=_("dj.form.katastrChange.label"),
        widget=autocomplete.ModelSelect2(url="heslar:katastr-autocomplete"),
        queryset=RuianKatastr.objects.all(),
        help_text=_("dj.form.katastrChange.tooltip"),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(ChangeKatastrForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
