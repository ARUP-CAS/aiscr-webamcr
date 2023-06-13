import hashlib
import logging
from enum import Enum
from typing import Union, Optional

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from projekt.models import Projekt
from xml_generator.generator import DocumentGenerator

logger = logging.getLogger(__name__)


class FedoraRequestType(Enum):
    GET_CONTAINER = 1
    CREATE_CONTAINER = 2
    CREATE_LINK = 3
    CREATE_METADATA = 4
    UPDATE_METADATA = 5
    GET_METADATA = 6


class FedoraRepositoryConnector:
    def _get_model_name(self):
        if isinstance(self.record, Projekt):
            return "projekt"

    def _get_request_url(self, request_type: FedoraRequestType, *, uuid=None) -> Optional[str]:
        base_url = f"http://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/" \
                   f"{settings.FEDORA_SERVER_NAME}"
        if request_type == FedoraRequestType.CREATE_CONTAINER:
            return f"{base_url}/record/"
        elif request_type == FedoraRequestType.GET_CONTAINER:
            return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type == FedoraRequestType.CREATE_LINK:
            return f"{base_url}/model/{self._get_model_name()}/member"
        elif request_type == FedoraRequestType.CREATE_METADATA:
            return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.GET_METADATA):
            return f"{base_url}/record/{self.record.ident_cely}/metadata"

    @staticmethod
    def _send_request(url: str, request_type: FedoraRequestType, *,
                      headers=None, data=None) -> Optional[requests.Response]:
        auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        response = None
        if request_type in (FedoraRequestType.CREATE_CONTAINER,):
            response = requests.post(url, headers=headers, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.GET_METADATA):
            response = requests.get(url, headers=headers, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.CREATE_LINK,):
            response = requests.post(url, headers=headers, data=data.encode('utf-8'), auth=auth, verify=False)
        elif request_type in (FedoraRequestType.CREATE_METADATA,):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.UPDATE_METADATA,):
            response = requests.put(url, headers=headers, data=data, auth=auth, verify=False)
        logger.debug("core_repository_connector._send_request.response", extra={"text": response.text,
                                                                                "status_code": response.status_code})
        print(response.text)
        return response

    def _create_container(self):
        url = self._get_request_url(FedoraRequestType.CREATE_CONTAINER)
        headers = {
            'Slug': self.record.ident_cely
        }
        self._send_request(url, FedoraRequestType.CREATE_CONTAINER, headers=headers)

    def _create_link(self):
        url = self._get_request_url(FedoraRequestType.CREATE_LINK)
        headers = {
            'Slug': self.record.ident_cely,
            'Content-Type': 'text/turtle'
        }
        data = f"@prefix ore: <http://www.openarchives.org/ore/terms/> " \
               f". <> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self._get_model_name()}>"
        self._send_request(url, FedoraRequestType.CREATE_LINK, headers=headers, data=data)

    def check_container(self):
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result.status_code == 404:
            self._create_container()
            self._create_link()

    def _generate_metadata(self):
        document_generator = DocumentGenerator(self.record)
        document = document_generator.generate_document()
        hash512 = hashlib.sha512(document).hexdigest()
        return document, hash512

    def get_metadata(self) -> bytes:
        self.save_metadata(True)
        url = self._get_request_url(FedoraRequestType.GET_METADATA)
        response = self._send_request(url, FedoraRequestType.GET_METADATA)
        return response.content

    def save_metadata(self, update=True):
        self.check_container()
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        document, hash512 = self._generate_metadata()
        headers = {
            'Content-Type': 'application/xml',
            'Content-Disposition': 'attachment; filename="metadata.xml"',
            'Digest': f'sha-512={hash512}',
            'Slug': self.record.ident_cely
        }
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result.status_code == 404:
            url = self._get_request_url(FedoraRequestType.CREATE_METADATA)
            self._send_request(url, FedoraRequestType.CREATE_METADATA, headers=headers, data=document)
        elif update is True:
            url = self._get_request_url(FedoraRequestType.UPDATE_METADATA)
            self._send_request(url, FedoraRequestType.UPDATE_METADATA, headers=headers, data=document)

    def __init__(self, record: Union[Projekt]):
        self.record = record
