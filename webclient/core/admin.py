from django.contrib import admin
from core.models import OdstavkaSystemu
from .forms import OdstavkaSystemuForm
from polib import pofile
from django.conf import settings
import logging
import os
from datetime import datetime, date
from bs4 import BeautifulSoup
from django.core.cache import cache
from core.constants import ROLE_NASTAVENI_ODSTAVKY
from django.core.cache.utils import make_template_fragment_key

logger = logging.getLogger(__name__)


class OdstavkaSystemuAdmin(admin.ModelAdmin):
    list_display = (
        "info_od",
        "datum_odstavky",
        "cas_odstavky",
        "status",
    )
    form = OdstavkaSystemuForm

    def save_model(self, request, obj, form, change):
        locale_path = settings.LOCALE_PATHS[0]
        languages = settings.LANGUAGES
        for code, lang in languages:
            path = locale_path + "/" + code + "/LC_MESSAGES/django.po"
            po_file = pofile(path)
            entry = po_file.find("base.odstavka.text")
            text = "text_" + code
            entry.msgstr = form.cleaned_data[text]
            po_file.save()
            po_filepath, ext = os.path.splitext(path)
            po_file.save_as_mofile(po_filepath + ".mo")
            self.file_handler(code, form)
        cache.delete("last_maintenance")
        cache.delete(make_template_fragment_key("maintenance"))
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_delete_permission(self, request, obj=None, *args):
        if request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() == 0:
            return False
        odstavka = OdstavkaSystemu.objects.filter(
            info_od__lte=datetime.today(), datum_odstavky__gte=datetime.today()
        )
        if odstavka:
            if odstavka[0].datum_odstavky != date.today():
                return True
            elif odstavka[0].cas_odstavky > datetime.now().time():
                return True
        return False

    def has_view_permission(self, request, obj=None, *args):
        if request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() == 0:
            return False
        return super().has_view_permission(request, obj, *args)

    def has_add_permission(self, request, *args):
        if request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() == 0:
            return False
        return super().has_add_permission(request, *args)

    def has_change_permission(self, request, obj=None, *args):
        if request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() == 0:
            return False
        return super().has_change_permission(request, obj, *args)

    def file_handler(self, language, form):
        with open("/vol/web/nginx/data/" + language + "/custom_50x.html") as fp:
            soup = BeautifulSoup(fp)
            soup.find("h1").string.replace_with(
                form.cleaned_data["error_text_" + language]
            )
        with open("/vol/web/nginx/data/" + language + "/custom_50x.html", "w") as fp:
            fp.write(str(soup))
        with open(
            "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html"
        ) as fp:
            soup = BeautifulSoup(fp)
            soup.find("h1").string.replace_with(
                form.cleaned_data["error_text_oznam_" + language]
            )
        with open(
            "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html", "w"
        ) as fp:
            fp.write(str(soup))


admin.site.register(OdstavkaSystemu, OdstavkaSystemuAdmin)
