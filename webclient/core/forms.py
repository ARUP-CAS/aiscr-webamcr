import logging
import structlog

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django.utils.translation import gettext as _
from core.models import Soubor
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

    def __init__(self, *args, **kwargs):
        super(VratitForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class SouborMetadataForm(forms.ModelForm):
    nazev_zkraceny = forms.CharField()
    nazev_puvodni = forms.CharField()
    nazev = forms.CharField()
    mimetype = forms.CharField()
    size_bytes = forms.CharField()

    class Meta:
        model = Soubor
        fields = ("nazev_zkraceny", "nazev_puvodni", "rozsah", "nazev", "mimetype", "size_bytes")

    def __init__(self, *args, **kwargs):
        super(SouborMetadataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("nazev_zkraceny", css_class="col-sm-2"),
                Div("nazev_puvodni", css_class="col-sm-3"),
                Div("rozsah", css_class="col-sm-1"),
                Div("nazev", css_class="col-sm-2"),
                Div("mimetype", css_class="col-sm-2"),
                Div("size_bytes", css_class="col-sm-2"),
                css_class="row",
            ),
        )
        self.fields["nazev_zkraceny"].widget.attrs["readonly"] = True
        self.fields["nazev_puvodni"].widget.attrs["readonly"] = True
        self.fields["rozsah"].widget.attrs["readonly"] = True
        self.fields["nazev"].widget.attrs["readonly"] = True
        self.fields["mimetype"].widget.attrs["readonly"] = True
        self.fields["size_bytes"].widget.attrs["readonly"] = True
