import logging

from core.connectors import RedisConnector
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class ContinueMedataProcessing(LoginRequiredMixin, View):
    def get(self, request, job_id):
        r = RedisConnector().get_connection()
        ident_list = r.get(job_id).decode("utf-8")
        if ident_list:
            ident_list = ident_list.split(";")
            result = {"ident_count": len(ident_list), "transaction_id": None}
            if len(ident_list) > 0:
                ident_cely = ident_list[0]
                result["ident_cely"] = ident_cely
                r.set(job_id, ";".join(ident_list[1:]))
                try:
                    record = get_record_from_ident(ident_cely)
                except Http404 as err:
                    record = None
                    logger.debug(
                        "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload" ".not_found",
                        extra={"ident_cely": ident_cely, "err": err},
                    )
                    result["result"] = _(
                        "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.record_not_found"
                    )
                if record and isinstance(record, ModelWithMetadata) or isinstance(record, User):
                    try:
                        fedora_transaction = FedoraTransaction()
                        result["transaction_id"] = fedora_transaction.uid
                        record.save_metadata(fedora_transaction)
                        fedora_transaction.mark_transaction_as_closed()
                        result["result"] = _(
                            "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.success"
                        )
                    except FedoraError as err:
                        result["result"] = _(
                            "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.error"
                        )
                        logger.debug(
                            "fedora_management.admin.FedoraCustomAdminSite.fedora_error" ".not_found",
                            extra={"ident_cely": ident_cely, "err": err},
                        )
                else:
                    result["result"] = _(
                        "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.does_not_exist"
                    )
            return JsonResponse(result)
