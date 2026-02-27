from django import forms
from django.utils.translation import gettext_lazy as _


class UpdateMetadataFileForm(forms.Form):
    """Třída `UpdateMetadataFileForm` v modulu `webclient.fedora_management.forms`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
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
        """Funkce `UpdateMetadataFileForm.__init__` v modulu `webclient.fedora_management.forms`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param args: Vstupní hodnota používaná při zpracování.
        :param kwargs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__(*args, **kwargs)
