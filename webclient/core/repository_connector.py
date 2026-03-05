import hashlib
import io
import logging
import re
from abc import ABC
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from typing import Optional, Union

import requests
from celery import Celery
from core.connectors import RedisConnector
from core.log_middleware import LogMiddleware
from core.utils import get_mime_type
from django.conf import settings
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps
from requests.auth import HTTPBasicAuth
from xml_generator.generator import DocumentGenerator
from xml_generator.models import ModelWithMetadata

from redis import ResponseError

logger = logging.getLogger(__name__)


class FedoraValidationError(Exception):
    pass


class FedoraError(Exception):
    def __init__(self, url, message, code, headers=None, fedora_transaction=None):
        self.url = url
        self.message = message
        self.code = code
        self.headers = headers
        self.fedora_transaction: FedoraTransaction = fedora_transaction
        self.ident_cely: str = fedora_transaction.main_record.ident_cely if fedora_transaction else None
        self.redirect = fedora_transaction.redirect_on_error if fedora_transaction else None
        self.redirect_url = self.fedora_transaction.redirect_url if fedora_transaction else None
        super().__init__(self.message)


class FedoraUpdatedByAnotherTransactionError(FedoraError):
    pass


class IdentChangeFedoraError(Exception):
    pass


class FedoraNoResponseError(FedoraError):
    pass


class RepositoryBinaryFile:
    @staticmethod
    def get_url_without_domain(url):
        return "/".join(url.split("/")[3:])

    @property
    def url_without_domain(self):
        return self.get_url_without_domain(self.url)

    @property
    def uuid(self):
        return self.url.split("/")[-1]

    def _calculate_sha_512(self):
        data = self.content.read()
        sha_512 = hashlib.sha512(data).hexdigest()
        self.content.seek(0)
        self.sha_512 = sha_512

    @property
    def size_mb(self):
        return self.size / 1024**2

    @property
    def mime_type(self):
        if self.filename is not None:
            return get_mime_type(self.filename)

    def __init__(self, url: str, content: io.BytesIO, filename: Union[str, None] = None):
        self.url = url
        self.content = content
        self.filename = filename
        self.size = content.getbuffer().nbytes
        self.content.seek(0)
        self._calculate_sha_512()


class FedoraRequestType(Enum):
    # dotazy, které mění data ve Fedoře
    CREATE_CONTAINER = 2
    CREATE_LINK = 3
    CREATE_METADATA = 4
    UPDATE_METADATA = 5
    CREATE_BINARY_FILE_CONTAINER = 7
    CREATE_BINARY_FILE = 9
    CREATE_BINARY_FILE_CONTENT = 10
    CREATE_BINARY_FILE_THUMB = 11
    UPDATE_BINARY_FILE_CONTENT = 13
    DELETE_CONTAINER = 15
    DELETE_TOMBSTONE = 16
    RECORD_DELETION_MOVE_MEMBERS = 17
    RECORD_DELETION_ADD_MARK = 18
    CHANGE_IDENT_CONNECT_RECORDS_2 = 20
    CHANGE_IDENT_CONNECT_RECORDS_4 = 22
    DELETE_LINK_CONTAINER = 23
    DELETE_LINK_TOMBSTONE = 24
    DELETE_BINARY_FILE = 25
    DELETE_BINARY_FILE_COMPLETELY = 26
    CONNECT_DELETED_RECORD_1 = 28
    CONNECT_DELETED_RECORD_2 = 29
    CONNECT_DELETED_RECORD_3 = 30
    CONNECT_DELETED_RECORD_4 = 31
    UPDATE_BINARY_FILE_CONTENT_THUMB = 33
    CREATE_BINARY_FILE_THUMB_LARGE = 34
    UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE = 36
    CHANGE_IDENT_CONNECT_RECORDS_5 = 38
    CHANGE_IDENT_CONNECT_RECORDS_6 = 39
    METADATA_UPDATE_RDF_DATA = 40
    FILE_CONTENT_UPDATE_RDF_DATA = 41
    THUMB_CONTENT_UPDATE_RDF_DATA = 42
    THUMB_LARGE_CONTENT_UPDATE_RDF_DATA = 43

    # dotazy, které nemění Fedoru
    GET_CONTAINER = 1001
    GET_METADATA = 1006
    GET_BINARY_FILE_CONTAINER = 1008
    GET_BINARY_FILE_CONTENT = 1012
    GET_LINK = 1014
    GET_DELETED_LINK = 1027
    GET_BINARY_FILE_CONTENT_THUMB = 1032
    GET_BINARY_FILE_CONTENT_THUMB_LARGE = 1035
    GET_TOMBSTONE = 1037
    GET_METADATA_HISTORIE = 1038
    GET_BINARY_FILE_CONTENT_HISTORIE = 1039
    GET_METADATA_VERSION = 1040
    GET_BINARY_FILE_METADATA_VERSION = 1041


