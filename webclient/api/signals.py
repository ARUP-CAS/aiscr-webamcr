from api.models import ApiRequestLog
from core.constants import (
    API_REQUEST_LOG_STATUS_SUCCESS,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
)
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

_PAS_REQUEST_TARGETS = frozenset(
    {
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_XML_IMPORT,
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_EVIDENCNI_CISLO_PATCH,
        API_REQUEST_LOG_TARGET_SAMOSTATNY_NALEZ_FOTOGRAFIE_UPLOAD,
    }
)


@receiver(pre_save, sender=ApiRequestLog)
def validate_pas_request_target_fields(sender, instance: ApiRequestLog, **kwargs):
    """
    Pro PAS-specifické cíle (XML import, evidenční číslo patch, fotografie upload)
    vyžaduje vyplněné ``ident_cely`` i ``samostatny_nalez`` v okamžiku, kdy je
    záznam úspěšně dokončen (``status == success``). Stav ``failure`` validace
    cíleně neaktivuje — k chybě může dojít před tím, než je ``ident_cely``
    vůbec známé (např. chybějící soubor v XML importu, neexistující záznam pro
    PATCH/UPLOAD), a vynucení vyplnění by zablokovalo legitimní zápis chyby.

    :param sender: Třída modelu (``ApiRequestLog``).
    :param instance: Konkrétní ukládaný záznam.
    :param kwargs: Další argumenty signálu (nepoužity).

    :raises ValidationError: Pokud je ``request_target`` PAS-specifický, záznam
        je ve stavu ``success`` a chybí ``ident_cely`` nebo ``samostatny_nalez``.
    """
    if instance.request_target not in _PAS_REQUEST_TARGETS:
        return
    if instance.status != API_REQUEST_LOG_STATUS_SUCCESS:
        return
    missing = []
    if not instance.ident_cely:
        missing.append("ident_cely")
    if getattr(instance, "samostatny_nalez_id", None) is None:
        missing.append("samostatny_nalez")
    if missing:
        raise ValidationError(
            {
                field: _("api.model.apiRequestLog.pasTargetRequiresField").format(
                    field=field, target=instance.request_target
                )
                for field in missing
            }
        )
