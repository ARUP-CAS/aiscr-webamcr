"""Sdílené fixtures pro smoke testy ``run_data_import`` mapperů."""

import json
from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

from core.constants import (
    D_STAV_ZAPSANY,
    DOKUMENT_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    EZ_STAV_ZAPSANY,
    ROLE_BADATEL_ID,
)
from core.forms import ImportDataAdminForm
from core.models import SouborVazby
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_archeologicky_zaznam,
    create_dokumentacni_jednotka,
    create_heslar_fixtures,
    create_organizace,
    create_projekt,
    create_projekt_typ,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from dokument.models import Dokument, DokumentCast, Let
from ez.models import ExterniZdroj
from heslar.hesla import (
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_DOHLEDNOST,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_NAHRADA,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_EXTERNI_ZDROJ_TYP,
    HESLAR_JAZYK,
    HESLAR_LETFOTO_TVAR,
    HESLAR_LETISTE,
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_POCASI,
    HESLAR_POSUDEK_TYP,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_UDALOST_TYP,
    HESLAR_ZEME,
)
from heslar.models import Heslar, HeslarNazev
from historie.models import HistorieVazby
from komponenta.models import Komponenta, KomponentaVazby
from uzivatel.models import Osoba, User, UserNotificationType

JOB_ID = "test-job-remaining"
LOCK_TOKEN = "test-lock-token"


@contextmanager
def patched_fedora():
    """Umlčí Fedora side efekty při vytváření fixtures i běhu importu."""
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
                return_value=True,
            )
        )
        stack.enter_context(patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None))
        stack.enter_context(patch("projekt.models.Projekt.set_pristupnost", return_value=None))
        for target in (
            "arch_z.signals.FedoraTransaction",
            "core.signals.FedoraTransaction",
            "dj.signals.FedoraTransaction",
            "dokument.signals.FedoraTransaction",
            "heslar.signals.FedoraTransaction",
            "komponenta.signals.FedoraTransaction",
            "nalez.signals.FedoraTransaction",
            "neidentakce.signals.FedoraTransaction",
            "notifikace_projekty.signals.FedoraTransaction",
            "uzivatel.signals.FedoraTransaction",
        ):
            mock = stack.enter_context(patch(target))
            mock.return_value = MagicMock(uid="fixture-fedora-uid", updated_ident_cely=set())
        yield


