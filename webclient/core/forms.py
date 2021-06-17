from django import forms
from django.utils.translation import gettext as _
from heslar.models import Heslar


class TwoLevelSelectField(forms.CharField):
    def to_python(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None


class HeslarChoiceFieldField(forms.ChoiceField):
    def clean(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None


class VratitForm(forms.Form):
    reason = forms.CharField(label=_("Zdůvodnění vrácení"), required=True)
