from django import forms
from django.utils.translation import gettext_lazy as _


class UpdateMetadataFileForm(forms.Form):
    """Zapouzdřuje chování třídy ``UpdateMetadataFileForm`` pro modul ``webclient.fedora_management.forms``."""
    ident_list_file = forms.FileField(
        required=True,
        label=_("core.forms.UpdateMetadataFileForm.file.label"),
        widget=forms.FileInput(
            attrs={
                "accept": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, "
                    "application/vnd.ms-excel, text/csv"
                )
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param args: Poziční argumenty předané voláním.
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(*args, **kwargs)
