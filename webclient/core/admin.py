from pkgutil import extend_path
from django.contrib import admin
from core.models import OdstavkaSystemu
from .forms import OdstavkaSystemuForm
from polib import pofile
from django.conf import settings
import logging
import os
from datetime import datetime, date
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OdstavkaSystemuAdmin(admin.ModelAdmin):
    list_display = ("info_od", "datum_odstavky", "cas_odstavky", "text_cs", "text_en")
    form = OdstavkaSystemuForm

    def save_model(self, request, obj, form, change):
        locale_path = settings.LOCALE_PATHS[0]
        languages = settings.LANGUAGES
        for code, lang in languages:
            path = locale_path + "/" + code + "/LC_MESSAGES/django.po"
            po_file = pofile(path)
            entry = po_file.find("base.odstavka.text")
            text = "text_" + code
            entry.msgstr = getattr(obj, text)
            po_file.save()
            po_filepath, ext = os.path.splitext(path)
            po_file.save_as_mofile(po_filepath + ".mo")
            self.file_handler(code, form)

        super().save_model(request, obj, form, change)

    def has_add_permission(*args, **kwargs):
        odstavka = OdstavkaSystemu.objects.filter(
            info_od__lte=datetime.today(), datum_odstavky__gte=datetime.today()
        )
        if odstavka:
            if odstavka[0].datum_odstavky != date.today():
                return False
            elif odstavka[0].cas_odstavky > datetime.now().time():
                return False
        return True

    def has_delete_permission(request, obj=None, *args):
        odstavka = OdstavkaSystemu.objects.filter(
            info_od__lte=datetime.today(), datum_odstavky__gte=datetime.today()
        )
        if odstavka:
            if odstavka[0].datum_odstavky != date.today():
                return True
            elif odstavka[0].cas_odstavky > datetime.now().time():
                return True
        return False

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
                form.cleaned_data["error_text_oznam" + language]
            )
        with open(
            "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html", "w"
        ) as fp:
            fp.write(str(soup))


admin.site.register(OdstavkaSystemu, OdstavkaSystemuAdmin)
