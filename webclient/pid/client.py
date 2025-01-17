import logging

import requests
from django.conf import settings
from django.utils.translation import gettext as _
from dokument.models import Dokument
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez
from pid.model_serializers import DokumentSerializer, LokalitaSerializer, SamostatnyNalezSerializer
from requests.auth import HTTPBasicAuth

from webclient.settings.base import DATACITE_URL, DOI_USER, DOI_USER_PASSWORD, IGSN_USER, IGSN_USER_PASSWORD

logger = logging.getLogger(__name__)


class DoiWriteError(Exception):
    pass


class DoiHasBeenAlreadyPublishedError(DoiWriteError):
    pass


class DoiHasNotBeenPublishedYetError(DoiWriteError):
    pass


class DoiNoTransactionError(DoiWriteError):
    pass


class DigitalObjectIdentifierClient:
    headers = {"Content-Type": "application/vnd.api+json"}

    def __init__(self, record):
        self.record = record
        if isinstance(self.record, Dokument):
            self.serializer = DokumentSerializer(self.record)
            self.attribute_name = "doi"
            self.auth = HTTPBasicAuth(DOI_USER, DOI_USER_PASSWORD)
        elif isinstance(self.record, Lokalita):
            self.serializer = LokalitaSerializer(self.record)
            self.attribute_name = "igsn"
            self.auth = HTTPBasicAuth(IGSN_USER, IGSN_USER_PASSWORD)
        elif isinstance(self.record, SamostatnyNalez):
            self.serializer = SamostatnyNalezSerializer(self.record)
            self.attribute_name = "igsn"
            self.auth = HTTPBasicAuth(IGSN_USER, IGSN_USER_PASSWORD)
        else:
            logger.error("doi.client.DigitalObjectIdentifierClient.invalid_record_class")
            raise ValueError(_("doi.client.DigitalObjectIdentifierClient.invalid_record_class"))

    def _check_response_status(self, response):
        if not str(response.status_code).startswith("2"):
            logger.error(
                "doi.client.DigitalObjectIdentifierClient._check_response_status.error",
                extra={
                    "ident_cely": self.serializer.get_ident_cely(),
                    "status_code": response.status_code,
                },
            )
            raise DoiWriteError

    def _get_record_url(self):
        return f"{DATACITE_URL.rstrip('/')}/{settings.DOI_PREFIX}/{self.serializer.get_ident_cely()}"

    def check_record_exists(self):
        response = requests.get(self._get_record_url(), auth=self.auth)
        return str(response.status_code).startswith("2")

    def delete_record(self):
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_delete(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()

    def hide_record(self):
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_hide(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()

    def publish_record(self):
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        if self.check_record_exists():
            response = requests.put(
                self._get_record_url(), headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
            )
        else:
            response = requests.post(
                DATACITE_URL, headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
            )
        self._check_response_status(response)
        return response.json()

    def update_record(self):
        response = requests.put(
            self._get_record_url(), headers=self.headers, json=self.serializer.serialize_update(), auth=self.auth
        )
        self._check_response_status(response)
        return response.json()
