from django import forms
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
