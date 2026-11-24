"""Import zdrojové matice uživatelských oprávnění."""

import logging

import pandas as pd
from core.models import Permissions
from core.permission_validation import PermissionPolicyError, PolicyIssue, validate_permission_file
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q

logger = logging.getLogger(__name__)


class PermissionService:
    """Načte, ověří a atomicky nahradí matici oprávnění."""

    def run(self, docfile: InMemoryUploadedFile) -> tuple[pd.DataFrame, list[str]]:
        """Ověří soubor před nahrazením záznamů a zachová původní kompakci.

        :param docfile: Nahraný CSV nebo XLSX soubor s úplnou maticí oprávnění.
        :return: Přehled zpracovaných řádků a prázdný seznam chybějících URL.
        :raises PermissionPolicyError: Při neplatné matici nebo neúspěšném importu.
        """
        sheet, records = validate_permission_file(docfile)
        try:
            with transaction.atomic():
                groups = Group.objects.in_bulk((1, 2, 3, 4))
                missing_roles = sorted({1, 2, 3, 4} - groups.keys())
                if missing_roles:
                    raise PermissionPolicyError(
                        [PolicyIssue(f"Chybí standardní skupiny s ID {', '.join(map(str, missing_roles))}.")]
                    )
                Permissions.objects.all().delete()
                for record in records:
                    Permissions.objects.create(
                        address_in_app=record.address,
                        main_role=groups[record.role_id],
                        action=record.action,
                        base=record.base,
                        status=record.status,
                        ownership=record.ownership,
                        accessibility=record.accessibility,
                    )
                self._compact_unrestricted_permissions()
        except PermissionPolicyError:
            raise
        except Exception as error:
            logger.exception("core.services.PermissionService.import_failed")
            raise PermissionPolicyError(
                [PolicyIssue(f"Import selhal ({type(error).__name__}); předchozí oprávnění zůstala zachována.")]
            ) from error

        result = sheet.iloc[:, :3].copy()
        result["result"] = "ALL OK"
        return result.reset_index(drop=True), []

    @staticmethod
    def _compact_unrestricted_permissions():
        """Odstraní stejné neomezené záznamy jako původní import."""
        unique_pair_exists = Exists(
            Permissions.objects.filter(
                address_in_app=OuterRef("address_in_app"),
                main_role=OuterRef("main_role"),
            )
            .values("address_in_app", "main_role")
            .annotate(cnt=Count("id"))
            .filter(cnt=1)
        )
        exists_base_false = Exists(
            Permissions.objects.filter(
                address_in_app=OuterRef("address_in_app"),
                main_role=OuterRef("main_role"),
                base=False,
            )
        )
        Permissions.objects.filter(
            base=True,
            status__isnull=True,
            ownership__isnull=True,
            accessibility__isnull=True,
        ).filter(Q(unique_pair_exists) | ~Q(exists_base_false)).delete()
