import logging
import string

from core.connectors import RedisConnector
from core.ident_cely import get_record_from_ident
from core.repository_connector import FedoraError, FedoraTransaction, FedoraTransactionCommitFailedError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.utils.translation import gettext as _
from django.views import View
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)

#: Povolené znaky zbytku Redis klíče za prefixem (výstup ``secrets.token_urlsafe``).
_POVOLENE_ZNAKY_JOB_ID = set(string.ascii_letters + string.digits + "-_")


class AdminRecordProcessingView(LoginRequiredMixin, View):
    """
    Základ dávkového zpracování záznamů polovaného z administrace.

    Průběh drží Redis: pod klíčem ``job_id`` leží ``"<index>;<ident>;<ident>…"``
    a každé zavolání zpracuje jeden ident a index posune. JS na stránce průběhu
    volá endpoint dokola, dokud zbývají záznamy.

    Podtřída dodá :meth:`process_record`; protokol (čtení fronty, posun indexu,
    výpočet progresu, ošetření chyb) je společný, aby se opravy nemusely dělat
    na dvou místech.
    """

    #: Očekávaný prefix Redis klíče. Redis je sdílený s ostatními úlohami
    #: (``import_data_*``, ``update_pid_*``…), takže bez kontroly by šlo
    #: endpointu podstrčit cizí klíč a ``r.set`` níž by ho přepsal. ``None``
    #: kontrolu vypíná (podtřídy, které vlastní prefix nemají).
    job_id_prefix = None

    #: Expirace klíče při posunu indexu, v sekundách. ``None`` ji nemění.
    job_expirace = None

    #: Výjimky ze zpracování jednoho záznamu, které nesmí shodit celou dávku.
    #: ``FedoraTransactionCommitFailedError`` **není** potomek ``FedoraError``,
    #: takže bez explicitního uvedení by prošla ven jako HTTP 500 – a to až
    #: poté, co se index v Redis posunul, tedy s přeskočením zbytku fronty.
    zpracovani_chyby = (FedoraError, FedoraTransactionCommitFailedError, ValueError)

    def process_record(self, record, result, **kwargs):
        """
        Zpracuje jeden záznam v rámci dávkového zpracování metadat — přepisuje se v podtřídách.

        :param record: Instance záznamu ke zpracování.
        :param result: Slovník s výsledky průběhu zpracování.
        :param kwargs: Další parametry předané z pohledu.
        :return: Aktualizovaný slovník ``result``.
        """
        return result

    @classmethod
    def je_platny_job_id(cls, job_id: str) -> bool:
        """
        Ověří, že klíč patří do jmenného prostoru téhle úlohy.

        :param job_id: Identifikátor z URL.
        :return: ``True``, když prefix sedí nebo se kontrola nepoužívá.
        """
        if cls.job_id_prefix is None:
            return bool(job_id)
        if not job_id.startswith(cls.job_id_prefix):
            return False
        zbytek = job_id[len(cls.job_id_prefix) :]
        return bool(zbytek) and len(zbytek) <= 128 and set(zbytek) <= _POVOLENE_ZNAKY_JOB_ID

    def get(self, request, **kwargs):
        """
        Zpracuje další záznam ve frontě a vrátí JSON s progresem.

        :param request: HTTP GET požadavek.
        :param kwargs: Klíčové argumenty včetně ``job_id`` identifikujícího dávkovou úlohu v Redis.

            :return: ``JsonResponse`` se strukturou ``{progress, remaining, ident_cely, result, detail}``.
            :raises Http404: Když ``job_id`` nepatří do jmenného prostoru úlohy.
        """
        r = RedisConnector().get_connection()
        job_id = kwargs.get("job_id") or ""
        if not self.je_platny_job_id(job_id):
            logger.warning(
                "fedora_management.views.AdminRecordProcessingView.neplatny_job_id",
                extra={"job_id": job_id[:60]},
            )
            raise Http404("Neplatný identifikátor úlohy.")

        raw = r.get(job_id)
        if raw is None:
            # Klíč vypršel nebo byl smazán. Dřív se rovnou volalo ``.decode()``
            # a poll skončil AttributeError → HTTP 500.
            return JsonResponse({"progress": 100, "remaining": 0, "result": "expired"})

        iterator, *ident_list = raw.decode("utf-8").split(";")
        ident_list = [x for x in ident_list if x]
        try:
            iterator = int(iterator)
        except ValueError:
            logger.error(
                "fedora_management.views.AdminRecordProcessingView.poskozeny_job",
                extra={"job_id": job_id[:60]},
            )
            return JsonResponse({"progress": 100, "remaining": 0, "result": "expired"})

        # ``max(..., 1)``: prázdná fronta by jinak dělila nulou.
        item_count = max(len(ident_list), 1)
        result = {
            "progress": (iterator + 1) / item_count * 100,
            "remaining": len(ident_list) - iterator,
            "detail": None,
            "is_error": False,
        }
        if iterator >= len(ident_list):
            return JsonResponse(result)

        ident_cely = ident_list[iterator]
        result["ident_cely"] = ident_cely
        # Index se posouvá ještě před zpracováním záměrně: kdyby se posouval až
        # po úspěchu, jeden trvale padající záznam by frontu zablokoval. Cenou
        # je, že se selhání nezopakuje – proto musí být každá chyba odchycená
        # a vrácená jako ``is_error``, ne propadnout ven jako HTTP 500.
        if self.job_expirace is None:
            r.set(job_id, f"{iterator + 1};{';'.join(ident_list)}")
        else:
            r.set(job_id, f"{iterator + 1};{';'.join(ident_list)}", ex=self.job_expirace)

        try:
            record = get_record_from_ident(ident_cely)
        except Http404 as err:
            record = None
            logger.debug(
                "fedora_management.views.AdminRecordProcessingView.not_found",
                extra={"ident_cely": ident_cely, "error": err},
            )
        if record is None:
            result["result"] = _(
                "fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.record_not_found"
            )
            result["is_error"] = True
            return JsonResponse(result)

        try:
            result = self.process_record(record, result, **kwargs)
        except self.zpracovani_chyby as err:
            logger.error(
                "fedora_management.views.AdminRecordProcessingView.zpracovani_error",
                extra={"ident_cely": ident_cely, "error": str(err)[:500]},
            )
            result["result"] = _("fedora_management.admin.YourCustomAdminSite.update_metadata_file_upload.error")
            result["is_error"] = True
        return JsonResponse(result)


class ContinueMedataProcessing(AdminRecordProcessingView):
    """Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace."""

    def process_record(self, record, result, **kwargs):
        """
        Uloží metadata záznamu do Fedory a aktualizuje výsledkový slovník o stav zpracování.

        :param record: Instance záznamu, jehož metadata mají být uložena.
        :param result: Slovník s výsledky průběhu zpracování.
        :param kwargs: Další parametry předané z pohledu.

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
