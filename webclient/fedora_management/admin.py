import logging

import pandas as pd
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction
from django.contrib import admin
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext as _
from fedora_management.forms import UpdateMetadataFileForm
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class FedoraCustomAdminSite(admin.AdminSite):
    def update_metadata_file_upload(self, request):
        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST" and request.user.is_superuser:
            form = UpdateMetadataFileForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES["ident_list_file"]
                sheet = None
                if uploaded_file.content_type == "text/csv":
                    try:
                        sheet = pd.read_csv(uploaded_file, sep=",")
                    except Exception as err:
                        logger.debug(
                            "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload"
                            ".cannot_read_file",
                            extra={"err": err},
                        )
                        context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
                else:
                    try:
                        sheet = pd.read_excel(uploaded_file)
                    except Exception as err:
                        logger.debug(
                            "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload"
                            ".cannot_read_file",
                            extra={"err": err},
                        )
                        context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
                if sheet.shape[1] != 1:
                    context["error"] = _("fedora_management.admin.YourCustomAdminSite.too_many_columns")
                    sheet = None
                if isinstance(sheet, pd.DataFrame):
                    sheet.columns = [
                        "ident_cely",
                    ]
                    sheet["ident_cely"] = sheet["ident_cely"].str.strip()
                    sheet = sheet.set_index("ident_cely")
                    sheet["result"] = ""
                    sheet["detail"] = ""
                    for ident_cely in sheet.index.unique():
                        try:
                            record = get_record_from_ident(ident_cely)
                        except Http404 as err:
                            record = None
                            logger.debug(
                                "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload"
                                ".not_found",
                                extra={"ident_cely": ident_cely, "err": err},
                            )
                        if record and isinstance(record, ModelWithMetadata) or isinstance(record, User):
                            try:
                                fedora_transaction = FedoraTransaction()
                                record.save_metadata(fedora_transaction)
                                fedora_transaction.mark_transaction_as_closed()
                                sheet.loc[ident_cely, "result"] = _(
                                    "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.success"
                                )
                                sheet.loc[ident_cely, "detail"] = fedora_transaction.uid
                            except FedoraError as err:
                                sheet.loc[ident_cely, "result"] = _(
                                    "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.error"
                                )
                                logger.debug(
                                    "fedora_management.admin.FedoraCustomAdminSite.fedora_error" ".not_found",
                                    extra={"ident_cely": ident_cely, "err": err},
                                )
                        else:
                            sheet.loc[ident_cely, "result"] = _(
                                "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.does_not_exist"
                            )
                    sheet = sheet.reset_index(drop=False)
                    context.update(
                        {
                            "text": sheet.to_html(index=False),
                            "page_name": "Custom Page",
                            "app_list": self.get_app_list(request),
                            **self.each_context(request),
                        }
                    )
            context["form"] = form
        else:
            context["form"] = UpdateMetadataFileForm()
        return TemplateResponse(request, "admin/fedora_management/update_metadata.html", context)

    def get_urls(
        self,
    ):
        return [
            path(
                "update-metadata/",
                self.admin_view(self.update_metadata_file_upload),
                name="update_metadata",
            ),
        ] + super().get_urls()


admin.site.__class__ = FedoraCustomAdminSite
