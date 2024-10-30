from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext_lazy as _


class UpdateMetadataFileForm(forms.Form):
    ident_list_file = forms.FileField(
        required=True,
        label=_("core.forms.permissionImport.file.label"),
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
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    "ident_list_file",
                    css_class="col-sm-12",
                ),
                css_class="row",
            ),
        )