class RunDataImportMapperTestBase(TestCase):
    """Společný základ pro jednoúčelové ``run_data_import`` smoke testy."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        Group.objects.get_or_create(id=99001, defaults={"name": "remaining-import-group"})
        with patched_fedora():
            cls.base_heslars = create_heslar_fixtures("rem")
            cls.extra_heslars = cls._create_extra_heslars()
            cls.katastr, cls.pian = create_ruian_with_pian("rem", "P-0003-000001", cls.base_heslars)
            cls.organizace = create_organizace("rem", cls.base_heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-remaining@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-991001",
                first_name="Import",
                last_name="Runner",
            )
            cls.other_user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-coworker-remaining@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-991002",
                first_name="Other",
                last_name="Runner",
            )
            cls.osoba = Osoba.objects.create(
                ident_cely="OS-991001",
                jmeno="Autor",
                prijmeni="Zbyly",
                vypis="Zbyly A.",
                vypis_cely="Zbyly, Autor",
                rok_narozeni=1975,
            )
            cls.projekt_typ = create_projekt_typ("rem")
            cls.projekt = create_projekt("C-202399001", cls.katastr, cls.projekt_typ)
            cls.az = create_archeologicky_zaznam("C-202399001A", cls.katastr, cls.base_heslars["pristupnost"])
            cls.dj = create_dokumentacni_jednotka("C-202399001A-D01", cls.az, cls.pian, cls.base_heslars["dj_typ"])
            cls.dj.komponenty = KomponentaVazby.objects.create(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
            cls.dj.suppress_signal = True
            cls.dj.save()
            cls.let = cls._create_let("C-LET-991001")
            cls.dokument = cls._create_dokument("C-FD-991000001")
            cls.dokument_cast = cls._create_dokument_cast("C-FD-991000001-D001")
            cls.komponenta = cls._create_komponenta("C-202399001A-K001")
            cls.externi_zdroj = cls._create_externi_zdroj("BIB-9910001")
            cls.notification_type = UserNotificationType.objects.create(ident_cely="S-E-REM-01")

    @classmethod
    def _create_heslar(cls, nazev_id: int, suffix: str) -> Heslar:
        nazev, _ = HeslarNazev.objects.get_or_create(id=nazev_id, defaults={"nazev": f"remaining_{nazev_id}"})
        heslar, _ = Heslar.objects.get_or_create(
            ident_cely=f"HES-REM-{suffix}",
            defaults={
                "nazev_heslare": nazev,
                "heslo": f"Test {suffix}",
                "heslo_en": f"Test {suffix}",
                "zkratka": suffix[:8],
                "razeni": 1,
            },
        )
        return heslar

    @classmethod
    def _create_extra_heslars(cls) -> dict:
        return {
            "aktivita": cls._create_heslar(HESLAR_AKTIVITA, "AKT"),
            "areal": cls._create_heslar(HESLAR_AREAL, "ARE"),
            "dohlednost": cls._create_heslar(HESLAR_DOHLEDNOST, "DOH"),
            "doc_format": cls._create_heslar(HESLAR_DOKUMENT_FORMAT, "DFO"),
            "doc_material": cls._create_heslar(HESLAR_DOKUMENT_MATERIAL, "DMA"),
            "doc_nahrada": cls._create_heslar(HESLAR_DOKUMENT_NAHRADA, "DNA"),
            "doc_rada": cls._create_heslar(HESLAR_DOKUMENT_RADA, "DRA"),
            "doc_typ": cls._create_heslar(HESLAR_DOKUMENT_TYP, "DTY"),
            "doc_ulozeni": cls._create_heslar(HESLAR_DOKUMENT_ULOZENI, "DUL"),
            "doc_zachovalost": cls._create_heslar(HESLAR_DOKUMENT_ZACHOVALOST, "DZA"),
            "ez_typ": cls._create_heslar(HESLAR_EXTERNI_ZDROJ_TYP, "EZT"),
            "jazyk": cls._create_heslar(HESLAR_JAZYK, "JAZ"),
            "letiste": cls._create_heslar(HESLAR_LETISTE, "LET"),
            "okolnosti": cls._create_heslar(HESLAR_NALEZOVE_OKOLNOSTI, "OKO"),
            "obdobi": cls._create_heslar(HESLAR_OBDOBI, "OBD"),
            "objekt_druh": cls._create_heslar(HESLAR_OBJEKT_DRUH, "ODR"),
            "objekt_specifikace": cls._create_heslar(HESLAR_OBJEKT_SPECIFIKACE, "OSP"),
            "pocasi": cls._create_heslar(HESLAR_POCASI, "POC"),
            "posudek": cls._create_heslar(HESLAR_POSUDEK_TYP, "POS"),
            "predmet_druh": cls._create_heslar(HESLAR_PREDMET_DRUH, "PDR"),
            "predmet_specifikace": cls._create_heslar(HESLAR_PREDMET_SPECIFIKACE, "PSP"),
            "tvar": cls._create_heslar(HESLAR_LETFOTO_TVAR, "TVA"),
            "udalost_typ": cls._create_heslar(HESLAR_UDALOST_TYP, "UTY"),
            "zeme": cls._create_heslar(HESLAR_ZEME, "ZEM"),
        }

    @classmethod
    def _create_let(cls, ident_cely: str) -> Let:
        return Let.objects.create(
            ident_cely=ident_cely,
            letiste_start=cls.extra_heslars["letiste"],
            letiste_cil=cls.extra_heslars["letiste"],
            pozorovatel=cls.osoba,
            organizace=cls.organizace,
            pocasi=cls.extra_heslars["pocasi"],
            dohlednost=cls.extra_heslars["dohlednost"],
        )

    @classmethod
    def _create_dokument(cls, ident_cely: str) -> Dokument:
        dokument = Dokument(
            ident_cely=ident_cely,
            let=cls.let,
            rada=cls.extra_heslars["doc_rada"],
            typ_dokumentu=cls.extra_heslars["doc_typ"],
            organizace=cls.organizace,
            rok_vzniku=2024,
            pristupnost=cls.base_heslars["pristupnost"],
            material_originalu=cls.extra_heslars["doc_material"],
            stav=D_STAV_ZAPSANY,
            licence=cls.base_heslars["licence"],
        )
        dokument.historie = HistorieVazby.objects.create(typ_vazby=DOKUMENT_RELATION_TYPE)
        dokument.soubory = SouborVazby.objects.create(typ_vazby=DOKUMENT_RELATION_TYPE)
        dokument.active_transaction = MagicMock(uid="fixture-dokument-uid", updated_ident_cely=set())
        dokument.suppress_signal = True
        dokument.save()
        return dokument

    @classmethod
    def _create_dokument_cast(cls, ident_cely: str) -> DokumentCast:
        dokument_cast = DokumentCast(
            ident_cely=ident_cely,
            dokument=cls.dokument,
            archeologicky_zaznam=cls.az,
        )
        dokument_cast.active_transaction = MagicMock(uid="fixture-dokument-cast-uid", updated_ident_cely=set())
        dokument_cast.suppress_signal = True
        dokument_cast.save()
        return dokument_cast

    @classmethod
    def _create_komponenta(cls, ident_cely: str) -> Komponenta:
        komponenta = Komponenta(
            ident_cely=ident_cely,
            komponenta_vazby=cls.dj.komponenty,
            obdobi=cls.extra_heslars["obdobi"],
            areal=cls.extra_heslars["areal"],
            jistota=True,
        )
        komponenta.suppress_signal = True
        komponenta.save()
        return komponenta

    @classmethod
    def _create_externi_zdroj(cls, ident_cely: str) -> ExterniZdroj:
        externi_zdroj = ExterniZdroj(
            ident_cely=ident_cely,
            typ=cls.extra_heslars["ez_typ"],
            typ_dokumentu=cls.extra_heslars["doc_typ"],
            stav=EZ_STAV_ZAPSANY,
            nazev="Výchozí externí zdroj",
        )
        externi_zdroj.suppress_signal = True
        externi_zdroj.save()
        return externi_zdroj

    def run_import(
        self, file_key: str, payload: dict, performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT, **kwargs
    ):
        """Spustí pomocný importní scénář pro test.

        :param file_key: Hodnota použitá v testovacím importním scénáři.
        :param payload: Hodnota použitá v testovacím importním scénáři.
        :param performed_action: Hodnota použitá v testovacím importním scénáři.
        :param kwargs: Hodnota použitá v testovacím importním scénáři."""
        return self.run_import_records(file_key, [payload], performed_action, **kwargs)

    def run_import_records(
        self,
        file_key: str,
        payloads: list[dict],
        performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        save_metadata_side_effect=None,
        refresh_lock_side_effect=None,
        pre_redis_keys: dict | None = None,
        extra_patches: list | None = None,
    ):
        """Spustí pomocný importní scénář pro test.

        :param file_key: Hodnota použitá v testovacím importním scénáři.
        :param payloads: Hodnota použitá v testovacím importním scénáři.
        :param performed_action: Hodnota použitá v testovacím importním scénáři.
        :param save_metadata_side_effect: Hodnota použitá v testovacím importním scénáři.
        :param refresh_lock_side_effect: Hodnota použitá v testovacím importním scénáři.
        :param pre_redis_keys: Hodnota použitá v testovacím importním scénáři.
        :param extra_patches: Hodnota použitá v testovacím importním scénáři."""
        redis_data = {
            f"import_data_count_{JOB_ID}": str(len(payloads)),
            f"import_performed_action_{JOB_ID}": performed_action,
        }
        for index, payload in enumerate(payloads):
            redis_data[f"import_data_{JOB_ID}_record_{index}"] = json.dumps({"__file_name": file_key, **payload})
        if pre_redis_keys:
            for key, value in pre_redis_keys.items():
                redis_data[key] = value
        fake_redis = FakeRedis(redis_data)
        save_metadata_calls: list = []

        def default_save_metadata_side_effect(self, *args, **kwargs):
            save_metadata_calls.append(self)

        effective_save_metadata_side_effect = save_metadata_side_effect or default_save_metadata_side_effect

        def get_record_from_ident_side_effect(ident_cely):
            record = MagicMock()
            record.ident_cely = ident_cely
            return record

        refresh_lock_kwargs = (
            {"side_effect": refresh_lock_side_effect}
            if refresh_lock_side_effect is not None
            else {"return_value": True}
        )

        with ExitStack() as stack:
            stack.enter_context(patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis))
            stack.enter_context(patch("core.connectors.RedisConnector.refresh_import_lock", **refresh_lock_kwargs))
            stack.enter_context(
                patch(
                    "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
                    return_value=True,
                )
            )
            stack.enter_context(
                patch(
                    "xml_generator.models.ModelWithMetadata.save_metadata",
                    autospec=True,
                    side_effect=effective_save_metadata_side_effect,
                )
            )
            stack.enter_context(patch("projekt.models.Projekt.set_pristupnost", return_value=None))
            stack.enter_context(
                patch("cron.tasks.get_record_from_ident", side_effect=get_record_from_ident_side_effect)
            )
            stack.enter_context(
                patch("xml_generator.models.ModelWithMetadata.record_deletion", autospec=True, return_value=None)
            )
            stack.enter_context(patch("historie.models.Historie.save_record_deletion_record", return_value=None))
            fedora_transaction_mock = stack.enter_context(patch("cron.tasks.FedoraTransaction"))
            fedora_deletion_mock = stack.enter_context(patch("cron.tasks.FedoraDeletionOnlyTransaction"))
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-deletion-uid", updated_ident_cely=set())
            for target in (
                "arch_z.signals.FedoraTransaction",
                "core.signals.FedoraTransaction",
                "dj.signals.FedoraTransaction",
                "dokument.signals.FedoraTransaction",
                "komponenta.signals.FedoraTransaction",
                "nalez.signals.FedoraTransaction",
                "neidentakce.signals.FedoraTransaction",
                "notifikace_projekty.signals.FedoraTransaction",
                "uzivatel.signals.FedoraTransaction",
            ):
                mock = stack.enter_context(patch(target))
                mock.return_value = MagicMock(uid="test-signals-fedora-uid", updated_ident_cely=set())
            if extra_patches:
                for ctx in extra_patches:
                    stack.enter_context(ctx)
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return fake_redis, save_metadata_calls

    def _import_details(self, fake_redis: FakeRedis) -> dict:
        details = [
            item.decode("utf-8") if isinstance(item, bytes) else item
            for item in fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        ]
        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        status = status_raw.decode("utf-8") if isinstance(status_raw, bytes) else status_raw
        return {"status": status, "details": details}

    def assert_import_success(self, fake_redis: FakeRedis):
        """Ověří pomocnou podmínku importního testu.

        :param fake_redis: Hodnota použitá v testovacím importním scénáři."""
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(
            int(progress_raw.decode("utf-8")),
            cron_tasks.IMPORT_PROGRESS_PHASE_FINISHED,
            self._import_details(fake_redis),
        )

    def assert_import_failed(self, fake_redis: FakeRedis):
        """Ověří pomocnou podmínku importního testu.

        :param fake_redis: Hodnota použitá v testovacím importním scénáři."""
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(
            int(progress_raw.decode("utf-8")),
            cron_tasks.IMPORT_PROGRESS_PHASE_FAILED,
            self._import_details(fake_redis),
        )
