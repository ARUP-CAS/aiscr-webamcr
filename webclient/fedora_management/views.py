import logging

from core.connectors import RedisConnector
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.utils.translation import gettext as _
from django.views import View
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class AdminRecordProcessingView(LoginRequiredMixin, View):
    """Implementuje komponentu ``AdminRecordProcessingView`` v rámci aplikace."""

    def process_record(self, record, result, **kwargs):
        """
        Provádí operaci process record.

        :param record: Parametr ``record`` slouží jako vstup pro logiku funkce ``process_record``.
        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``process_record``.
        """
        pass

    def get(self, request, **kwargs):
        """
        Vrací výsledek operace.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``process_record()``, pracuje se s atributy ``get``.

            :return: Vrací výsledek volání ``JsonResponse()``.
        """
        r = RedisConnector().get_connection()
        job_id = kwargs.get("job_id")
        job_data = r.get(job_id).decode("utf-8")
        if job_data:
            iterator, *ident_list = job_data.split(";")
            iterator = int(iterator)
            item_count = len(ident_list)
            result = {
                "progress": (iterator + 1) / item_count * 100,
                "remaining": len(ident_list) - iterator,
                "detail": None,
            }
            if len(ident_list) > iterator:
                ident_cely = ident_list[iterator]
                result["ident_cely"] = ident_cely
                r.set(job_id, f"{str(iterator + 1)};{';'.join(ident_list)}")
                try:
                    record = get_record_from_ident(ident_cely)
                except Http404 as err:
                    record = None
                    logger.debug(
                        "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload" ".not_found",
                        extra={"ident_cely": ident_cely, "error": err},
                    )
                if record:
                    result = self.process_record(record, result, **kwargs)
                else:
                    result["result"] = _(
                        "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.record_not_found"
                    )
            return JsonResponse(result)


class ContinueMedataProcessing(AdminRecordProcessingView):
    """Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace."""

    def process_record(self, record, result, **kwargs):
        """
        Provádí operaci process record.

        :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``debug()``, pracuje se s atributy ``save_metadata``, ``ident_cely``, ovlivňuje větvení podmínek.
        :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``process_record``.

            :return: Vrací proměnná ``result``.
        """
        if record and isinstance(record, ModelWithMetadata) or isinstance(record, User):
            try:
                fedora_transaction = FedoraTransaction()
                result["detail"] = fedora_transaction.uid
                record.save_metadata(fedora_transaction)
                fedora_transaction.mark_transaction_as_closed()
                result["result"] = _("fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.success")
            except FedoraError as err:
                result["result"] = _("fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.error")
                logger.debug(
                    "fedora_management.admin.FedoraCustomAdminSite.fedora_error" ".not_found",
                    extra={"ident_cely": record.ident_cely, "error": err},
                )
        else:
            result["result"] = _(
                "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.does_not_exist"
            )
        return result
