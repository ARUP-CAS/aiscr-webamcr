import logging

import requests
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


class DoiConnectionError(DoiWriteError):
    pass


class DigitalObjectIdentifierClient:
    headers = {"Content-Type": "application/vnd.api+json"}

    record_serializer_map = {
        Dokument: (DokumentSerializer, "doi", HTTPBasicAuth(DOI_USER, DOI_USER_PASSWORD)),
        Lokalita: (LokalitaSerializer, "igsn", HTTPBasicAuth(IGSN_USER, IGSN_USER_PASSWORD)),
        SamostatnyNalez: (SamostatnyNalezSerializer, "igsn", HTTPBasicAuth(IGSN_USER, IGSN_USER_PASSWORD)),
    }

    def __init__(self, record):
        self.record = record
        record_type = type(record)
        if record_type in self.record_serializer_map:
            serializer_class, self.attribute_name, self.auth = self.record_serializer_map[record_type]
            self.serializer = serializer_class(self.record)  # Access serializer class dynamically
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
                    "request_url": response.url,
                },
            )
            raise DoiWriteError

    def get_record_url(self):
        return f"{DATACITE_URL.rstrip('/')}/{self.serializer._get_prefix()}/{self.serializer.get_ident_cely()}"

    def check_record_exists(self):
        response = requests.get(self.get_record_url(), auth=self.auth)
        if str(response.status_code).startswith("5"):
            logger.error(
                "doi.client.DigitalObjectIdentifierClient.check_record_exists.error",
                extra={
                    "ident_cely": self.serializer.get_ident_cely(),
                    "status_code": response.status_code,
                },
            )
            raise DoiConnectionError(response.text)
        return str(response.status_code).startswith("2")

    def delete_record(self):
        logger.debug(
            "doi.client.DigitalObjectIdentifierClient.delete_record.start",
            extra={"ident_cely": self.serializer.get_ident_cely()},
        )
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        if self.check_record_exists():
            response = requests.put(
                self.get_record_url(), headers=self.headers, json=self.serializer.serialize_delete(), auth=self.auth
            )
            self._check_response_status(response)
            return response.json()
        else:
            logger.info(
                "doi.client.DigitalObjectIdentifierClient.delete_record.does_not_exist",
                extra={"ident_cely": self.serializer.get_ident_cely()},
            )

    def hide_record(self):
        logger.debug(
            "doi.client.DigitalObjectIdentifierClient.hide_record.start",
            extra={"ident_cely": self.serializer.get_ident_cely()},
        )
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        if self.check_record_exists():
            response = requests.put(
                self.get_record_url(), headers=self.headers, json=self.serializer.serialize_hide(), auth=self.auth
            )
            self._check_response_status(response)
            return response.json()
        else:
            logger.info(
                "doi.client.DigitalObjectIdentifierClient.hide_record.does_not_exist",
                extra={"ident_cely": self.serializer.get_ident_cely()},
            )

    def publish_record(self):
        logger.debug(
            "doi.client.DigitalObjectIdentifierClient.check_record_exists.publish_record",
            extra={"ident_cely": self.serializer.get_ident_cely()},
        )
        if not isinstance(self.record, Lokalita) and not hasattr(self.record, "active_transaction"):
            raise DoiNoTransactionError
        if self.check_record_exists():
            response = requests.put(
                self.get_record_url(), headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
            )
        else:
            response = requests.post(
                DATACITE_URL, headers=self.headers, json=self.serializer.serialize_publish(), auth=self.auth
            )
        self._check_response_status(response)
        return response.json()

    def update_record(self):
        logger.debug(
            "doi.client.DigitalObjectIdentifierClient.update_record.start",
            extra={"ident_cely": self.serializer.get_ident_cely()},
        )
        if self.check_record_exists():
            response = requests.put(
                self.get_record_url(), headers=self.headers, json=self.serializer.serialize_update(), auth=self.auth
            )
            self._check_response_status(response)
            return response.json()
        else:
            logger.info(
                "doi.client.DigitalObjectIdentifierClient.update_record.does_not_exist",
                extra={"ident_cely": self.serializer.get_ident_cely()},
            )