class FedoraRepositoryConnector:
    def __init__(self, record, transaction=None, skip_container_check=True):
        from core.models import ModelWithMetadata
        from uzivatel.models import User

        record: ModelWithMetadata
        self.record = record
        if isinstance(transaction, FedoraTransaction):
            self.transaction_uid = transaction.uid
        elif isinstance(transaction, str):
            self.transaction_uid = transaction
            transaction = FedoraTransaction(uid=transaction)
        else:
            self.transaction_uid = None
        self.restored_container = False
        self.skip_container_check = skip_container_check
        self.transaction = transaction
        if transaction and not transaction.main_record:
            transaction.main_record = record
        if isinstance(self.transaction, FedoraTransaction) and isinstance(self.transaction.transaction_user, User):
            self.user = self.transaction.transaction_user.ident_cely
        else:
            self.user = LogMiddleware.get_user_id()
        logger.debug(
            "core_repository_connector.__init__.end",
            extra={"transaction": self.transaction_uid, "ident_cely": record.ident_cely},
        )

    def _get_model_name(self):
        class_name = self.record.__class__.__name__
        return {
            "Adb": "adb",
            "ArcheologickyZaznam": "archeologicky_zaznam",
            "Dokument": "dokument",
            "ExterniZdroj": "ext_zdroj",
            "Heslar": "heslo",
            "Let": "let",
            "Organizace": "organizace",
            "Osoba": "osoba",
            "Pian": "pian",
            "Projekt": "projekt",
            "RuianKatastr": "ruian_katastr",
            "RuianKraj": "ruian_kraj",
            "RuianOkres": "ruian_okres",
            "SamostatnyNalez": "samostatny_nalez",
            "User": "uzivatel",
        }.get(class_name)

    def _get_creator_rdf_data(self):
        return f"""PREFIX dcterms: <http://purl.org/dc/terms/>
DELETE WHERE {{ <> dcterms:creator ?oldCreator .}};
INSERT DATA {{ <> dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> .}};"""

    def _get_creator(self, url, only_uri=False):
        headers = {"Accept": "text/turtle"}
        r = self._send_request(url, FedoraRequestType.GET_METADATA, headers=headers)
        if r.status_code != 200:
            return None
        # Může být dcterms:creator "U-123" nebo dcterms:creator <info:fedora/AMCR/record/U-123>
        if only_uri:
            pattern = re.compile(
                r"dcterms:creator\s+<([^>]+)>",
                re.MULTILINE,
            )
            match = pattern.search(r.text)
            if not match:
                return None
            value = match.group(1)
        else:
            pattern = re.compile(
                r'dcterms:creator\s+(?:"([^"]+)"|<([^>]+)>)',
                re.MULTILINE,
            )
            match = pattern.search(r.text)
            if not match:
                return None
            value = match.group(1) or match.group(2)

        if "/" in value:
            return value.rstrip("/").split("/")[-1]
        return value.strip()

    def _update_creator(self, request_type: FedoraRequestType, uuid=None, ident_cely=None):
        url = self._get_request_url(request_type, uuid=uuid, ident_cely=ident_cely)
        existing_creator = self._get_creator(url, only_uri=True)
        if existing_creator != self.user:
            self._send_request(
                url,
                request_type,
                headers={"Content-Type": "application/sparql-update"},
                data=self._get_creator_rdf_data(),
            )

    @staticmethod
    def get_base_url():
        return (
            f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/"
            f"{settings.FEDORA_SERVER_NAME}"
        )

    def _get_request_url(self, request_type: FedoraRequestType, *, uuid=None, ident_cely=None) -> Optional[str]:
        base_url = self.get_base_url()
        if request_type == FedoraRequestType.CREATE_CONTAINER:
            return f"{base_url}/record/"
        elif request_type in (
            FedoraRequestType.GET_CONTAINER,
            FedoraRequestType.CREATE_METADATA,
            FedoraRequestType.CREATE_BINARY_FILE_CONTAINER,
            FedoraRequestType.DELETE_CONTAINER,
            FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS,
            FedoraRequestType.CONNECT_DELETED_RECORD_1,
            FedoraRequestType.CONNECT_DELETED_RECORD_2,
        ):
            return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type == FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_6:
            ident_cely = ident_cely if ident_cely else self.record.ident_cely
            return f"{base_url}/record/{ident_cely}"
        elif request_type in (FedoraRequestType.CREATE_LINK,):
            return f"{base_url}/model/{self._get_model_name()}/member"
        elif request_type in (FedoraRequestType.GET_LINK, FedoraRequestType.DELETE_LINK_CONTAINER):
            return (
                f"{base_url}/model/{self._get_model_name()}/member/"
                f"{ident_cely if ident_cely else self.record.ident_cely}"
            )
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.GET_METADATA):
            return f"{base_url}/record/{self.record.ident_cely}/metadata"
        elif request_type == FedoraRequestType.METADATA_UPDATE_RDF_DATA:
            return f"{base_url}/record/{self.record.ident_cely}/metadata/fcr:metadata"
        elif request_type == FedoraRequestType.GET_METADATA_HISTORIE:
            return f"{base_url}/record/{self.record.ident_cely}/metadata/fcr:versions"
        elif request_type == FedoraRequestType.GET_METADATA_VERSION:
            return f"{base_url}/record/{self.record.ident_cely}/metadata/fcr:metadata/fcr:versions"
        elif request_type == FedoraRequestType.GET_BINARY_FILE_METADATA_VERSION:
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig/fcr:metadata/fcr:versions"
        elif request_type == FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE:
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig/fcr:versions"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE):
            return f"{base_url}/record/{self.record.ident_cely}/file"
        elif request_type in (
            FedoraRequestType.CREATE_BINARY_FILE_CONTENT,
            FedoraRequestType.DELETE_BINARY_FILE,
            FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY,
            FedoraRequestType.CREATE_BINARY_FILE_THUMB,
            FedoraRequestType.CREATE_BINARY_FILE_THUMB_LARGE,
        ):
            ident_cely = ident_cely if ident_cely else self.record.ident_cely
            return f"{base_url}/record/{ident_cely}/file/{uuid}"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTENT, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT):
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig"
        elif request_type == FedoraRequestType.FILE_CONTENT_UPDATE_RDF_DATA:
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig/fcr:metadata"
        elif request_type in (
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB,
            FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB,
        ):
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/thumb"
        elif request_type == FedoraRequestType.THUMB_CONTENT_UPDATE_RDF_DATA:
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/thumb/fcr:metadata"
        elif request_type in (
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE,
            FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE,
        ):
            ident_cely = ident_cely if ident_cely else self.record.ident_cely
            return f"{base_url}/record/{ident_cely}/file/{uuid}/thumb-large"
        elif request_type == FedoraRequestType.THUMB_LARGE_CONTENT_UPDATE_RDF_DATA:
            ident_cely = ident_cely if ident_cely else self.record.ident_cely
            return f"{base_url}/record/{ident_cely}/file/{uuid}/thumb-large/fcr:metadata"
        elif request_type == FedoraRequestType.DELETE_TOMBSTONE:
            return f"{base_url}/record/{self.record.ident_cely}/fcr:tombstone"
        elif request_type == FedoraRequestType.DELETE_LINK_TOMBSTONE:
            return (
                f"{base_url}/model/{self._get_model_name()}/member/"
                f"{ident_cely if ident_cely else self.record.ident_cely}/fcr:tombstone"
            )
        elif request_type in (
            FedoraRequestType.RECORD_DELETION_ADD_MARK,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4,
        ):
            return f"{base_url}/model/deleted/member"
        elif request_type in (
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_5,
        ):
            if ident_cely:
                return f"{base_url}/record/{ident_cely}"
            else:
                return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type in (FedoraRequestType.GET_DELETED_LINK, FedoraRequestType.CONNECT_DELETED_RECORD_3):
            if ident_cely:
                return f"{base_url}/model/deleted/member/{ident_cely}"
            else:
                return f"{base_url}/model/deleted/member/{self.record.ident_cely}"
        elif request_type in (FedoraRequestType.CONNECT_DELETED_RECORD_4,):
            if ident_cely:
                return f"{base_url}/model/deleted/member/{ident_cely}/fcr:tombstone"
            else:
                return f"{base_url}/model/deleted/member/{self.record.ident_cely}/fcr:tombstone"
        logger.error("core_repository_connector._get_request_url.not_implemented", extra={"request_type": request_type})

    def check_container_deleted(self, ident_cely):
        result = self._send_request(f"{self.get_base_url()}/record/{ident_cely}", FedoraRequestType.GET_CONTAINER)
        regex = re.compile(r"dcterms:type *\"deleted\" *;")
        return hasattr(result, "text") and regex.search(result.text)

    @classmethod
    def check_container_deleted_or_not_exists(cls, ident_cely, model_name):
        logger.debug("core_repository_connector.check_container_is_deleted.start", extra={"ident_cely": ident_cely})

        def send_request(url, request_type):
            auth = cls._get_auth(request_type)
            response = requests.get(url, auth=auth, verify=False)
            return response

        result = send_request(f"{cls.get_base_url()}/record/{ident_cely}", FedoraRequestType.GET_CONTAINER)
        result_2 = send_request(
            f"{cls.get_base_url()}/model/deleted/member/{ident_cely}", FedoraRequestType.GET_DELETED_LINK
        )
        result_3 = send_request(
            f"{cls.get_base_url()}/model/{model_name}/member/{ident_cely}", FedoraRequestType.GET_LINK
        )

        result_4 = send_request(f"{cls.get_base_url()}/record/{ident_cely}", FedoraRequestType.GET_CONTAINER)
        regex = re.compile(r"dcterms:type *\"deleted\" *;")
        is_deleted = hasattr(result_4, "text") and regex.search(result_4.text)

        if result.status_code == 200:
            if is_deleted:
                if result_2.status_code == 200:
                    logger.debug(
                        "core_repository_connector.check_container_is_deleted.true",
                        extra={"ident_cely": ident_cely, "text": result.text},
                    )
                    if result_3.status_code == 200:
                        logger.debug(
                            "core_repository_connector.check_container_is_deleted.true",
                            extra={"ident_cely": ident_cely, "text": result.text},
                        )
                        return True
        elif result.status_code == 404 and result_2.status_code == 404:
            logger.debug(
                "core_repository_connector.check_container_is_deleted.true",
                extra={"ident_cely": ident_cely, "text": result.text},
            )
            return True
        logger.debug(
            "core_repository_connector.check_container_is_deleted.false",
            extra={"ident_cely": ident_cely, "text": result.text},
        )
        return False

    @classmethod
    def _get_auth(cls, request_type: FedoraRequestType):
        if request_type in (
            FedoraRequestType.DELETE_CONTAINER,
            FedoraRequestType.DELETE_TOMBSTONE,
            FedoraRequestType.DELETE_LINK_CONTAINER,
            FedoraRequestType.DELETE_LINK_TOMBSTONE,
        ):
            auth = HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        else:
            auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        return auth

    def _send_request(
        self, url: str, request_type: FedoraRequestType, *, headers=None, data=None
    ) -> requests.Response | None:
        extra = {"info": url, "request_type": request_type, "transaction": self.transaction_uid}
        if isinstance(data, str) and len(data) < 1000:
            extra["data"] = data
        logger.debug("core_repository_connector._send_request.start", extra=extra)
        auth = self._get_auth(request_type)
        response = None
        if self.transaction_uid:
            if headers is None:
                headers = {}
            if settings.FEDORA_TRANSACTION_URL:
                headers["Atomic-ID"] = f"{settings.FEDORA_TRANSACTION_URL}rest/fcr:tx/{self.transaction_uid}"
            else:
                headers["Atomic-ID"] = (
                    f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}"
                    f":{settings.FEDORA_PORT_NUMBER}/rest/fcr:tx/{self.transaction_uid}"
                )
            if request_type.value < 1000:
                self.transaction.changes_count += 1
        if request_type in (FedoraRequestType.CREATE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE_CONTAINER):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type in (
            FedoraRequestType.GET_CONTAINER,
            FedoraRequestType.GET_METADATA,
            FedoraRequestType.GET_BINARY_FILE_CONTAINER,
            FedoraRequestType.GET_BINARY_FILE_CONTENT,
            FedoraRequestType.GET_LINK,
            FedoraRequestType.GET_DELETED_LINK,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE,
            FedoraRequestType.GET_TOMBSTONE,
            FedoraRequestType.GET_METADATA_HISTORIE,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE,
        ):
            try:
                response = requests.get(url, headers=headers, auth=auth, verify=False)
            except requests.exceptions.RequestException:
                return None
        elif request_type in (
            FedoraRequestType.CREATE_METADATA,
            FedoraRequestType.RECORD_DELETION_ADD_MARK,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4,
            FedoraRequestType.CREATE_LINK,
        ):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type in (
            FedoraRequestType.CREATE_BINARY_FILE_CONTENT,
            FedoraRequestType.CREATE_BINARY_FILE_THUMB,
            FedoraRequestType.CREATE_BINARY_FILE_THUMB_LARGE,
        ):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False, timeout=10)
        elif request_type in (
            FedoraRequestType.UPDATE_METADATA,
            FedoraRequestType.UPDATE_BINARY_FILE_CONTENT,
            FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB,
            FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE,
        ):
            response = requests.put(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type == FedoraRequestType.CREATE_BINARY_FILE:
            response = requests.post(url, headers=headers, auth=auth, data=data, verify=False)
        elif request_type in (
            FedoraRequestType.DELETE_CONTAINER,
            FedoraRequestType.DELETE_TOMBSTONE,
            FedoraRequestType.DELETE_LINK_CONTAINER,
            FedoraRequestType.DELETE_LINK_TOMBSTONE,
            FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY,
            FedoraRequestType.CONNECT_DELETED_RECORD_3,
            FedoraRequestType.CONNECT_DELETED_RECORD_4,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_5,
        ):
            response = requests.delete(url, headers=headers, auth=auth)
        elif request_type in (
            FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
            FedoraRequestType.DELETE_BINARY_FILE,
            FedoraRequestType.CONNECT_DELETED_RECORD_1,
            FedoraRequestType.CONNECT_DELETED_RECORD_2,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_6,
            FedoraRequestType.METADATA_UPDATE_RDF_DATA,
            FedoraRequestType.FILE_CONTENT_UPDATE_RDF_DATA,
            FedoraRequestType.THUMB_CONTENT_UPDATE_RDF_DATA,
            FedoraRequestType.THUMB_LARGE_CONTENT_UPDATE_RDF_DATA,
        ):
            response = requests.patch(url, auth=auth, headers=headers, data=data)
        extra["status_code"] = response.status_code

        if request_type in (
            FedoraRequestType.CONNECT_DELETED_RECORD_4,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_5,
        ):
            extra = {
                "status_code": response.status_code,
                "request_type": request_type,
                "response": response.text,
                "transaction": self.transaction_uid,
                "info": url,
            }
            if str(response.status_code)[0] == "2":
                logger.debug("core_repository_connector._send_request.response.ok", extra=extra)
            else:
                logger.warning("core_repository_connector._send_request.error", extra=extra)
        elif request_type not in (
            FedoraRequestType.GET_CONTAINER,
            FedoraRequestType.GET_METADATA,
            FedoraRequestType.GET_BINARY_FILE_CONTAINER,
            FedoraRequestType.GET_BINARY_FILE_CONTENT,
            FedoraRequestType.GET_LINK,
            FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
            FedoraRequestType.GET_DELETED_LINK,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE,
        ):
            if str(response.status_code)[0] == "2":
                logger.debug("core_repository_connector._send_request.response.ok", extra=extra)
            else:
                extra = {
                    "status_code": response.status_code,
                    "request_type": request_type,
                    "response": response.text,
                    "transaction": self.transaction_uid,
                    "info": url,
                }
                if self.transaction:
                    self.transaction.rollback_transaction()
                else:
                    fedora_transaction = FedoraTransaction(uid=self.transaction_uid)
                    fedora_transaction.rollback_transaction()
                if response.status_code == 409:
                    logger.info(
                        "core_repository_connector._send_request.response.another_transaction_error", extra=extra
                    )
                    raise FedoraUpdatedByAnotherTransactionError(
                        url, response.text, response.status_code, response.headers, self.transaction
                    )
                else:
                    logger.error("core_repository_connector._send_request.response.error", extra=extra)
                    raise FedoraError(url, response.text, response.status_code, response.headers, self.transaction)
        elif request_type in (
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB,
            FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE,
        ):
            if str(response.status_code)[0] == "2":
                return response
            else:
                return None
        else:
            logger.debug("core_repository_connector._send_request.response", extra=extra)
            if (
                request_type
                in (
                    FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB,
                    FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE,
                )
                and str(response.status_code)[0] != "2"
            ):
                return None
        return response

    def _create_container(self):
        logger.debug(
            "core_repository_connector._create_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.CREATE_CONTAINER)
        headers = {
            "Slug": self.record.ident_cely,
            "Link": '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"',
            "Content-Type": "text/turtle",
        }
        rdf = f"@prefix dcterms: <http://purl.org/dc/terms/> . <> dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        self._send_request(url, FedoraRequestType.CREATE_CONTAINER, headers=headers, data=rdf)
        self.create_link()
        logger.debug(
            "core_repository_connector._create_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def create_link(self, ident_cely_proxy=None):
        logger.debug(
            "core_repository_connector._create_link.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.CREATE_LINK)
        headers = {"Slug": self.record.ident_cely, "Content-Type": "text/turtle"}
        data = (
            "@prefix ore: <http://www.openarchives.org/ore/terms/> . "
            "@prefix dcterms: <http://purl.org/dc/terms/> . "
            f"<> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/"
            f"{ident_cely_proxy if ident_cely_proxy else self.record.ident_cely}> ; "
            f"dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        )
        self._send_request(url, FedoraRequestType.CREATE_LINK, headers=headers, data=data)
        logger.debug(
            "core_repository_connector._create_link.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def container_exists(self):
        logger.debug(
            "core_repository_connector._container_exists.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result is None or result.status_code == 404:
            logger.debug(
                "core_repository_connector._container_exists.false",
                extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
            return False
        logger.debug(
            "core_repository_connector._container_exists.true",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        return True

    def _connect_deleted_container(self):
        logger.debug(
            "core_repository_connector._connect_deleted_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.CONNECT_DELETED_RECORD_1)
        headers = {
            "Content-Type": "application/sparql-update",
        }
        data = "DELETE DATA {<> <http://purl.org/dc/terms/type> 'deleted'}"
        self._send_request(url, FedoraRequestType.CONNECT_DELETED_RECORD_1, headers=headers, data=data)
        url = self._get_request_url(FedoraRequestType.CONNECT_DELETED_RECORD_2)
        headers = {
            "Content-Type": "application/sparql-update",
        }
        data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'restored'}"
        self._send_request(url, FedoraRequestType.CONNECT_DELETED_RECORD_2, headers=headers, data=data)
        url = self._get_request_url(FedoraRequestType.CONNECT_DELETED_RECORD_3)
        self._send_request(url, FedoraRequestType.CONNECT_DELETED_RECORD_3)
        url = self._get_request_url(FedoraRequestType.CONNECT_DELETED_RECORD_4)
        self._send_request(url, FedoraRequestType.CONNECT_DELETED_RECORD_4)

        logger.debug(
            "core_repository_connector._connect_deleted_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def link_exists(self):
        url = self._get_request_url(FedoraRequestType.GET_LINK)
        result = self._send_request(url, FedoraRequestType.GET_LINK)
        return result.status_code != 404

    def _check_container(self):
        logger.debug(
            "core_repository_connector._check_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        regex = re.compile(r"dcterms:type *\"deleted\" *;")
        if hasattr(result, "text") and regex.search(result.text):
            logger.debug(
                "core_repository_connector._check_container.connect_delete",
                extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
            self._connect_deleted_container()
            self.restored_container = True
        elif result.status_code == 404:
            logger.debug(
                "core_repository_connector._check_container.create",
                extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
            self._create_container()
        if not self.link_exists():
            self.create_link()
        logger.debug(
            "core_repository_connector._check_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def _create_binary_file_container(self):
        logger.debug(
            "core_repository_connector._create_binary_file_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTAINER)
        headers = {
            "Slug": "file",
            "Content-Type": "text/turtle",
        }
        rdf = f"@prefix dcterms: <http://purl.org/dc/terms/> . <> dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTAINER, headers=headers, data=rdf)
        logger.debug(
            "core_repository_connector._create_binary_file_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def _check_binary_file_container(self):
        logger.debug(
            "core_repository_connector._check_binary_file_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        if not self.skip_container_check:
            self._check_container()
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTAINER)
        if result.status_code == 404:
            self._create_binary_file_container()
        logger.debug(
            "core_repository_connector._check_binary_file_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def _generate_metadata(self):
        logger.debug(
            "core_repository_connector._generate_metadata.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        document_generator = DocumentGenerator(self.record)
        document = document_generator.generate_document()
        hash512 = hashlib.sha512(document).hexdigest()
        logger.debug(
            "core_repository_connector._generate_metadata.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        return document, hash512

    def get_metadata(self, update=False) -> bytes:
        logger.debug(
            "core_repository_connector.get_metadata.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        self.save_metadata(update)
        url = self._get_request_url(FedoraRequestType.GET_METADATA)
        response = self._send_request(url, FedoraRequestType.GET_METADATA)
        logger.debug(
            "core_repository_connector.get_metadata.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        return response.content

    def get_metadata_historicka(self, timestamp):
        """
        Metoda varacející konkrétní verzi metadat
        """
        url = self._get_request_url(FedoraRequestType.GET_METADATA_HISTORIE)
        response = self._send_request(f"{url}/{timestamp}", FedoraRequestType.GET_METADATA_HISTORIE)
        return response.content

    def parse_historie(self, response_text):
        """
        Metoda k parsování odpovědi s verzemi
        Vrací list dictů: {"datetime": datetime, "timestamp": str}
        """
        result = []
        for line in response_text.splitlines():
            stripped = line.strip()

            if stripped.startswith("ldp:contains"):

                m = re.search(r"<(.*?)>", stripped)
                if m:
                    url = m.group(1)
                    ts = url.rstrip("/").split("/")[-1]
                    if ts.isdigit() and len(ts) == 14:
                        try:
                            dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
                            dt = dt.replace(tzinfo=timezone.utc)
                            result.append(
                                {
                                    "datetime": dt,
                                    "timestamp": ts,
                                }
                            )
                        except ValueError:
                            logger.error(
                                "core_repository_connector.parse_historie.datetime_error",
                                extra={"ident_cely": self.record.ident_cely, "data": ts},
                            )

        return result

    def get_historie_metadat(self):
        """
        Metoda k získání info o verzích metadat
        """
        url = self._get_request_url(FedoraRequestType.GET_METADATA_HISTORIE)
        response = self._send_request(url, FedoraRequestType.GET_METADATA_HISTORIE, headers={"Accept": "text/turtle"})
        result = self.parse_historie(response.text)
        url = self._get_request_url(FedoraRequestType.GET_METADATA_VERSION)
        for item in result:
            item["creator"] = self._get_creator(f"{url}/{item['timestamp']}")
        return result

    def get_historie_file(self, uuid):
        """
        Metoda k získání info o verzích souborů
        """
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE, uuid=uuid)
        response = self._send_request(
            url, FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE, headers={"Accept": "text/turtle"}
        )
        result = self.parse_historie(response.text)
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_METADATA_VERSION, uuid=uuid)
        for item in result:
            item["creator"] = self._get_creator(f"{url}/{item['timestamp']}")
        return result

    def save_metadata(self, update=True):
        logger.debug(
            "core_repository_connector.save_metadata.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        if not self.skip_container_check:
            self._check_container()
        url = self._get_request_url(FedoraRequestType.GET_METADATA)
        result = self._send_request(url, FedoraRequestType.GET_METADATA)

        def generate_metadata():
            document_func, hash512 = self._generate_metadata()
            headers_func = {
                "Content-Type": "application/xml",
                "Content-Disposition": 'attachment; filename="metadata.xml"',
                "Digest": f"sha-512={hash512}",
            }
            return document_func, headers_func

        if result is None:
            raise FedoraNoResponseError(url, "No Fedora response", None, fedora_transaction=self.transaction)
        if result.status_code == 404:
            document, headers = generate_metadata()
            headers["slug"] = "metadata"
            url = self._get_request_url(FedoraRequestType.CREATE_METADATA)
            self._send_request(url, FedoraRequestType.CREATE_METADATA, headers=headers, data=document)
            self._update_creator(FedoraRequestType.METADATA_UPDATE_RDF_DATA)
        elif update is True:
            document, headers = generate_metadata()
            url = self._get_request_url(FedoraRequestType.UPDATE_METADATA)
            self._send_request(url, FedoraRequestType.UPDATE_METADATA, headers=headers, data=document)
            self._update_creator(FedoraRequestType.METADATA_UPDATE_RDF_DATA)
        logger.debug(
            "core_repository_connector.save_metadata.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def save_binary_file(
        self, file_name, content_type, file: io.BytesIO, save_thumbs: bool = True
    ) -> RepositoryBinaryFile:
        logger.debug(
            "core_repository_connector.save_binary_file.start",
            extra={"file": file_name, "ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        self._check_binary_file_container()
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE)
        headers = {
            "Content-Type": "text/turtle",
        }
        rdf = f"@prefix dcterms: <http://purl.org/dc/terms/> . <> dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        result = self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE, headers=headers, data=rdf)
        uuid = result.text.split("/")[-1]
        rep_bin_file = RepositoryBinaryFile(result.text, file, file_name)
        data = file.read()
        file_sha_512 = hashlib.sha512(data).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{file_name}"'.encode("utf-8"),
            "Digest": f"sha-512={file_sha_512}",
            "Slug": "orig",
        }
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTENT, uuid=uuid)
        self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTENT, headers=headers, data=data)
        self._update_creator(FedoraRequestType.FILE_CONTENT_UPDATE_RDF_DATA, uuid)
        if save_thumbs:
            self.save_thumbs(file_name, file, uuid)
        logger.debug(
            "core_repository_connector.save_binary_file.end",
            extra={"uuid": uuid, "ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        return rep_bin_file

    @staticmethod
    def __generate_thumb(file_name: str, file_content: BytesIO, large=False):
        logger.debug("core_repository_connector.__generate_thumb.start", extra={"file": file_name, "large": large})

        def resize_image(image: BytesIO, large_inner=False):
            image = Image.open(image)
            image = ImageOps.exif_transpose(image)
            max_size = ((1 + large_inner * 7) * 100, (1 + large_inner * 7) * 100)
            image.thumbnail(max_size)
            output_buffer = BytesIO()
            image.save(output_buffer, format="PNG")
            output_buffer.seek(0)
            return output_buffer

        def __generate_thumb_from_icon(file_name: str, file_content: BytesIO, large=False):
            from core.models import Soubor

            thumb_icon, mime_type = Soubor.get_thumb_icon(file_content)
            if mime_type.startswith("image/"):
                try:
                    thumbnail = resize_image(file_content, large)
                    logger.debug(
                        "core_repository_connector.__generate_thumb.end", extra={"file": file_name, "large": large}
                    )
                    return thumbnail
                except Exception as err:
                    logger.info(
                        "core_repository_connector.__generate_thumb.error",
                        extra={"error": err, "file": file_name, "large": large},
                    )
                    if thumb_icon is not None:
                        try:
                            return resize_image(thumb_icon, large)
                        except Exception as err:
                            logger.error(
                                "core_repository_connector.__generate_thumb_icon.error",
                                extra={"error": err, "file": file_name, "large": large},
                            )
                    return None
            else:
                return resize_image(thumb_icon, large)

        if file_name.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(file_content.getvalue(), first_page=1, last_page=1)
                image_bytes_io = io.BytesIO()
                images[0].save(image_bytes_io, format="PNG")
                image_bytes_io.seek(0)
                thumbnail = resize_image(image_bytes_io, large)
                logger.debug(
                    "core_repository_connector.__generate_thumb.end", extra={"file": file_name, "large": large}
                )
                return thumbnail
            except Exception as err:
                logger.debug(
                    "core_repository_connector.__generate_thumb.error",
                    extra={"error": err, "file": file_name, "large": large},
                )
                return __generate_thumb_from_icon(file_name, file_content, large)
        else:
            return __generate_thumb_from_icon(file_name, file_content, large)

    def save_thumbs(self, file_name, file, uuid, update=False, ident_cely_old=None):
        logger.debug(
            "core_repository_connector._save_thumb.start",
            extra={
                "file": file_name,
                "ident_cely": self.record.ident_cely,
                "update": update,
                "uuid": uuid,
                "transaction": self.transaction_uid,
            },
        )
        for large in (True, False):
            file.seek(0)
            data = self.__generate_thumb(file_name, file, large)
            if not data:
                logger.info(
                    "core_repository_connector._save_thumb.error",
                    extra={
                        "file": file_name,
                        "ident_cely": self.record.ident_cely,
                        "large": large,
                        "update": update,
                        "uuid": uuid,
                        "transaction": self.transaction_uid,
                    },
                )
                continue
            data = data.read()
            file_sha_512 = hashlib.sha512(data).hexdigest()
            thumb_file_name = file_name[: file_name.rfind(".")]
            headers = {
                "Content-Type": "image/png",
                "Content-Disposition": f'attachment; filename="{thumb_file_name}.png"'.encode("utf-8"),
                "Digest": f"sha-512={file_sha_512}",
                "Slug": f"thumb{'-large' * large}",
            }
            ident_cely = ident_cely_old if ident_cely_old and update else self.record.ident_cely
            existing_large_thumb, existing_small_thumb = None, None
            if large:
                existing_large_thumb = self.get_binary_file(uuid, thumb_large=True)
            else:
                existing_small_thumb = self.get_binary_file(uuid, thumb_small=True)
            if large:
                if update and existing_large_thumb is not None:
                    url = self._get_request_url(
                        FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE, uuid=uuid, ident_cely=ident_cely
                    )
                else:
                    url = self._get_request_url(
                        FedoraRequestType.CREATE_BINARY_FILE_THUMB_LARGE, uuid=uuid, ident_cely=ident_cely
                    )
            else:
                if update and existing_small_thumb is not None:
                    url = self._get_request_url(
                        FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB, uuid=uuid, ident_cely=ident_cely
                    )
                else:
                    url = self._get_request_url(
                        FedoraRequestType.CREATE_BINARY_FILE_THUMB, uuid=uuid, ident_cely=ident_cely
                    )
            if large:
                if update and existing_large_thumb is not None:
                    self._send_request(
                        url, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB_LARGE, headers=headers, data=data
                    )
                else:
                    self._send_request(
                        url, FedoraRequestType.CREATE_BINARY_FILE_THUMB_LARGE, headers=headers, data=data
                    )
                self._update_creator(FedoraRequestType.THUMB_LARGE_CONTENT_UPDATE_RDF_DATA, uuid, ident_cely)
            else:
                if update and existing_small_thumb is not None:
                    self._send_request(
                        url, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT_THUMB, headers=headers, data=data
                    )
                else:
                    self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_THUMB, headers=headers, data=data)
                self._update_creator(FedoraRequestType.THUMB_CONTENT_UPDATE_RDF_DATA, uuid, ident_cely)
            logger.debug(
                "core_repository_connector._save_thumb.end",
                extra={
                    "file": file_name,
                    "ident_cely": self.record.ident_cely,
                    "large": large,
                    "update": update,
                    "uuid": uuid,
                    "transaction": self.transaction_uid,
                },
            )

    def migrate_binary_file(
        self, soubor, include_content=True, check_if_exists=True, ident_cely_old=None
    ) -> Optional[RepositoryBinaryFile]:
        from core.models import Soubor

        soubor: Soubor
        logger.debug(
            "core_repository_connector.migrate_binary_file.start",
            extra={"pk": soubor.pk, "transaction": self.transaction_uid},
        )
        if soubor.repository_uuid is not None and check_if_exists:
            return None
        self._check_binary_file_container()
        if include_content:
            if soubor.repository_uuid is None:
                with open(soubor.path, mode="rb") as file:
                    data = file.read()
                data = io.BytesIO(data)
                file_sha_512 = hashlib.sha512(data).hexdigest()
            else:
                old_rep_bin_file = soubor.get_repository_content(ident_cely_old)
                data = old_rep_bin_file.content
                file_sha_512 = old_rep_bin_file.sha_512
                data.seek(0)
        else:
            data = None
            file_sha_512 = None
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE)
        headers = {
            "Content-Type": "text/turtle",
        }
        rdf = f"@prefix dcterms: <http://purl.org/dc/terms/> . <> dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        result = self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE, headers=headers, data=rdf)
        uuid = result.text.split("/")[-1]
        soubor.path = RepositoryBinaryFile.get_url_without_domain(result.text)
        soubor.suppress_signal = True
        soubor.save()
        if include_content:
            content_type = get_mime_type(soubor.nazev)
            rep_bin_file = RepositoryBinaryFile(uuid, data, soubor.nazev)
            headers = {
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{soubor.nazev}"'.encode("utf-8"),
                "Digest": f"sha-512={file_sha_512}",
                "Slug": "orig",
            }
            url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTENT, uuid=uuid)
            self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTENT, headers=headers, data=data)
            self._update_creator(FedoraRequestType.FILE_CONTENT_UPDATE_RDF_DATA, uuid)
            self.save_thumbs(soubor.nazev, data, soubor.repository_uuid)
            logger.debug(
                "core_repository_connector.migrate_binary_file.end",
                extra={"uuid": uuid, "ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
            return rep_bin_file

    def get_binary_file(
        self, uuid, ident_cely_old=None, thumb_small=False, thumb_large=False, timestamp=None
    ) -> RepositoryBinaryFile | None:
        logger.debug(
            "core_repository_connector.get_binary_file.start",
            extra={
                "uuid": uuid,
                "ident_cely_old": ident_cely_old,
                "thumb_small": thumb_small,
                "thumb_large": thumb_large,
                "transaction": self.transaction_uid,
            },
        )
        if thumb_small:
            url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB, uuid=uuid)
        elif thumb_large:
            url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE, uuid=uuid)
        else:
            url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT, uuid=uuid)
        if ident_cely_old is not None:
            url = url.replace(self.record.ident_cely, ident_cely_old)
        if thumb_small:
            response = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB)
        elif thumb_large:
            response = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTENT_THUMB_LARGE)
        elif timestamp:
            url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE, uuid=uuid)
            response = self._send_request(f"{url}/{timestamp}", FedoraRequestType.GET_BINARY_FILE_CONTENT_HISTORIE)
        else:
            response = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTENT)
        if response:
            file = io.BytesIO()
            file.write(response.content)
            file.seek(0)
            rep_bin_file = RepositoryBinaryFile(uuid, file)
            logger.debug(
                "core_repository_connector.get_binary_file.end",
                extra={
                    "uuid": uuid,
                    "key": rep_bin_file.sha_512,
                    "ident_cely_old": ident_cely_old,
                    "thumb_small": thumb_small,
                    "thumb_large": thumb_large,
                    "transaction": self.transaction_uid,
                },
            )
            return rep_bin_file
        else:
            return None

    def update_binary_file(
        self, file_name, content_type, file: io.BytesIO, uuid: str, save_thumbs: bool = True
    ) -> RepositoryBinaryFile:
        logger.debug(
            "core_repository_connector.update_binary_file.start",
            extra={
                "file": file_name,
                "ident_cely": self.record.ident_cely,
                "transaction": self.transaction_uid,
                "option": save_thumbs,
            },
        )
        rep_bin_file = RepositoryBinaryFile(uuid, file, file_name)
        data = file.read()
        file_sha_512 = hashlib.sha512(data).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Digest": f"sha-512={file_sha_512}",
        }
        url = self._get_request_url(FedoraRequestType.UPDATE_BINARY_FILE_CONTENT, uuid=uuid)
        self._send_request(url, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT, headers=headers, data=data)
        if save_thumbs:
            self.save_thumbs(file_name, file, uuid, True)
        logger.debug(
            "core_repository_connector.update_binary_file.end",
            extra={"uuid": uuid, "ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        return rep_bin_file

    def delete_binary_file(self, soubor):
        from core.models import Soubor

        soubor: Soubor
        if soubor.repository_uuid:
            logger.debug(
                "core_repository_connector.delete_binary_file.start",
                extra={
                    "uuid": soubor.repository_uuid,
                    "ident_cely": self.record.ident_cely,
                    "transaction": self.transaction_uid,
                },
            )
            headers = {"Content-Type": "application/sparql-update"}
            data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'deleted'}"
            url = self._get_request_url(FedoraRequestType.DELETE_BINARY_FILE, uuid=soubor.repository_uuid)
            self._send_request(url, FedoraRequestType.DELETE_BINARY_FILE, headers=headers, data=data)
            logger.debug(
                "core_repository_connector.delete_binary_file.end",
                extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely},
            )
        else:
            logger.debug(
                "core_repository_connector.delete_binary_file.no_repository_uuid",
                extra={
                    "pk": soubor.pk,
                    "ident_cely": self.record.ident_cely,
                    "transaction": self.transaction_uid,
                },
            )

    def delete_binary_file_completely(self, soubor):
        logger.debug(
            "core_repository_connector.delete_binary_file_completely.start",
            extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely},
        )
        from core.models import Soubor

        soubor: Soubor
        url = self._get_request_url(FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY, uuid=soubor.repository_uuid)
        self._send_request(url, FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY)
        logger.debug(
            "core_repository_connector.delete_binary_file_completely.end",
            extra={
                "uuid": soubor.repository_uuid,
                "ident_cely": self.record.ident_cely,
                "transaction": self.transaction_uid,
            },
        )

    def delete_container(self, delete_tombstone=True):
        self._delete_link()
        logger.debug(
            "core_repository_connector.delete_container.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.DELETE_CONTAINER)
        self._send_request(url, FedoraRequestType.DELETE_CONTAINER)
        if delete_tombstone:
            url = self._get_request_url(FedoraRequestType.DELETE_TOMBSTONE)
            self._send_request(url, FedoraRequestType.DELETE_TOMBSTONE)
        logger.debug(
            "core_repository_connector.delete_container.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def _delete_link(self, ident_cely=None):
        logger.debug(
            "core_repository_connector.delete_link.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.DELETE_LINK_CONTAINER, ident_cely=ident_cely)
        self._send_request(url, FedoraRequestType.DELETE_LINK_CONTAINER)
        url = self._get_request_url(FedoraRequestType.DELETE_LINK_TOMBSTONE, ident_cely=ident_cely)
        self._send_request(url, FedoraRequestType.DELETE_LINK_TOMBSTONE)
        logger.debug(
            "core_repository_connector.delete_link.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def record_deletion(self):
        logger.debug(
            "core_repository_connector.record_deletion.start",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )
        url = self._get_request_url(FedoraRequestType.GET_DELETED_LINK, ident_cely=self.record.ident_cely)
        result = self._send_request(url, FedoraRequestType.GET_DELETED_LINK)
        if result is not None and result.status_code != 404:
            logger.debug(
                "core_repository_connector.record_deletion.already_exists",
                extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
        else:
            logger.debug(
                "core_repository_connector.record_deletion.adding_link",
                extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
            )
            headers = {"Content-Type": "application/sparql-update"}
            data = """PREFIX dcterms: <http://purl.org/dc/terms/>
DELETE WHERE { <> dcterms:type ?restored .};
INSERT DATA { <> dcterms:type "deleted" .};"""
            url = self._get_request_url(FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS)
            self._send_request(url, FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS, headers=headers, data=data)
            headers = {"Slug": self.record.ident_cely, "Content-Type": "text/turtle"}
            data = (
                "@prefix ore: <http://www.openarchives.org/ore/terms/> . "
                "@prefix dcterms: <http://purl.org/dc/terms/> . "
                f"<> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.record.ident_cely}> ; "
                f"dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
            )
            url = self._get_request_url(FedoraRequestType.RECORD_DELETION_ADD_MARK)
            self._send_request(url, FedoraRequestType.RECORD_DELETION_ADD_MARK, headers=headers, data=data)
        logger.debug(
            "core_repository_connector.record_deletion.end",
            extra={"ident_cely": self.record.ident_cely, "transaction": self.transaction_uid},
        )

    def record_ident_change(self, ident_cely_old, delete_container=True):
        logger.debug(
            "core_repository_connector.record_ident_change.start",
            extra={
                "ident_cely": self.record.ident_cely,
                "ident_cely_old": ident_cely_old,
                "transaction": self.transaction_uid,
            },
        )
        if ident_cely_old is None or self.record.ident_cely == ident_cely_old:
            logger.error(
                "core_repository_connector.record_ident_change.no_ident_cely_old",
                extra={"ident_cely": self.record.ident_cely, "ident_cely_old": ident_cely_old},
            )
            raise IdentChangeFedoraError()
        base_url = f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/"
        ident_cely_new = self.record.ident_cely
        data = (
            f"INSERT DATA {{<> <http://purl.org/dc/terms/replaces> "
            f"<{base_url}{settings.FEDORA_SERVER_NAME}/record/{ident_cely_old}>}}"
        )
        headers = {"Content-Type": "application/sparql-update"}
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2, ident_cely=ident_cely_new)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2, headers=headers, data=data)
        headers = {"Slug": ident_cely_old, "Content-Type": "text/turtle"}
        data = (
            "@prefix ore: <http://www.openarchives.org/ore/terms/> . "
            "@prefix dcterms: <http://purl.org/dc/terms/> . "
            f"<> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{ident_cely_old}> ; "
            f"dcterms:creator <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.user}> ."
        )
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4, headers=headers, data=data)

        if delete_container:
            url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_5, ident_cely=ident_cely_old)
            self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_5)

            self._delete_link(ident_cely_old)
        else:
            url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_6, ident_cely=ident_cely_old)
            headers = {
                "Content-Type": "application/sparql-update",
            }
            data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'deleted'}"
            self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_6, headers=headers, data=data)
        logger.debug(
            "core_repository_connector.record_ident_change.end",
            extra={
                "ident_cely": self.record.ident_cely,
                "ident_cely_old": ident_cely_old,
                "transaction": self.transaction_uid,
            },
        )
        from dokument.models import Dokument
        from pas.models import SamostatnyNalez
        from projekt.models import Projekt

        if (
            isinstance(self.record, Dokument)
            or isinstance(self.record, Projekt)
            or isinstance(self.record, SamostatnyNalez)
        ):
            for item in self.record.soubory.soubory.all():
                from core.models import Soubor

                item: Soubor
                item.nazev = item.nazev.replace(
                    ident_cely_old.replace("-", ""), self.record.ident_cely.replace("-", "")
                )
                item.save()
                self.migrate_binary_file(
                    item, include_content=True, check_if_exists=False, ident_cely_old=ident_cely_old
                )

    @classmethod
    def generate_thumb_for_single_file(cls, record) -> None:
        from core.models import Soubor
        from xml_generator.models import ModelWithMetadata

        if isinstance(record, int):
            record = Soubor.objects.get(pk=record)
        record: Soubor
        related_record: ModelWithMetadata = record.vazba.navazany_objekt
        fedora_transaction = FedoraTransaction()
        record.active_transaction = fedora_transaction
        conn = FedoraRepositoryConnector(related_record, fedora_transaction)
        if not conn.get_binary_file(record.repository_uuid, thumb_small=True) and not conn.get_binary_file(
            record, thumb_large=True
        ):
            rep_bin_file = conn.get_binary_file(record.repository_uuid)
            if rep_bin_file:
                conn.save_thumbs(record.nazev, rep_bin_file.content, record.repository_uuid)
        fedora_transaction.mark_transaction_as_closed()


class FedoraTransactionQueueClosedError(Exception):
    pass


class FedoraTransactionNoIDError(Exception):
    pass


class FedoraTransactionCommitFailedError(Exception):
    pass


class FedoraTransactionUnsupportedOperationError(Exception):
    pass


class FedoraTransactionOperation(Enum):
    COMMIT = 1
    ROLLBACK = 2


class FedoraTransactionPostCommitTasks(Enum):
    CREATE_LINK = 1


class FedoraTransactionResult(Enum):
    COMMITED = 1
    ABORTED = 2


class FedoraTransactionStatus(Enum):
    ACTIVE = 1
    COMMITTED = 2
    ABORTED = 3


class BaseFedoraTransaction(ABC):
    """
    Abstraktní základní třída pro Fedora transakce.

    Definuje společné rozhraní pro všechny typy Fedora transakcí.
    Podtřídy implementují konkrétní chování pro skutečné, testovací (dry-run)
    a mazací transakce.
    """

    def __init__(self):
        self.uid = None

    def mark_transaction_as_closed(self):
        """Označí transakci jako uzavřenou. Výchozí implementace neprovádí žádnou akci."""
        pass

    def rollback_transaction(self):
        """Provede rollback transakce. Výchozí implementace neprovádí žádnou akci."""
        pass


class DryRunFedoraTransaction(BaseFedoraTransaction):
    """
    Testovací (dry-run) Fedora transakce, která nevytváří skutečnou transakci v repozitáři.

    Používá se při importu dat, kdy se zápisy do Fedory provádí až samostatném kroku,
    aby nedocházelo k duplicitním úpravám jednotlivých kontejnerů.
    """

    def __init__(self):
        super().__init__()
        self.updated_ident_cely: set[str] = set()

    def add_updated_ident_cely(self, ident_cely: str):
        """
        Přidá identifikátor záznamu do množiny dotčených záznamů.

        Args:
            ident_cely: identifikátor záznamu (ident_cely)
        """
        self.updated_ident_cely.add(ident_cely)


class FedoraTransaction(BaseFedoraTransaction):
    """
    Třída pro správu transakcí ve Fedora repozitáři.

    Zapouzdřuje vytvoření, commit a rollback transakce v Fedora repozitáři.
    Při inicializaci vytváří novou transakci ve Fedoře (pokud není předáno
    existující uid). Výsledek transakce se ukládá do Redis pro zobrazení uživateli.

    Args:
        main_record: hlavní záznam (ModelWithMetadata), ke kterému se transakce váže
        transaction_user: uživatel provádějící transakci
        success_message: zpráva zobrazená při úspěšném dokončení
        error_message: zpráva zobrazená při chybě
        uid: existující UID transakce; pokud není zadáno, vytvoří se nová transakce
        request: HTTP request pro předání kontextu
        suppress_message: pokud True, neukládá výsledek transakce do Redis
        redirect_on_error: pokud True, při chybě provede přesměrování
        redirect_url: URL pro přesměrování při chybě

    Raises:
        FedoraTransactionNoIDError: pokud se nepodaří vytvořit transakci nebo získat její UID
    """

    def __init__(
        self,
        main_record: ModelWithMetadata = None,
        transaction_user=None,
        success_message=None,
        error_message=None,
        *,
        uid=None,
        request=None,
        suppress_message=False,
        redirect_on_error=False,
        redirect_url=None,
    ):
        super().__init__()
        from uzivatel.models import User

        self.main_record = main_record
        self.transaction_user = transaction_user
        self.success_message = success_message
        self.error_message = error_message
        transaction_user: User
        self.post_commit_tasks = {}
        if uid is None:
            self.__create_transaction()
        else:
            self.uid = uid
            logger.debug("core_repository_connector.FedoraTransaction.__init__", extra={"transaction": self.uid})
        self.request = request
        self.suppress_message = suppress_message
        self.__status = FedoraTransactionStatus.ACTIVE
        self.redirect_on_error = redirect_on_error
        self.redirect_url = redirect_url
        self.changes_count = 0

    def __str__(self):
        return self.uid

    @staticmethod
    def get_transaction_redis_key(ident_cely: str, transaction_user_id: int):
        """
        Vytvoří klíč pro uložení výsledku transakce do Redis.

        Args:
            ident_cely: identifikátor záznamu
            transaction_user_id: ID uživatele provádějícího transakci
        """
        return f"fedora-transaction-result-{ident_cely}-{transaction_user_id}"

    @property
    def _transaction_redis_key(self):
        return self.get_transaction_redis_key(self.main_record.ident_cely, self.transaction_user.id)

    @property
    def status(self):
        return self.__status

    def _save_transaction_result_to_redis(self, result: FedoraTransactionResult):
        """
        Uloží výsledek transakce (COMMITED/ABORTED) do Redis.

        Args:
            result: výsledek transakce (FedoraTransactionResult)
        """
        if self.main_record and self.transaction_user and not self.suppress_message:
            r = RedisConnector()
            redis_connection = r.get_connection()
            redis_connection.hset(self._transaction_redis_key, "status", str(result.value))
            if self.success_message:
                redis_connection.hset(self._transaction_redis_key, "success_message", str(self.success_message))
            if self.error_message:
                redis_connection.hset(self._transaction_redis_key, "error_message", str(self.error_message))

    def _send_transaction_request(self, operation=FedoraTransactionOperation.COMMIT):
        """
        Odešle požadavek na commit nebo rollback transakce do Fedory.

        Args:
            operation: typ operace (COMMIT nebo ROLLBACK)

        Raises:
            FedoraTransactionUnsupportedOperationError: pokud je zadána neplatná operace
            FedoraTransactionCommitFailedError: pokud Fedora vrátí chybový status
        """
        logger.debug(
            "core_repository_connector.FedoraTransaction.commit_transaction.start", extra={"transaction": self.uid}
        )
        url = (
            f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}"
            f"/rest/fcr:tx/{self.uid}"
        )
        auth = HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        if operation == FedoraTransactionOperation.COMMIT:
            response = requests.put(url, auth=auth, verify=False)
            try:
                self._save_transaction_result_to_redis(FedoraTransactionResult.COMMITED)
            except ResponseError as err:
                logger.error(
                    "core_repository_connector.FedoraTransaction._save_transaction_result_to_redis.commited.failed",
                    extra={"transaction": self.uid, "error": err},
                )
        elif operation == FedoraTransactionOperation.ROLLBACK:
            response = requests.delete(url, auth=auth, verify=False)
            try:
                self._save_transaction_result_to_redis(FedoraTransactionResult.ABORTED)
            except ResponseError as err:
                logger.error(
                    "core_repository_connector.FedoraTransaction._save_transaction_result_to_redis.rollback.failed",
                    extra={"transaction": self.uid, "error": err},
                )
        else:
            raise FedoraTransactionUnsupportedOperationError(operation)
        if not str(response.status_code).startswith("2"):
            logger.error(
                "core_repository_connector.FedoraTransaction.commit_transaction.failed",
                extra={"transaction": self.uid, "response": response.text},
            )
            raise FedoraTransactionCommitFailedError(response.text)
        logger.debug(
            "core_repository_connector.FedoraTransaction.commit_transaction.end", extra={"transaction": self.uid}
        )

    def rollback_transaction(self):
        """Provede rollback transakce ve Fedora repozitáři, pokud transakce ještě nebyla zrušena."""
        logger.debug(
            "core_repository_connector.FedoraTransaction.rollback_transaction.start", extra={"transaction": self.uid}
        )
        if self.__status != FedoraTransactionStatus.ABORTED:
            self._send_transaction_request(FedoraTransactionOperation.ROLLBACK)
            self.__status = FedoraTransactionStatus.ABORTED
        logger.debug(
            "core_repository_connector.FedoraTransaction.rollback_transaction.end", extra={"transaction": self.uid}
        )

    def mark_transaction_as_closed(self):
        """
        Uzavře transakci: provede commit, spustí post-commit úlohy a případně aktualizaci digiarchívu.
        """
        logger.debug(
            "core_repository_connector.FedoraTransaction.mark_transaction_as_closed.start",
            extra={"transaction": self.uid, "value": self.post_commit_tasks.keys()},
        )
        self._send_transaction_request()
        self._perform_post_commit_tasks()
        if settings.DIGIARCHIV_URL != "" and self.changes_count > 0:
            self.call_digiarchiv_update()
        self.__status = FedoraTransactionStatus.COMMITTED
        logger.debug(
            "core_repository_connector.FedoraTransaction.mark_transaction_as_closed.end",
            extra={"transaction": self.uid},
        )

    def _perform_post_commit_tasks(self):
        """Provede úlohy naplánované po commitu transakce (např. vytvoření linků) v nové transakci."""
        if len(self.post_commit_tasks) == 0:
            return
        new_transaction = FedoraTransaction()
        for key, value in self.post_commit_tasks.items():
            task, _ = key
            if task == FedoraTransactionPostCommitTasks.CREATE_LINK:
                if not isinstance(value, list) or len(value) != 3:
                    logger.error(
                        "core_repository_connector.FedoraTransaction._perform_post_commit_tasks." "parameter_error",
                        extra={"transaction": self.uid},
                    )
                record, ident_cely, old_ident_cely = value
                record.ident_cely = old_ident_cely
                connector = FedoraRepositoryConnector(record, new_transaction)
                if not connector.link_exists():
                    connector.create_link(ident_cely_proxy=ident_cely)
        new_transaction.mark_transaction_as_closed()

    def __create_transaction(self):
        """
        Vytvoří novou transakci ve Fedoře.

        Raises:
            FedoraTransactionNoIDError: pokud se nepodaří vytvořit transakci nebo získat její UID
        """
        logger.debug("core_repository_connector.FedoraTransaction.__create_transaction.start")
        url = (
            f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/fcr:tx"
        )
        auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        response = requests.post(url, auth=auth, verify=False)
        if not str(response.status_code).startswith("2"):
            logger.error(
                "core_repository_connector.FedoraTransaction.__create_transaction.failed",
                extra={"response": response.text},
            )
            raise FedoraTransactionNoIDError(response.text)
        uuid_pattern = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
        match = re.search(uuid_pattern, response.headers.get("Location"))
        if match:
            self.uid = match.group()
            logger.debug(
                "core_repository_connector.FedoraTransaction.__create_transaction", extra={"transaction": self.uid}
            )
        else:
            logger.error(
                "core_repository_connector.FedoraTransaction.__create_transaction.no_uid",
                extra={"response": response.text},
            )
            raise FedoraTransactionNoIDError(response.text)

    @staticmethod
    def call_digiarchiv_update():
        """
        Spustí asynchronní aktualizaci digiarchívu přes Celery.

        Kontroluje, zda úloha již není naplánovaná nebo běží, aby nedocházelo k duplicitnímu spuštění.
        """
        from cron.tasks import call_digiarchiv_update_task

        logger.debug("core_repository_connector.FedoraTransaction.call_digiarchiv_update.start")
        try:
            app = Celery("webclient")
            app.config_from_object("django.conf:settings", namespace="CELERY")
            app.autodiscover_tasks()
            i = app.control.inspect(["worker1@amcr"])
            queues = (
                i.scheduled(),
                i.active(),
            )
        except Exception as e:
            logger.warning(
                "core_repository_connector.FedoraTransaction.call_digiarchiv_update.Celery_warning",
                extra={"error": e, "app": app},
            )
            call_digiarchiv_update_task.apply_async()
        for queue in queues:
            if queue is None:
                logger.warning(
                    "core_repository_connector.FedoraTransaction.call_digiarchiv_update.warning",
                    extra={"key": i, "queue": queues},
                )
                break
            for queue_name, queue_tasks in queue.items():
                for task in queue_tasks:
                    if "request" in task and "call_digiarchiv_update_task" in task.get("request").get("name").lower():
                        logger.debug(
                            "core_repository_connector.FedoraTransaction.call_digiarchiv_update." "already_scheduled"
                        )
                        return
        call_digiarchiv_update_task.apply_async()
        logger.debug("core_repository_connector.FedoraTransaction.call_digiarchiv_update.end")


class FedoraDeletionOnlyTransaction(FedoraTransaction):
    """
    Fedora transakce určená pouze pro mazání záznamů při importu dat.

    Na rozdíl od běžné FedoraTransaction sbírá identifikátory dotčených záznamů, které jsou navázané
    na mazaný záznam a musejí být aktualizovány v následujícím kroku,
    podobně jako DryRunFedoraTransaction.
    """

    def __init__(self):
        super().__init__()
        self.updated_ident_cely: set[str] = set()

    def add_updated_ident_cely(self, ident_cely: str):
        """
        Přidá identifikátor záznamu do množiny dotčených záznamů.

        Args:
            ident_cely: identifikátor záznamu (ident_cely)
        """
        self.updated_ident_cely.add(ident_cely)
