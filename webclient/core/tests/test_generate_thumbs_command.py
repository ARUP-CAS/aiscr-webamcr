"""Regrese vynuceného přegenerování existujících náhledů příkazem generate_thumbs."""

import io
from types import SimpleNamespace
from unittest import mock

from core.management.commands.generate_thumbs import Command
from django.core.management import call_command
from django.test import SimpleTestCase

COMMAND_MODULE = "core.management.commands.generate_thumbs"


class _ThumbnailRepository:
    """Úložiště s existujícím malým i velkým náhledem bez síťového připojení."""

    def __init__(self):
        """Připraví původní náhledy a seznam požadavků na jejich obnovu."""
        self.thumbnails = {"thumb": b"old-small", "thumb-large": b"old-large"}
        self.writes = []

    def get_binary_file(self, uuid, thumb_small=False, thumb_large=False):
        """Vrátí existující náhled nebo originál fotografie pro přegenerování."""
        if thumb_small or thumb_large:
            content = self.thumbnails["thumb" if thumb_small else "thumb-large"]
        else:
            content = b"original-photo"
        return SimpleNamespace(content=io.BytesIO(content))

    def save_thumbs(self, filename, content, uuid, update=False):
        """Existující náhledy přepíše pouze při výslovném požadavku update."""
        self.writes.append((filename, content.getvalue(), uuid, update))
        if not update:
            return []
        self.thumbnails = {"thumb": b"new-small", "thumb-large": b"new-large"}
        return [("thumb", True), ("thumb-large", True)]


class GenerateThumbsCommandTests(SimpleTestCase):
    """Volba force musí obnovit i náhledy, které už úložiště obsahuje."""

    def _run_command(self, force=False):
        """Spustí skutečný parser a příkaz nad souborem s oběma existujícími náhledy.

        :param force: Zda předat příkazu přepínač --force.
        :return: Testovací úložiště a zaznamenané distribuční změny.
        """
        repository = _ThumbnailRepository()
        history = []
        record = SimpleNamespace(
            pk=1,
            repository_uuid="uuid-1",
            nazev="photo.jpg",
            path="record/photo.jpg",
            vazba=SimpleNamespace(navazany_objekt=SimpleNamespace(ident_cely="record")),
            zaznamenej_distribuce=history.extend,
        )
        arguments = ["--pks", "1"]
        if force:
            arguments.append("--force")
        with (
            mock.patch("core.models.Soubor.objects.filter", return_value=[record]),
            mock.patch(COMMAND_MODULE + ".FedoraRepositoryConnector", return_value=repository),
        ):
            call_command(Command(stdout=io.StringIO()), *arguments)
        return repository, history

    def test_force_regenerates_both_existing_thumbnails_and_records_history(self):
        """Přepínač force přepíše oba existující náhledy a zaznamená jejich nové verze."""
        repository, history = self._run_command(force=True)
        self.assertEqual(repository.writes, [("photo.jpg", b"original-photo", "uuid-1", True)])
        self.assertEqual(repository.thumbnails, {"thumb": b"new-small", "thumb-large": b"new-large"})
        self.assertEqual(history, [("thumb", True), ("thumb-large", True)])

    def test_existing_thumbnails_are_skipped_without_force(self):
        """Bez přepínače force existující náhledy ani jejich historie nemění."""
        repository, history = self._run_command()
        self.assertEqual(repository.writes, [])
        self.assertEqual(repository.thumbnails, {"thumb": b"old-small", "thumb-large": b"old-large"})
        self.assertEqual(history, [])
