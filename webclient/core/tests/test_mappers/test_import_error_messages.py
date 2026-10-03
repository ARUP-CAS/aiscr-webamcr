from unittest.mock import patch

from core.import_data_mappers import (
    ImportDataIncorrectStructureContentObjectError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    ImportDataMissingReferencedValueError,
    ImportDataUnsupportedFileError,
    ImportDataUnsupportedFilesError,
)
from django.test import SimpleTestCase

PREFIX = "core_admin."


def untranslated(message_id):
    """Vrátí ID zprávy beze změny — test tak vidí vybraný klíč i předané parametry.

    :param message_id: Překladové ID zprávy předané do ``_()``.
    :return: Totéž ID, jako by překlad chyběl.
    """
    return message_id


@patch("core.import_data_mappers._", side_effect=untranslated)
class ImportErrorMessagesTest(SimpleTestCase):
    """Chybová hlášení importu: jedna celá věta (jedno ID) s pojmenovanými parametry."""

    def test_missing_referenced_value_selects_message_by_context(self, _mock):
        """Podle toho, zda je znám model a pole, se vybere celá věta s odpovídajícími zástupnými znaky.

        :param _mock: Mock pro ``core.import_data_mappers._`` vracející ID zprávy beze změny.
        """
        cases = {
            (None, None): "message",
            ("Osoba", None): "message.model",
            (None, "autor"): "message.field",
            ("Osoba", "autor"): "message.model_field",
        }
        for (model, field), suffix in cases.items():
            with self.subTest(model=model, field=field):
                message = str(ImportDataMissingReferencedValueError("OS-1", model, field))
                self.assertEqual(
                    message,
                    f"{PREFIX}ImportDataMissingReferencedValueError.{suffix} value=OS-1 model={model} field={field}",
                )

    def test_incorrect_structure_lists_missing_and_excess_columns(self, _mock):
        """Souhrnná věta, pak samostatné věty pro chybějící a přebývající sloupce.

        :param _mock: Mock pro ``core.import_data_mappers._`` vracející ID zprávy beze změny.
        """
        message = str(ImportDataIncorrectStructureError(["a", "b"], ["c"]))
        self.assertEqual(
            message,
            f"{PREFIX}ImportDataIncorrectStructureError.message "
            f"{PREFIX}ImportDataIncorrectStructureError.message.missing_columns columns=a, b "
            f"{PREFIX}ImportDataIncorrectStructureError.message.excess_columns columns=c",
        )

    def test_incorrect_structure_without_column_lists(self, _mock):
        """Bez seznamů sloupců zůstane jen souhrnná věta.

        :param _mock: Mock pro ``core.import_data_mappers._`` vracející ID zprávy beze změny.
        """
        self.assertEqual(
            str(ImportDataIncorrectStructureError([], [])), f"{PREFIX}ImportDataIncorrectStructureError.message"
        )

    def test_single_sentence_messages_carry_their_params(self, _mock):
        """Ostatní výjimky předají všechny hodnoty jako pojmenované parametry jedné věty.

        :param _mock: Mock pro ``core.import_data_mappers._`` vracející ID zprávy beze změny.
        """
        cases = [
            (
                ImportDataIncorrectStructureContentObjectError(["x", "y"], ("a", "b"), ("c",)),
                "ImportDataIncorrectStructureContentObjectError.message columns=x, y options=('a', 'b'); ('c',)",
            ),
            (
                ImportDataIntegrityError("C-1", "Dokument", "INSERT"),
                "ImportDataIntegrityError.message record=C-1 model=Dokument action=INSERT",
            ),
            (ImportDataUnsupportedFileError("x.csv"), "ImportDataUnsupportedFileError.message file=x.csv"),
            (
                ImportDataUnsupportedFilesError(["a.csv", "b.csv"]),
                "ImportDataUnsupportedFilesError.message files=a.csv, b.csv",
            ),
        ]
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                self.assertEqual(str(error), PREFIX + expected)
