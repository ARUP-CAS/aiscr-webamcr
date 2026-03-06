import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

logger = logging.getLogger(__name__)


class CustomAdminSettings(ExportModelOperationsMixin("custom_admin_settings"), models.Model):
    """Implementuje komponentu ``CustomAdminSettings`` v rámci aplikace."""

    item_group = models.CharField(max_length=100)
    item_id = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        verbose_name = _("core.model.CustomAdminSettings.modelTitle.label")
        verbose_name_plural = _("core.model.CustomAdminSettings.modelTitles.label")
