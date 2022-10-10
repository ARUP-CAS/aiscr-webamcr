from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.gis.forms import HiddenInput
from django.utils.translation import gettext as _
from pian.models import Pian


class PianCreateForm(forms.ModelForm):

    # geom = GeometryField(srid=4326, required=True, widget=HiddenInput())
    # geom_sjtsk = GeometryField(srid=5514, required=True, widget=HiddenInput())

    class Meta:
        model = Pian
        fields = ("presnost", "geom", "geom_sjtsk", "geom_system")
        labels = {"presnost": _("Přesnost")}
        help_texts = {
            "presnost": _("pian.form.presnost.tooltip"),
        }
        widgets = {
            "geom": HiddenInput(),
            "geom_sjtsk": HiddenInput(),
            "geom_system": HiddenInput(),
            "presnost": forms.Select(attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"})
        }

    def __init__(self, *args, **kwargs):
        super(PianCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.fields["geom_system"].initial = "wgs84"
