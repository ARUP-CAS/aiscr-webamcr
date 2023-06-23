import hashlib
import io
import logging
import re
from enum import Enum
from typing import Union, Optional

import requests
from django.conf import settings
from django.contrib.gis.db.models.functions import AsGML, AsWKT
from requests.auth import HTTPBasicAuth

from xml_generator.generator import DocumentGenerator

logger = logging.getLogger(__name__)


class RepositoryBinaryFile:
    @property
    def size_mb(self):
        return self.size / 1024 ** 2

    def __init__(self, uuid: str, content: io.BytesIO, filename: Union[str, None] = None):
        self.uuid = uuid
        self.content = content
        self.filename = filename
        self.size = content.getbuffer().nbytes
        self.content.seek(0)


class FedoraRequestType(Enum):
    GET_CONTAINER = 1
    CREATE_CONTAINER = 2
    CREATE_LINK = 3
    CREATE_METADATA = 4
    UPDATE_METADATA = 5
    GET_METADATA = 6
    CREATE_BINARY_FILE_CONTAINER = 7
    GET_BINARY_FILE_CONTAINER = 8
    CREATE_BINARY_FILE = 9
    CREATE_BINARY_FILE_CONTENT = 10
    CREATE_BINARY_FILE_PREVIEW = 11
    GET_BINARY_FILE_CONTENT = 12
    UPDATE_BINARY_FILE_CONTENT = 13


