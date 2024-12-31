from django import forms
from django.utils.translation import gettext as _


class UpdateDocumentObjectIdentifierFileForm(forms.Form):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
