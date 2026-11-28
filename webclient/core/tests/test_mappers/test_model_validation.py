from core.forms import ImportDataAdminForm
from core.import_data_mappers import DokumentMapper, ImportDataError, ImportModelMapper
from cron.tests._run_data_import_mapper_base import RunDataImportMapperTestBase
from dokument.models import Dokument, DokumentExtraData
from historie.models import Historie
from komponenta.models import KomponentaVazby
from uzivatel.models import Organizace, User

UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE


class ValidateRecordFieldsTest(RunDataImportMapperTestBase):
    """Validace polí nastavených řádkem proti pravidlům modelu (``ImportModelMapper._validate_record_fields``)."""

    def assert_rejected(self, record, row_fields, batch_unique_keys=None):
        """
        Ověří, že validace polí záznam odmítne.

        :param record: Validovaná instance modelu.
        :param row_fields: Pole, která nastavuje importovaný řádek.
        :param batch_unique_keys: Klíče unikátních hodnot z dřívějších řádků dávky.
        """
        with self.assertRaises(ImportDataError):
            ImportModelMapper._validate_record_fields(record, row_fields, batch_unique_keys or {})

    def test_validator_without_db_constraint_rejects_value(self):
        """Rok vzniku mimo 1900–2050 hlídá jen validátor modelu, bez kontroly by se uložil."""
        self.dokument.rok_vzniku = 1800
        self.assert_rejected(self.dokument, {"rok_vzniku"})

    def test_check_constraint_rejects_value(self):
        """Hodnota porušující check constraint se odmítne už ve validaci."""
        self.assert_rejected(DokumentExtraData(dokument=self.dokument, duveryhodnost=150), {"duveryhodnost"})

    def test_required_field_rejects_none(self):
        """Povinné pole nastavené řádkem na prázdnou hodnotu se odmítne."""
        self.dokument.stav = None
        self.assert_rejected(self.dokument, {"stav"})

    def test_unique_value_existing_in_database_is_rejected(self):
        """Unikátní hodnota, kterou už má jiný záznam v DB, se odmítne."""
        self.assert_rejected(User(email=self.user.email, ident_cely="U-VAL-001"), {"email"})

    def test_unique_value_repeated_in_batch_is_rejected(self):
        """Druhý záznam dávky se stejnou unikátní hodnotou se odmítne, i když v DB ještě není."""
        batch_unique_keys = {}
        first = User(email="novy@example.cz", ident_cely="U-VAL-002")
        ImportModelMapper._validate_record_fields(first, {"email"}, batch_unique_keys)
        self.assert_rejected(User(email="novy@example.cz", ident_cely="U-VAL-003"), {"email"}, batch_unique_keys)

    def test_same_record_repeating_unique_value_in_batch_passes(self):
        """Dva řádky aktualizující tentýž záznam na stejnou unikátní hodnotu se neodmítnou jako duplicita."""
        batch_unique_keys = {}
        self.user.email = "zmeneny@example.cz"
        ImportModelMapper._validate_record_fields(self.user, {"email"}, batch_unique_keys)
        ImportModelMapper._validate_record_fields(self.user, {"email"}, batch_unique_keys)

    def test_choices_are_not_checked(self):
        """Kód mimo choices modelu projde, protože ho uložená data i aplikace používají (typ_zmeny IMP)."""
        ImportModelMapper._validate_record_fields(Historie(typ_zmeny="IMP"), {"typ_zmeny"}, {})

    def test_empty_string_in_required_field_passes(self):
        """Prázdný řetězec projde: ``blank`` je omezení formulářů, DB ho přijme (např. typ_vazby '')."""
        ImportModelMapper._validate_record_fields(KomponentaVazby(typ_vazby=""), {"typ_vazby"}, {})

    def test_fields_not_set_by_row_are_not_checked(self):
        """Neplatná hodnota v poli, které řádek nenastavuje, řádek neodmítne."""
        self.dokument.rok_vzniku = 1800
        ImportModelMapper._validate_record_fields(self.dokument, {"popis"}, {})


class ValidateRecordDeletionTest(RunDataImportMapperTestBase):
    """Kontrola odkazů ``RESTRICT``/``PROTECT`` u DELETE (``ImportModelMapper._validate_record_deletion``)."""

    def _organizace_referenced_by_dokument(self, suffix: str, dokument_ident: str):
        """
        Vytvoří organizaci, na kterou odkazuje (RESTRICT) jediný dokument.

        Organizace se ukládá bez signálu, aby test nezapisoval do Fedory.

        :param suffix: Přípona identifikátoru organizace.
        :param dokument_ident: Identifikátor odkazujícího dokumentu.
        :return: Dvojice ``(organizace, dokument)``.
        """
        organizace = Organizace(
            ident_cely=f"ORG-VAL-{suffix}-001",
            nazev=f"Org {suffix}",
            nazev_zkraceny=f"ORGVAL{suffix}",
            typ_organizace=self.base_heslars["typ_org"],
            zverejneni_pristupnost=self.base_heslars["pristupnost"],
            licence=self.base_heslars["licence"],
        )
        organizace.suppress_signal = True
        organizace.save()
        dokument = self._create_dokument(dokument_ident)
        Dokument.objects.filter(pk=dokument.pk).update(organizace=organizace)
        return organizace, dokument

    def test_restricted_reference_rejects_delete(self):
        """Organizaci, na kterou odkazuje dokument (RESTRICT), nelze smazat."""
        organizace, _dokument = self._organizace_referenced_by_dokument("val1", "C-FD-991000077")
        with self.assertRaises(ImportDataError):
            ImportModelMapper._validate_record_deletion(organizace, set())

    def test_reference_deleted_by_earlier_row_allows_delete(self):
        """Odkazující dokument smazaný dřívějším řádkem dávky smazání organizace nebrání."""
        organizace, dokument = self._organizace_referenced_by_dokument("val2", "C-FD-991000078")
        batch_deleted = {(Dokument, dokument.pk)}
        ImportModelMapper._validate_record_deletion(organizace, batch_deleted)
        self.assertIn((organizace.__class__, organizace.pk), batch_deleted)

    def test_delete_records_cascaded_objects_for_later_rows(self):
        """Záznamy smazané kaskádou se zapíšou do stavu dávky pro další řádky."""
        extra_data = DokumentExtraData.objects.create(dokument=self.dokument, geom_system="4326")
        batch_deleted = set()
        DokumentMapper({"ident_cely": self.dokument.ident_cely}).validate_model_records(
            [self.dokument], DELETE, {"unique_keys": {}, "deleted": batch_deleted}
        )
        self.assertIn((DokumentExtraData, extra_data.pk), batch_deleted)
