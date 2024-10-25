# Register your models here.
import pandas as pd
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext as _
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
                if uploaded_file.content_type == "text/csv":
                    sheet = pd.read_csv(uploaded_file, sep=",")
                else:
                    sheet = pd.read_excel(uploaded_file)
                sheet.columns = [
                    "ident_cely",
                ]
                sheet = sheet.set_index("ident_cely")
                sheet["result"] = ""
                sheet["detail"] = ""
                for ident_cely in sheet.index:
                    record = get_record_from_ident(ident_cely)
                    if record and isinstance(record, ModelWithMetadata):
                        try:
                            fedora_transaction = FedoraTransaction()
                            record.save_metadata(fedora_transaction)
                            fedora_transaction.mark_transaction_as_closed()
                            sheet["result"] = _("fedora_management.admin.YourCustomAdminSite.custom_page.success")
                            sheet["detail"] = fedora_transaction.uid
                        except FedoraError as e:
                            sheet["result"] = _("fedora_management.admin.YourCustomAdminSite.custom_page.error")
                            sheet["detail"] = e
                    else:
                        sheet.loc[ident_cely, "result"] = sheet["result"] = _(
                            "fedora_management.admin.YourCustomAdminSite.custom_page.does_not_exist"
                        )
                sheet = sheet.reset_index(drop=False)
                context = {
                    "text": sheet.to_html(index=False),
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
