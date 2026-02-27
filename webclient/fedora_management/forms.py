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
        """Provádí funkci ``UpdateMetadataFileForm.__init__`` v rámci modulu ``webclient.fedora_management.forms``."""
        super().__init__(*args, **kwargs)
