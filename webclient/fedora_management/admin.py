# Register your models here.
import pandas as pd
from core.ident_cely import get_record_from_ident
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from fedora_management.forms import UpdateMetadataFileForm
from xml_generator.models import ModelWithMetadata


class YourCustomAdminSite(admin.AdminSite):
    def custom_page(self, request):
        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST":
            form = UpdateMetadataFileForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES["ident_list_file"]
                sheet = pd.read_csv(uploaded_file, sep=",")
                sheet.columns = [
                    "ident_cely",
                ]
                sheet = sheet.set_index("ident_cely")
                sheet["result"] = ""
                for ident_cely in sheet.index:
                    record = get_record_from_ident(ident_cely)
                    if record and isinstance(record, ModelWithMetadata):
                        record.save_metadata()
                    else:
                        sheet.loc[ident_cely, "result"] = "Record does not exist"
                context = {
                    "text": str(sheet),
                    "page_name": "Custom Page",
                    "app_list": self.get_app_list(request),
                    **self.each_context(request),
                }
            context["update_metadata_file_form"] = form
        else:
            context["update_metadata_file_form"] = UpdateMetadataFileForm()
        return TemplateResponse(request, "admin/fedora_management/update_metadata.html", context)

    def get_urls(
        self,
    ):
        return [
            path(
                "update-metadata/",
                self.admin_view(self.custom_page),
                name="update_metadata",
            ),
        ] + super().get_urls()


admin.site.__class__ = YourCustomAdminSite
