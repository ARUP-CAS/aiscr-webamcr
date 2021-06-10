from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.gis.forms import GeometryField, HiddenInput
from django.utils.translation import gettext as _
from pian.models import Pian


class PianCreateForm(forms.ModelForm):

    geom = GeometryField(required=True, widget=HiddenInput())

    class Meta:
        model = Pian
        fields = ("presnost", "geom")
        labels = {"presnost": _("Přesnost")}

    def __init__(self, *args, **kwargs):
        super(PianCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
