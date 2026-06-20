from core.constants import (
    API_REQUEST_LOG_STATUS_FAILURE,
    API_REQUEST_LOG_STATUS_PROCESSING,
    API_REQUEST_LOG_STATUS_RECEIVED,
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
)
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ApiRequestLog(models.Model):
    """Zaznamenává každý požadavek na API včetně stavu a výsledku."""

    STATUS_CHOICES = (
        (API_REQUEST_LOG_STATUS_RECEIVED, _("api.model.apiRequestLog.status.received")),
        (API_REQUEST_LOG_STATUS_PROCESSING, _("api.model.apiRequestLog.status.processing")),
        (API_REQUEST_LOG_STATUS_SUCCESS, _("api.model.apiRequestLog.status.success")),
        (API_REQUEST_LOG_STATUS_FAILURE, _("api.model.apiRequestLog.status.failure")),
    )

    REQUEST_TARGET_CHOICES = (
        (
            API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
            _("api.model.apiRequestLog.requestTarget.samostatnyNalezXmlImport"),
        ),
        (
            API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
            _("api.model.apiRequestLog.requestTarget.samostatnyNalezEvidencniCisloPatch"),
        ),
        (
            API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
            _("api.model.apiRequestLog.requestTarget.samostatnyNalezFotografieUpload"),
        ),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.user"),
    )
    client_ip = models.GenericIPAddressField(
        verbose_name=_("api.model.apiRequestLog.clientIp"),
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("api.model.apiRequestLog.receivedAt"),
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.finishedAt"),
    )
    request_target = models.CharField(
        max_length=64,
        choices=REQUEST_TARGET_CHOICES,
        verbose_name=_("api.model.apiRequestLog.requestTarget"),
    )
    filename = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.filename"),
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.fileSize"),
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=API_REQUEST_LOG_STATUS_RECEIVED,
        verbose_name=_("api.model.apiRequestLog.status"),
    )
    ident_cely = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_("api.model.apiRequestLog.identCely"),
    )
    samostatny_nalez = models.ForeignKey(
        "pas.SamostatnyNalez",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.samostatnyNalez"),
    )
    errors = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("api.model.apiRequestLog.errors"),
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "api_log_pozadavku"
        ordering = ["-received_at"]
        verbose_name = _("api.model.apiRequestLog.modelTitle.label")
        verbose_name_plural = _("api.model.apiRequestLog.modelTitles.label")
