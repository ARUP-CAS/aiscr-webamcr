from django.contrib import admin
from django import forms
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from .models import KonkretniOpravneni, Opravneni
from django.contrib.admin.utils import (
    flatten_fieldsets,
    unquote,
)
from django.forms.formsets import all_valid
from django.contrib.admin import helpers
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext as _

IS_POPUP_VAR = "_popup"
TO_FIELD_VAR = "_to_field"


HORIZONTAL, VERTICAL = 1, 2


class KonkretniOpravneniForm(forms.ModelForm):
    class Meta:
        model = KonkretniOpravneni
        fields = [
            "id",
            "druh_opravneni",
            "porovnani_stavu",
            "stav",
            "vazba_na_konkretni_opravneni",
        ]

    def __init__(self, *args, **kwargs):
        super(KonkretniOpravneniForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["vazba_na_konkretni_opravneni"].queryset = self.fields[
                "vazba_na_konkretni_opravneni"
            ].queryset.exclude(pk=self.instance.pk)

    def clean(self):
        cleaned_data = super().clean()
        druh_opravneni = cleaned_data.get("druh_opravneni")
        porovnani_stavu = cleaned_data.get("porovnani_stavu")
        stav = cleaned_data.get("stav")

        if druh_opravneni == "Stav":
            if stav is None:
                self.add_error(
                    "stav", "Pole musi byt vyplneno pokud je vybran druh opravneni STAV"
                )
            if porovnani_stavu is None:
                self.add_error(
                    "porovnani_stavu",
                    "Pole musi byt vyplneno pokud je vybran druh opravneni STAV",
                )
        if druh_opravneni != "Stav":
            if stav is not None:
                self.add_error(
                    "stav",
                    "Pole muze byt vyplneno jen pokud je vybran druh opravneni STAV",
                )
            if porovnani_stavu is not None:
                self.add_error(
                    "porovnani_stavu",
                    "Pole muze byt vyplneno jen pokud je vybran druh opravneni STAV",
                )


class OpravneniInline(admin.TabularInline):
    model = KonkretniOpravneni
    form = KonkretniOpravneniForm
    readonly_fields = ("id",)
    extra = 1

    def get_field_queryset(self, db, db_field, request):
        if db_field.name == "vazba_na_konkretni_opravneni":
            if request.resolver_match.kwargs.get("object_id"):
                return KonkretniOpravneni.objects.filter(
                    parent_opravneni_id=request.resolver_match.kwargs["object_id"],
                    vazba_na_konkretni_opravneni__isnull=True,
                )
        super(admin.TabularInline, self).get_field_queryset(db, db_field, request)


class OpravneniAdmin(admin.ModelAdmin):
    list_display = ("id", "aplikace", "adresa_v_aplikaci", "hlavni_role")
    inlines = [OpravneniInline]


admin.site.register(Opravneni, OpravneniAdmin)
