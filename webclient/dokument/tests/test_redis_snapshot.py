"""Jednotkové testy Redis snapshotů dokumentů (volba tabulky a klíče podle ``Dokument.je_model_3d``)."""

from unittest import mock

from django.test import SimpleTestCase
from dokument.models import Dokument


class _FakeTable:
    """Náhrada tabulky: zaznamenává, které záznamy dostala k vykreslení."""

    def __init__(self, data):
        """
        Uloží předaný queryset.

        :param data: Queryset záznamů tabulky.
        """
        self.data = data


class DokumentRedisSnapshotTest(SimpleTestCase):
    """Ověřuje, že 3D a běžné dokumenty jdou do své tabulky a pod klíč se stejným rozlišením."""

    def test_je_model_3d(self):
        """Za 3D model se považuje dokument, jehož ``ident_cely`` začíná na ``3D``."""
        self.assertTrue(Dokument(ident_cely="3D-C-201900001").je_model_3d)
        self.assertFalse(Dokument(ident_cely="C-TX-201900001").je_model_3d)

    @mock.patch("dokument.models.RedisConnector.prepare_models_for_redis")
    @mock.patch("dokument.tables.DokumentTable")
    @mock.patch("dokument.tables.Model3DTable")
    @mock.patch.object(Dokument, "objects")
    def test_records_are_rendered_by_their_table(self, objects, model3d_table, dokument_table, prepare):
        """
        3D model se vykreslí ``Model3DTable``, běžný dokument ``DokumentTable``; klíč odpovídá tabulce.

        :param objects: Mock manageru ``Dokument.objects``.
        :param model3d_table: Mock třídy ``Model3DTable``.
        :param dokument_table: Mock třídy ``DokumentTable``.
        :param prepare: Mock ``RedisConnector.prepare_models_for_redis``.
        """
        model3d = Dokument(pk=1, ident_cely="3D-C-201900001")
        dokument = Dokument(pk=2, ident_cely="C-TX-201900001")
        objects.filter.side_effect = lambda pk__in: mock.Mock(select_related=mock.Mock(return_value=tuple(pk__in)))
        model3d_table.side_effect = _FakeTable
        dokument_table.side_effect = _FakeTable
        records_by_pk = {1: model3d, 2: dokument}
        prepare.side_effect = lambda table: {records_by_pk[pk].redis_snapshot_id: table for pk in table.data}

        snapshots = Dokument.generate_redis_snapshots([dokument, model3d])

        model3d_table.assert_called_once_with(data=(1,))
        dokument_table.assert_called_once_with(data=(2,))
        self.assertEqual(snapshots[model3d.redis_snapshot_id].data, (1,))
        self.assertEqual(snapshots[dokument.redis_snapshot_id].data, (2,))

    @mock.patch("dokument.models.RedisConnector.prepare_models_for_redis", return_value={})
    @mock.patch("dokument.tables.DokumentTable")
    @mock.patch("dokument.tables.Model3DTable")
    @mock.patch.object(Dokument, "objects")
    def test_table_without_records_is_skipped(self, objects, model3d_table, dokument_table, _prepare):
        """
        Když v dávce není žádný 3D model, ``Model3DTable`` se vůbec nevytváří.

        :param objects: Mock manageru ``Dokument.objects``.
        :param model3d_table: Mock třídy ``Model3DTable``.
        :param dokument_table: Mock třídy ``DokumentTable``.
        :param _prepare: Mock ``RedisConnector.prepare_models_for_redis``.
        """
        Dokument.generate_redis_snapshots([Dokument(pk=2, ident_cely="C-TX-201900001")])

        model3d_table.assert_not_called()
        dokument_table.assert_called_once()
