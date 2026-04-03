from django import forms
from django.utils.translation import gettext as _


class FormWithOrcid:
    """Implementuje komponentu ``FormWithOrcid`` v rámci aplikace."""

    def clean_orcid(self):
        """
        Doplní k zadanému ORCID identifikátoru prefix URL ``https://orcid.org/`` a vrátí jej, nebo ``None`` pro prázdný vstup.

        :return: Vrací hodnotu podle větve zpracování.
        """
        data = self.cleaned_data["orcid"]
        return "https://orcid.org/" + data if len(data) > 0 else None


class FormWithWikidata:
    """Implementuje komponentu ``FormWithWikidata`` v rámci aplikace."""

    def clean_wikidata(self):
        """
        Doplní k zadanému identifikátoru Wikidata prefix URL ``https://www.wikidata.org/entity/`` a vrátí jej, nebo ``None`` pro prázdný vstup.

        :return: Vrací hodnotu podle větve zpracování.
        """
        data = self.cleaned_data["wikidata"]
        return "https://www.wikidata.org/entity/" + data if len(data) > 0 else None


class UpdateDocumentObjectIdentifierFileForm(forms.Form):
    """Implementuje komponentu ``UpdateDocumentObjectIdentifierFileForm`` v rámci aplikace."""

    ident_list_file = forms.FileField(
        required=True,
        label=_("core.forms.UpdateDocumentObjectIdentifierFileForm.file.label"),
        widget=forms.FileInput(
            attrs={
                "accept": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, "
                    "application/vnd.ms-excel, text/csv"
                )
            }
        ),
    )
    performed_action = forms.CharField(
        required=True,
        label=_("core.forms.UpdateDocumentObjectIdentifierFileForm.action.label"),
        widget=forms.Select(
            choices=[
                ("post_publish", _("core.forms.UpdateDocumentObjectIdentifierFileForm.post_publish")),
                ("put_publish", _("core.forms.UpdateDocumentObjectIdentifierFileForm.put_publish")),
                ("hide", _("core.forms.UpdateDocumentObjectIdentifierFileForm.hide")),
                ("update", _("core.forms.UpdateDocumentObjectIdentifierFileForm.update")),
            ]
        ),
    )
