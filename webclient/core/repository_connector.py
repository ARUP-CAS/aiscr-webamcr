import hashlib
import io
import logging
from enum import Enum
from typing import Union, Optional

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from core.utils import get_mime_type
from xml_generator.generator import DocumentGenerator

logger = logging.getLogger(__name__)


class FedoraValidationError(Exception):
    pass

class FedoraError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(self.message)


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
        return self.size / 1024 ** 2

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
    GET_LINK = 14
    DELETE_CONTAINER = 15
    DELETE_TOMBSTONE = 16
    RECORD_DELETION_MOVE_MEMBERS = 17
    RECORD_DELETION_ADD_MARK = 18
    CHANGE_IDENT_CONNECT_RECORDS_1 = 19
    CHANGE_IDENT_CONNECT_RECORDS_2 = 20
    CHANGE_IDENT_CONNECT_RECORDS_3 = 21
    CHANGE_IDENT_CONNECT_RECORDS_4 = 22
    DELETE_LINK_CONTAINER = 23
    DELETE_LINK_TOMBSTONE = 24
    DELETE_BINARY_FILE = 25
    DELETE_BINARY_FILE_COMPLETELY = 26
    GET_DELETED_LINK = 27


class FedoraRepositoryConnector:
    def __init__(self, record):
        from core.models import ModelWithMetadata

        record: ModelWithMetadata
        self.record = record

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

    def _get_request_url(self, request_type: FedoraRequestType, *, uuid=None, ident_cely=None) -> Optional[str]:
        base_url = f"http://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/" \
                   f"{settings.FEDORA_SERVER_NAME}"
        if request_type == FedoraRequestType.CREATE_CONTAINER:
            return f"{base_url}/record/"
        elif request_type in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.CREATE_METADATA,
                              FedoraRequestType.CREATE_BINARY_FILE_CONTAINER, FedoraRequestType.DELETE_CONTAINER,
                              FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS):
            return f"{base_url}/record/{self.record.ident_cely}"
        elif request_type in (FedoraRequestType.CREATE_LINK, ):
            return f"{base_url}/model/{self._get_model_name()}/member"
        elif request_type in (FedoraRequestType.GET_LINK, FedoraRequestType.DELETE_LINK_CONTAINER):
            return f"{base_url}/model/{self._get_model_name()}/member/{self.record.ident_cely}"
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.GET_METADATA):
            return f"{base_url}/record/{self.record.ident_cely}/metadata"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE):
            return f"{base_url}/record/{self.record.ident_cely}/file"
        elif request_type in (FedoraRequestType.CREATE_BINARY_FILE_CONTENT, FedoraRequestType.DELETE_BINARY_FILE,
                              FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY):
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}"
        elif request_type in (FedoraRequestType.GET_BINARY_FILE_CONTENT, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT):
            return f"{base_url}/record/{self.record.ident_cely}/file/{uuid}/orig"
        elif request_type == FedoraRequestType.DELETE_TOMBSTONE:
            return f"{base_url}/record/{self.record.ident_cely}/fcr:tombstone"
        elif request_type == FedoraRequestType.DELETE_LINK_TOMBSTONE:
            return f"{base_url}/model/{self._get_model_name()}/member/{self.record.ident_cely}/fcr:tombstone"
        elif request_type in (FedoraRequestType.RECORD_DELETION_ADD_MARK,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4):
            return f"{base_url}/model/deleted/member"
        elif request_type in (FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_1,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_3):
            return f"{base_url}/record/{ident_cely}"
        elif request_type == FedoraRequestType.GET_DELETED_LINK:
            return f"{base_url}/model/deleted/member/{ident_cely}"

    @staticmethod
    def _send_request(url: str, request_type: FedoraRequestType, *,
                      headers=None, data=None) -> Optional[requests.Response]:
        logger.debug("core_repository_connector._send_request.start", extra={"url": url, "request_type": request_type})
        if request_type in (FedoraRequestType.DELETE_CONTAINER, FedoraRequestType.DELETE_TOMBSTONE,
                            FedoraRequestType.DELETE_LINK_CONTAINER, FedoraRequestType.DELETE_LINK_TOMBSTONE):
            auth = HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        else:
            auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        response = None
        if request_type in (FedoraRequestType.CREATE_CONTAINER, FedoraRequestType.CREATE_BINARY_FILE_CONTAINER):
            response = requests.post(url, headers=headers, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.GET_METADATA,
                              FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.GET_BINARY_FILE_CONTENT,
                              FedoraRequestType.GET_LINK, FedoraRequestType.GET_DELETED_LINK):
            try:
                response = requests.get(url, headers=headers, auth=auth, verify=False)
            except requests.exceptions.RequestException:
                return None
        elif request_type in (FedoraRequestType.CREATE_METADATA, FedoraRequestType.RECORD_DELETION_ADD_MARK,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4,
                              FedoraRequestType.CREATE_LINK):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.CREATE_BINARY_FILE_CONTENT, ):
            response = requests.post(url, headers=headers, data=data, auth=auth, verify=False, timeout=10)
        elif request_type in (FedoraRequestType.UPDATE_METADATA, FedoraRequestType.UPDATE_BINARY_FILE_CONTENT):
            response = requests.put(url, headers=headers, data=data, auth=auth, verify=False)
        elif request_type == FedoraRequestType.CREATE_BINARY_FILE:
            response = requests.post(url, auth=auth, verify=False)
        elif request_type in (FedoraRequestType.DELETE_CONTAINER, FedoraRequestType.DELETE_TOMBSTONE,
                              FedoraRequestType.DELETE_LINK_CONTAINER, FedoraRequestType.DELETE_LINK_TOMBSTONE,
                              FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY):
            response = requests.delete(url, auth=auth)
        elif request_type in (FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_1,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
                              FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_3,
                              FedoraRequestType.DELETE_BINARY_FILE):
            response = requests.patch(url, auth=auth, headers=headers, data=data)
        if request_type not in (FedoraRequestType.GET_CONTAINER, FedoraRequestType.GET_METADATA,
                                FedoraRequestType.GET_BINARY_FILE_CONTAINER, FedoraRequestType.GET_BINARY_FILE_CONTENT,
                                FedoraRequestType.GET_LINK, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_1,
                                FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2,
                                FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_3, FedoraRequestType.GET_DELETED_LINK,
                                ):
            if str(response.status_code)[0] == "2":
                logger.debug("core_repository_connector._send_request.response.ok",
                             extra={"text": response.text, "status_code": response.status_code})
            else:
                logger.error("core_repository_connector._send_request.response.error",
                             extra={"text": response.text, "status_code": response.status_code})
                raise FedoraError(response.text, response.status_code)
        else:
            logger.debug("core_repository_connector._send_request.response",
                         extra={"text": response.text, "status_code": response.status_code})
        return response

    def _create_container(self):
        logger.debug("core_repository_connector._create_container.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.CREATE_CONTAINER)
        headers = {
            'Slug': self.record.ident_cely,
            'Link': '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"'
        }
        self._send_request(url, FedoraRequestType.CREATE_CONTAINER, headers=headers)
        self._create_link()
        logger.debug("core_repository_connector._create_container.end", extra={"ident_cely": self.record.ident_cely})

    def _create_link(self):
        logger.debug("core_repository_connector._create_link.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.CREATE_LINK)
        headers = {
            'Slug': self.record.ident_cely,
            'Content-Type': 'text/turtle'
        }
        data = "@prefix ore: <http://www.openarchives.org/ore/terms/> " \
               f". <> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.record.ident_cely}>"
        self._send_request(url, FedoraRequestType.CREATE_LINK, headers=headers, data=data)
        logger.debug("core_repository_connector._create_link.end", extra={"ident_cely": self.record.ident_cely})

    def container_exists(self):
        logger.debug("core_repository_connector._container_exists.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result.status_code == 404 or "not found" in result.text:
            logger.debug("core_repository_connector._container_exists.false",
                         extra={"ident_cely": self.record.ident_cely})
            return False
        logger.debug("core_repository_connector._container_exists.true", extra={"ident_cely": self.record.ident_cely})
        return True

    def _check_container(self):
        logger.debug("core_repository_connector._check_container.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.GET_CONTAINER)
        result = self._send_request(url, FedoraRequestType.GET_CONTAINER)
        if result.status_code == 404 or "not found" in result.text:
            self._create_container()
        url = self._get_request_url(FedoraRequestType.GET_LINK)
        result = self._send_request(url, FedoraRequestType.GET_LINK)
        if result.status_code == 404 or "not found" in result.text:
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
        rep_bin_file = RepositoryBinaryFile(result.text, file, file_name)
        data = file.read()
        file_sha_512 = hashlib.sha512(data).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{file_name}"'.encode("utf-8"),
            "Digest": f"sha-512={file_sha_512}",
            "Slug": "orig"
        }
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTENT, uuid=uuid)
        self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTENT, headers=headers, data=data)
        logger.debug("core_repository_connector.save_binary_file.end",
                     extra={"url": uuid, "ident_cely": self.record.ident_cely})
        return rep_bin_file

    def migrate_binary_file(self, soubor, include_content=True) -> Optional[RepositoryBinaryFile]:
        from core.models import Soubor
        soubor: Soubor
        logger.debug("core_repository_connector.migrate_binary_file.start", extra={"soubor": soubor.pk})
        if soubor.repository_uuid is not None:
            return None
        self._check_binary_file_container()
        url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE)
        result = self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE)
        uuid = result.text.split("/")[-1]
        soubor.path = RepositoryBinaryFile.get_url_without_domain(result.text)
        soubor.suppress_signal = True
        soubor.save()
        if include_content:
            with open(soubor.path, mode="rb") as file:
                data = file.read()
            data = io.BytesIO(data)
            soubor.nazev = soubor.nazev
            soubor.save()
            content_type = get_mime_type(soubor.name)
            rep_bin_file = RepositoryBinaryFile(uuid, data, soubor.nazev)
            file_sha_512 = hashlib.sha512(data).hexdigest()
            headers = {
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{soubor.nazev}"'.encode("utf-8"),
                "Digest": f"sha-512={file_sha_512}",
                "Slug": "orig"
            }
            url = self._get_request_url(FedoraRequestType.CREATE_BINARY_FILE_CONTENT, uuid=uuid)
            self._send_request(url, FedoraRequestType.CREATE_BINARY_FILE_CONTENT, headers=headers, data=data)
            logger.debug("core_repository_connector.migrate_binary_file.end",
                         extra={"url": uuid, "ident_cely": self.record.ident_cely})
            return rep_bin_file

    def get_binary_file(self, uuid) -> RepositoryBinaryFile:
        logger.debug("core_repository_connector.get_binary_file.start", extra={"url": uuid})
        url = self._get_request_url(FedoraRequestType.GET_BINARY_FILE_CONTENT, uuid=uuid)
        response = self._send_request(url, FedoraRequestType.GET_BINARY_FILE_CONTENT)
        file = io.BytesIO()
        file.write(response.content)
        file.seek(0)
        rep_bin_file = RepositoryBinaryFile(uuid, file)
        logger.debug("core_repository_connector.get_binary_file.end", extra={"url": uuid})
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
        logger.debug("core_repository_connector.update_binary_file.end",
                     extra={"url": uuid, "ident_cely": self.record.ident_cely})
        return rep_bin_file

    def delete_binary_file(self, soubor):
        from core.models import Soubor
        soubor: Soubor
        logger.debug("core_repository_connector.delete_binary_file.start",
                     extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely})
        headers = {
            'Content-Type': 'application/sparql-update'
        }
        data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'deleted'}"
        url = self._get_request_url(FedoraRequestType.DELETE_BINARY_FILE, uuid=soubor.repository_uuid)
        self._send_request(url, FedoraRequestType.DELETE_BINARY_FILE, headers=headers, data=data)
        logger.debug("core_repository_connector.delete_binary_file.end",
                     extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely})

    def delete_binary_file_completely(self, soubor):
        logger.debug("core_repository_connector.delete_binary_file_completely.start",
                     extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely})
        from core.models import Soubor
        soubor: Soubor
        url = self._get_request_url(FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY, uuid=soubor.repository_uuid)
        self._send_request(url, FedoraRequestType.DELETE_BINARY_FILE_COMPLETELY)
        logger.debug("core_repository_connector.delete_binary_file_completely.end",
                     extra={"uuid": soubor.repository_uuid, "ident_cely": self.record.ident_cely})

    def delete_container(self):
        self._delete_link()
        logger.debug("core_repository_connector.delete_container.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.DELETE_CONTAINER)
        self._send_request(url, FedoraRequestType.DELETE_CONTAINER)
        url = self._get_request_url(FedoraRequestType.DELETE_TOMBSTONE)
        self._send_request(url, FedoraRequestType.DELETE_TOMBSTONE)
        logger.debug("core_repository_connector.delete_container.end", extra={"ident_cely": self.record.ident_cely})

    def _delete_link(self):
        logger.debug("core_repository_connector.delete_link.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.DELETE_LINK_CONTAINER)
        self._send_request(url, FedoraRequestType.DELETE_LINK_CONTAINER)
        url = self._get_request_url(FedoraRequestType.DELETE_LINK_TOMBSTONE)
        self._send_request(url, FedoraRequestType.DELETE_LINK_TOMBSTONE)
        logger.debug("core_repository_connector.delete_link.end", extra={"ident_cely": self.record.ident_cely})

    def record_deletion(self):
        logger.debug("core_repository_connector.record_deletion.start", extra={"ident_cely": self.record.ident_cely})
        url = self._get_request_url(FedoraRequestType.GET_DELETED_LINK, ident_cely=self.record.ident_cely)
        result = self._send_request(url, FedoraRequestType.GET_DELETED_LINK)
        if result is None or result.status_code == 404 or "not found" in result.text:
            logger.debug("core_repository_connector.record_deletion.already_exists",
                         extra={"ident_cely": self.record.ident_cely})
        else:
            logger.debug("core_repository_connector.record_deletion.adding_link",
                         extra={"ident_cely": self.record.ident_cely})
            headers = {
                "Content-Type": "application/sparql-update"
            }
            data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'deleted'}"
            url = self._get_request_url(FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS)
            self._send_request(url, FedoraRequestType.RECORD_DELETION_MOVE_MEMBERS,headers=headers, data=data)
            headers = {
                "Slug": self.record.ident_cely,
                "Content-Type": "text/turtle"
            }
            data = f"@prefix ore: <http://www.openarchives.org/ore/terms/> . " \
                    f"<> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{self.record.ident_cely}>"
            url = self._get_request_url(FedoraRequestType.RECORD_DELETION_ADD_MARK)
            self._send_request(url, FedoraRequestType.RECORD_DELETION_ADD_MARK, headers=headers, data=data)
        logger.debug("core_repository_connector.record_deletion.end", extra={"ident_cely": self.record.ident_cely})

    def record_ident_change(self, ident_cely_old):
        logger.debug("core_repository_connector.record_ident_change.start", extra={"ident_cely": self.record.ident_cely,
                                                                                   "ident_cely_old": ident_cely_old})
        if ident_cely_old is None or self.record.ident_cely == ident_cely_old:
            logger.warning("core_repository_connector.record_ident_change.no_ident_cely_old",
                         extra={"ident_cely": self.record.ident_cely})
            return
        base_url = f"http://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}/rest/"
        ident_cely_new = self.record.ident_cely
        data = f"INSERT DATA {{<> <http://purl.org/dc/terms/isReplacedBy> " \
               f"'{base_url}{settings.FEDORA_SERVER_NAME}/record/{ident_cely_new}'}}"
        headers = {
            "Content-Type": "application/sparql-update"
        }
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_1, ident_cely=ident_cely_old)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_1, headers=headers, data=data)
        data = f"INSERT DATA {{<> <http://purl.org/dc/terms/replaces> " \
                f"'{base_url}{settings.FEDORA_SERVER_NAME}/record/{ident_cely_old}'}}"
        headers = {
            "Content-Type": "application/sparql-update"
        }
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2, ident_cely=ident_cely_new)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_2, headers=headers, data=data)
        data = "INSERT DATA {<> <http://purl.org/dc/terms/type> 'renamed'}"
        headers = {
            "Content-Type": "application/sparql-update"
        }
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_3, ident_cely=ident_cely_old)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_3, headers=headers, data=data)
        headers = {
            "Slug": ident_cely_old,
            "Content-Type": "text/turtle"
        }
        data = f"@prefix ore: <http://www.openarchives.org/ore/terms/> . " \
               f"<> ore:proxyFor <info:fedora/{settings.FEDORA_SERVER_NAME}/record/{ident_cely_old}> ."
        url = self._get_request_url(FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4, ident_cely=ident_cely_new)
        self._send_request(url, FedoraRequestType.CHANGE_IDENT_CONNECT_RECORDS_4, headers=headers, data=data)
        logger.debug("core_repository_connector.record_ident_change.end", extra={"ident_cely": self.record.ident_cely,
                                                                                 "ident_cely_old": ident_cely_old})

    def validate_file_sha_512(self, soubor):
        logger.error("core_repository_connector.validate_file_sha_512.start",
                     extra={"ident_cely": self.record.ident_cely, "soubor": soubor.pk})
        from core.models import Soubor
        soubor: Soubor
        rep_bin_file: RepositoryBinaryFile = self.get_binary_file(soubor.repository_uuid)
        if rep_bin_file.sha_512 != soubor.sha_512:
            logger.error("core_repository_connector.validate_file_sha_512.error",
                         extra={"ident_cely": self.record.ident_cely, "soubor": soubor.pk})
            raise FedoraValidationError()
        else:
            logger.debug("core_repository_connector.validate_file_sha_512.ok",
                         extra={"ident_cely": self.record.ident_cely, "soubor": soubor.pk})

