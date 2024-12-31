import logging

import requests
from core.constants import D_STAV_ARCHIVOVANY
from django.conf import settings
from django.utils.translation import gettext as _
from doi.model_serializers import DokumentSerializer
from dokument.models import Dokument
from requests.auth import HTTPBasicAuth

from webclient.settings.base import DATACITE_URL, DATACITE_USER, DATACITE_USER_PASSWORD

logger = logging.getLogger(__name__)


class DoiWriteError(Exception):
    pass


class DoiHasBeenAlreadyPublishedError(DoiWriteError):
    pass


class DoiHasNotBeenPublishedYetError(DoiWriteError):
    pass


class DoiIncorrectStatusError(DoiWriteError):
    pass


class DoiNoTransactionError(DoiWriteError):
    pass


class DigitalObjectIdentifierClient:
    auth = HTTPBasicAuth(DATACITE_USER, DATACITE_USER_PASSWORD)
    headers = {"Content-Type": "application/vnd.api+json"}

    def __init__(self, record):
        if not isinstance(record, Dokument):
            raise ValueError(_("doi.client.DigitalObjectIdentifierClient.invalid_record_class"))
        self.record = record
        if isinstance(self.record, Dokument):
            self.serializer = DokumentSerializer(self.record)

    def _check_response_status(self, response):
        if not str(response.status_code).startswith("2"):
            logger.error(
                "doi.client.DigitalObjectIdentifierClient._check_response_status.error",
                extra={
                    "ident_cely": self.record.ident_cely,
                    "status_code": response.status_code,
                    "response_text": response.text,
                },
            )
            raise DoiWriteError

    def _get_record_url(self):
        return f"{DATACITE_URL.rstrip(" / ")}/{settings.DOI_PREFIX}/{self.serializer.get_ident_cely()}"

    def check_record_exists(self):
        response = requests.get(self._get_record_url(), auth=self.auth)
        return str(response.status_code).startswith("2")

    def delete_record(self):
        if not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_hide(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()

    def hide_record(self):
        if not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_hide(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()

    def publish_or_update_record(self):
        if not self.record.doi and not self.check_record_exists():
            return self.publish_record()
        else:
            return self.update_record()

    def publish_record(self):
        if self.record.doi:
            logger.error(
                "doi.client.DigitalObjectIdentifierClient.publish_record.already_published.error",
                extra={"ident_cely": self.record.ident_cely},
            )
            raise DoiHasBeenAlreadyPublishedError
        if not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        if isinstance(self.record, Dokument):
            if self.record.stav != D_STAV_ARCHIVOVANY:
                logger.error(
                    "doi.client.DigitalObjectIdentifierClient.publish_record.archived.error",
                    extra={"ident_cely": self.record.ident_cely},
                )
                raise DoiIncorrectStatusError
        response = requests.post(
            DATACITE_URL, headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()

    def update_record(self):
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()
