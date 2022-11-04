import logging

from arch_z.models import Akce, ArcheologickyZaznam
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django import forms
from django.db.models import Q
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_DJ_TYP, TYP_DJ_KATASTR
from heslar.models import Heslar

logger = logging.getLogger(__name__)


class MyAutocompleteWidget(autocomplete.ModelSelect2):
    def media(self):
        return ()


class CreateDJForm(forms.ModelForm):
    ku_change = forms.CharField(
        max_length=50, required=False, widget=forms.HiddenInput()
    )

    def get_typ_queryset(
        self,
        jednotky,
        instance: DokumentacniJednotka = None,
        typ_arch_z=None,
        typ_akce=None,
    ):
        queryset = Heslar.objects.filter(nazev_heslare=HESLAR_DJ_TYP)
        logger.debug(jednotky)
        if typ_arch_z == ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA:
            return queryset.filter(
                Q(heslo__iexact="lokalita") | Q(heslo__iexact="Katastrální území")
            )
        if (
            instance is not None
            and jednotky is not None
            and hasattr(instance, "typ")
            and instance.typ is not None
            and instance.typ.heslo.lower() == "část akce"
        ):
            queryset = queryset.filter(Q(heslo__iexact="část akce"))
        elif jednotky is not None:
            if jednotky.filter(typ__heslo__iexact="sonda").count() > 0:
                if instance.ident_cely is None:
                    queryset = queryset.filter(heslo__iexact="sonda")
                elif (
                    jednotky.filter(
                        Q(typ__heslo__iexact="sonda")
                        & Q(ident_cely__lt=instance.ident_cely)
                    ).count()
                    > 0
                ):
                    queryset = queryset.filter(heslo__iexact="sonda")
                elif jednotky.filter(typ__heslo__iexact="sonda").count() > 1:
                    queryset = queryset.filter(
                        Q(heslo__iexact="sonda") | Q(heslo__iexact="celek akce")
                    )
                else:
                    queryset = queryset.filter(
                        Q(heslo__iexact="sonda")
                        | Q(heslo__iexact="celek akce")
                        | Q(heslo__iexact="Katastrální území")
                    )
            elif hasattr(instance, "typ") and instance.typ.heslo == "Celek akce":
                if jednotky.filter(typ__heslo__iexact="část akce").count() > 0:
                    queryset = queryset.filter(
                        Q(heslo__iexact="sonda") | Q(heslo__iexact="celek akce")
                    )
                else:
                    queryset = queryset.filter(
                        Q(heslo__iexact="sonda")
                        | Q(heslo__iexact="celek akce")
                        | Q(heslo__iexact="Katastrální území")
                    )
            elif hasattr(instance, "typ") and instance.typ == Heslar.objects.get(
                id=TYP_DJ_KATASTR
            ):
                queryset = queryset.filter(
                    Q(heslo__iexact="sonda")
                    | Q(heslo__iexact="celek akce")
                    | Q(heslo__iexact="Katastrální území")
                )
            elif jednotky.filter(typ__heslo__iexact="část akce").count() > 0:
                if jednotky.filter(typ__heslo__iexact="celek akce").count() > 0:
                    queryset = queryset.filter(heslo__iexact="část akce")
                else:
                    queryset = queryset.filter(
                        Q(heslo__iexact="část akce") | Q(heslo__iexact="celek akce")
                    )
            elif jednotky.filter(typ__heslo__iexact="celek akce").count() > 0:
                queryset = queryset.filter(heslo__iexact="část akce")
            elif typ_akce == Akce.TYP_AKCE_SAMOSTATNA:
                queryset = queryset.filter(
                    Q(heslo__iexact="sonda")
                    | Q(heslo__iexact="celek akce")
                    | Q(heslo__iexact="Katastrální území")
                )
            else:
                queryset = queryset.filter(
                    Q(heslo__iexact="sonda") | Q(heslo__iexact="celek akce")
                )

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
            "pian": MyAutocompleteWidget(url="pian:pian-autocomplete"),
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
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("typ", css_class="col-sm-2"),
                Div("pian", css_class="col-sm-2"),
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