class FedoraRepositoryConnector:
    def __init__(self, record):
        from core.models import ModelWithMetadata

        record: ModelWithMetadata
        self.record = record

    def _get_model_name(self):
        class_name = self.record.__class__.__name__.lower()
        # Conversion of capitals
        # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        name = re.sub(r'(?<!^)(?=[A-Z])', '-', class_name).lower()
        return name

    def _get_request_url(self, request_type: FedoraRequestType, *, uuid=None) -> Optional[str]:
        base_url = f"http://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/" \
                   f"{settings.FEDORA_SERVER_NAME}"
        if request_type == FedoraRequestType.CREATE_CONTAINER:
            return f"{base_url}/record/"
        elif request_type in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.CREATE_METADATA,
                              FedoraRequestType.CREATE_BINARY_FILE_CONTAINER):
            return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type == FedoraRequestType.CREATE_LINK:
            return f"{base_url}/model/{self._get_model_name()}/member"
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.GET_METADATA):
            return f"{base_url}/record/{self.record.ident_cely}/metadata"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE):
            return f"{base_url}/record/{self.record.ident_cely}/file"
        elif request_type == FedoraRequestType.CREATE_BINARY_FILE_CONTENT:
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTENT, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT):
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig"

    @staticmethod
    def _send_request(url: str, request_type: FedoraRequestType, *,
                      headers=None, data=None) -> Optional[requests.Response]:
        logger.debug("core_repository_connector._send_request.start", extra={"url": url, "request_type": request_type})
        auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        response = None
        if request_type in (FedoraRequestType.CREATE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE_CONTAINER):
            response = requests.post(url, headers=headers, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.GET_METADATA,
                              FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.GET_BINARY_FILE_CONTENT):
            response = requests.get(url, headers=headers, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.CREATE_LINK,):
            response = requests.post(url, headers=headers, data=data.encode('utf-8'), auth=auth, verify=False)
        elif request_type in (FedoraRequestType.CREATE_METADATA, FedoraRequestType.CREATE_BINARY_FILE_CONTENT):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT):
            response = requests.put(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type == FedoraRequestType.CREATE_BINARY_FILE:
            response = requests.post(url, auth=auth, verify=False)
        logger.debug("core_repository_connector._send_request.response", extra={"text": response.text,
                                                                                "status_code": response.status_code})
        return response

    def _create_container(self):
        logger.debug("core_repository_connector._create_container.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.CREATE_CONTAINER)
        headers = {
            'Slug': self.record.ident_cely
        }
        self._send_request(url, FedoraRequestType.CREATE_CONTAINER, headers=headers)
        logger.debug("core_repository_connector._create_container.end", extra={"ident_cely": self.record.ident_cely})

    def _create_link(self):
        logger.debug("core_repository_connector._create_link.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.CREATE_LINK)
        headers = {
            'Slug': self.record.ident_cely,
            'Content-Type': 'text/turtle'
        }
        data = f"@prefix ore: <http://www.openarchives.org/ore/terms/> " \
               f". <> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self._get_model_name()}>"
        self._send_request(url, FedoraRequestType.CREATE_LINK, headers=headers, data=data)
        logger.debug("core_repository_connector._create_link.end", extra={"ident_cely": self.record.ident_cely})

    def _check_container(self):
        logger.debug("core_repository_connector._check_container.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result.status_code == 404 or "not found" in result.text:
            self._create_container()
            self._create_link()
        logger.debug("core_repository_connector._check_container.end", extra={"ident_cely": self.record.ident_cely})

    def _create_binary_file_container(self):
        logger.debug("core_repository_connector._create_binary_file_container.start",
                     extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTAINER)
        headers = {
            "Slug": "file"
        }
        self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTAINER, headers=headers)
        logger.debug("core_repository_connector._create_binary_file_container.end",
                     extra={"ident_cely": self.record.ident_cely})

    def _check_binary_file_container(self):
        logger.debug("core_repository_connector._check_binary_file_containe.start",
                     extra={"ident_cely": self.record.ident_cely})
        self._check_container()
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTAINER)
        if result.status_code == 404 or "not found" in result.text:
            self._create_binary_file_container()
        logger.debug("core_repository_connector._check_binary_file_container.end",
                     extra={"ident_cely": self.record.ident_cely})

    def _generate_metadata(self):
        logger.debug("core_repository_connector._generate_metadata.start",
                     extra={"ident_cely": self.record.ident_cely})
        document_generator = DocumentGenerator(self.record)
        document = document_generator.generate_document()
        hash512 = hashlib.sha512(document).hexdigest()
        logger.debug("core_repository_connector._generate_metadata.end", extra={"ident_cely": self.record.ident_cely})
        return document, hash512

    def get_metadata(self, update=False) -> bytes:
        logger.debug("core_repository_connector.get_metadata.start", extra={"ident_cely": self.record.ident_cely})
        self.save_metadata(update)
        url = self._get_request_url(FedoraRequestType.GET_METADATA)
        response = self._send_request(url, FedoraRequestType.GET_METADATA)
        logger.debug("core_repository_connector.get_metadata.end", extra={"ident_cely": self.record.ident_cely})
        return response.content

    def save_metadata(self, update=True):
        logger.debug("core_repository_connector.save_metadata.start", extra={"ident_cely": self.record.ident_cely})
        self._check_container()
        url = self._get_request_url(FedoraRequestType.GET_METADATA)
        result = self._send_request(url, FedoraRequestType.GET_METADATA)

        def generate_metadata():
            document_func, hash512 = self._generate_metadata()
            headers_func = {
                "Content-Type": "application/xml",
                "Content-Disposition": 'attachment; filename="metadata.xml"',
                "Digest": f"sha-512={hash512}"
            }
            return document_func, headers_func
        if result.status_code == 404 or "not found" in result.text:
            document, headers = generate_metadata()
            headers["slug"] = "metadata"
            url = self._get_request_url(FedoraRequestType.CREATE_METADATA)
            self._send_request(url, FedoraRequestType.CREATE_METADATA, headers=headers, data=document)
        elif update is True:
            document, headers = generate_metadata()
            url = self._get_request_url(FedoraRequestType.UPDATE_METADATA)
            self._send_request(url, FedoraRequestType.UPDATE_METADATA, headers=headers, data=document)
        logger.debug("core_repository_connector.save_metadata.end", extra={"ident_cely": self.record.ident_cely})

    def save_binary_file(self, file_name, content_type, file: io.BytesIO) -> RepositoryBinaryFile:
        logger.debug("core_repository_connector.save_binary_file.start",
                     extra={"file_name": file_name, "ident_cely": self.record.ident_cely})
        self._check_binary_file_container()
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE)
        result = self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE)
        uuid = result.text.split("/")[-1]
        rep_bin_file = RepositoryBinaryFile(uuid, file, file_name)
        data = file.read()
        file_sha_512 = hashlib.sha512(data).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Digest": f"sha-512={file_sha_512}",
            "Slug": "orig"
        }
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTENT, uuid=uuid)
        self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTENT, headers=headers, data=data)
        logger.debug("core_repository_connector.save_binary_file.end",
                     extra={"uuid": uuid, "ident_cely": self.record.ident_cely})
        return rep_bin_file

    def get_binary_file(self, uuid) -> RepositoryBinaryFile:
        logger.debug("core_repository_connector.get_binary_file.start", extra={"uuid": uuid})
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT, uuid=uuid)
        response = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTENT)
        file = io.BytesIO()
        file.write(response.content)
        file.seek(0)
        rep_bin_file = RepositoryBinaryFile(uuid, file)
        logger.debug("core_repository_connector.get_binary_file.end", extra={"uuid": uuid})
        return rep_bin_file

    def update_binary_file(self, file_name, content_type, file: io.BytesIO, uuid: str) -> RepositoryBinaryFile:
        logger.debug("core_repository_connector.update_binary_file.start",
                     extra={"file_name": file_name, "ident_cely": self.record.ident_cely})
        rep_bin_file = RepositoryBinaryFile(uuid, file, file_name)
        data = file.read()
        file_sha_512 = hashlib.sha512(data).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Digest": f"sha-512={file_sha_512}"
        }
        url = self._get_request_url(FedoraRequestType.UPDATE_BINARY_FILE_CONTENT, uuid=uuid)
        self._send_request(url, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT, headers=headers, data=data)
        logger.debug("core_repository_connector.save_binary_file.end",
                     extra={"uuid": uuid, "ident_cely": self.record.ident_cely})
        return rep_bin_file
