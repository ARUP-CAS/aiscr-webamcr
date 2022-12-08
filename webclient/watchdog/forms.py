from django import forms
from .models import Watchdog
from heslar.models import RuianKraj, RuianOkres
from django.utils.translation import gettext_lazy as _
from dal.widgets import Select
from django_select2.forms import Select2Widget


class WatchdogCreateForm(forms.Form):
    kraje = RuianKraj.objects.all()
    okresy_choices = [
        (0, '----')
    ]
    kraje_choices = [
        (0, '----'),
    ]
    for kraj in kraje:
        kraje_choices.append((kraj.id, kraj.nazev))
        kraj_group = []
        okresy = RuianOkres.objects.filter(kraj=kraj)
        for okres in okresy:
            kraj_group.append((okres.pk, okres.nazev))
        kraj_group = (kraj.nazev, tuple(kraj_group))
        okresy_choices.append(kraj_group)
    kraj = forms.ChoiceField(choices=kraje_choices, label=_('Kraj'), required=False, widget=Select2Widget, initial=0)
    okres = forms.ChoiceField(choices=okresy_choices, label=_('Okres'), required=False, widget=Select2Widget, initial=0)

    # this function will be used for the validation
    def clean(self):
        super(WatchdogCreateForm, self).clean()
        kraj = self.cleaned_data.get('kraj')
        okres = self.cleaned_data.get('okres')
        if (int(kraj) > 0 and int(okres) > 0):
            self._errors['kraj'] = self.error_class([_('Vyberte kraj nebo okres, ne dva najednou')])
        return self.cleaned_data
