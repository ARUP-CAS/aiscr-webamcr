import logging
import structlog

from django import forms
from crispy_forms.helper import FormHelper
from django.utils.translation import gettext as _
from heslar.models import Heslar

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


class TwoLevelSelectField(forms.CharField):
    def to_python(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class HeslarChoiceFieldField(forms.ChoiceField):
    def clean(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return super().clean(selected_value)

    def to_python(self, selected_value):
        if selected_value:
            return Heslar.objects.get(pk=int(selected_value))
        else:
            return None

    def has_changed(self, initial, data) -> bool:
        if initial is not None:
            initial = Heslar.objects.get(pk=int(initial))
        return super().has_changed(initial, data)


class CheckStavNotChangedForm(forms.Form):
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, db_stav= None, *args, **kwargs):
        self.db_stav=db_stav
        super(CheckStavNotChangedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        old_stav = self.cleaned_data.get("old_stav")
        if str(self.db_stav) != str(old_stav):
            logger_s.debug("CheckStavNotChangedForm.clean.ValidationError",
                         message="Stav zaznamu se zmenil mezi posunutim stavu.", db_stav=self.db_stav,
                         old_stav=old_stav)
            raise forms.ValidationError("State_changed")
        return cleaned_data


class VratitForm(forms.Form):
    reason = forms.CharField(label=_("Zdůvodnění vrácení"), required=True, help_text= _("core.forms.vratit.tooltip"))
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())
