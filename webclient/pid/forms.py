from django import forms
from django.utils.translation import gettext as _


class FormWithOrcid:
    """Zapouzdřuje chování třídy ``FormWithOrcid`` pro modul ``webclient.pid.forms``."""
    def clean_orcid(self):
        """Zajišťuje logiku funkce ``clean_orcid``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        data = self.cleaned_data["orcid"]
        return "https://orcid.org/" + data if len(data) > 0 else None


class FormWithWikidata:
    """Zapouzdřuje chování třídy ``FormWithWikidata`` pro modul ``webclient.pid.forms``."""
    def clean_wikidata(self):
        """Zajišťuje logiku funkce ``clean_wikidata``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        data = self.cleaned_data["wikidata"]
        return "https://www.wikidata.org/entity/" + data if len(data) > 0 else None


class UpdateDocumentObjectIdentifierFileForm(forms.Form):
    """Zapouzdřuje chování třídy ``UpdateDocumentObjectIdentifierFileForm`` pro modul ``webclient.pid.forms``."""
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
