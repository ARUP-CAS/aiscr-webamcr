from django import forms
from django.utils.translation import gettext_lazy as _


class UpdateMetadataFileForm(forms.Form):
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
        super().__init__(*args, **kwargs)
