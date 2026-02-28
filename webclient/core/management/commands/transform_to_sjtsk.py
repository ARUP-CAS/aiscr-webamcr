import logging

from core.coordTransform import transform_geom_to_sjtsk
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro transformaci souřadnic do systému S-JTSK.

    Tento příkaz transformuje geometrie z WGS84 do souřadnicového systému S-JTSK
    pro různé typy záznamů (PIAN, nález, projekt, dokument).

    Parametry:
    - model: Typ modelu pro transformaci (pian, nalez, projekt, dokument)

    Poznámka:
    - Transformuje pouze záznamy, které mají vyplněnou geometrii (geom) ale nemají vyplněnou S-JTSK geometrii (geom_sjtsk)

    Příklady použití::

    python manage.py transform_to_sjtsk pian
    python manage.py transform_to_sjtsk nalez
    python manage.py transform_to_sjtsk projekt
    python manage.py transform_to_sjtsk dokument
    """

    help = _("core.management.commands.transform_to_sjtsk.Command.help")

    def add_arguments(self, parser):
        """
        Provádí operaci add arguments.

        :param parser: Vstupní hodnota ``parser`` pro danou operaci.
        """
        parser.add_argument(
            "model",
            type=str,
            choices=["pian", "nalez", "projekt", "dokument"],
            help=_("core.management.commands.transform_to_sjtsk.Command.add_arguments.model_help"),
        )

    def handle(self, *args, **options):
        """
        Zpracuje hodnotu. v aplikaci.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        """
        model_type = options["model"]

        logger.debug(
            "core.management.commands.transform_to_sjtsk.start",
            extra={"model": model_type},
        )

        if model_type == "pian":
            self._transform_pian()
        elif model_type == "nalez":
            self._transform_nalez()
        elif model_type == "projekt":
            self._transform_projekt()
        elif model_type == "dokument":
            self._transform_dokument()

        logger.debug(
            "core.management.commands.transform_to_sjtsk.end",
            extra={"model": model_type},
        )

    def _transform_pian(self):
        """
        Transformuje pian.

        :return: Vrací výsledek provedené operace.
        """
        from pian.models import Pian

        self.stdout.write(_("core.management.commands.transform_to_sjtsk.Command._transform_pian.processing"))

        query_select = (
            "select pian.id,ST_AsText(pian.geom) as geometry "
            " from public.pian pian "
            " where pian.geom is not null "
            " and (pian.geom_sjtsk is null)"
            " order by pian.id"
        )
        query_update = (
            "update public.pian pian "
            " set geom_sjtsk = ST_GeomFromText(%s)"
            " where pian.geom_sjtsk is null and pian.id=%s "
        )

        pians = Pian.objects.raw(query_select)
        total = len(list(pians))
        pians = Pian.objects.raw(query_select)  # Re-execute query
        success_count = 0
        error_count = 0

        self.stdout.write(
            _("core.management.commands.transform_to_sjtsk.Command._transform_pian.found") + " " + str(total)
        )

        for idx, pian in enumerate(pians):
            if total > 0 and idx % max(total // 100, 1) == 0:
                percentage = round(idx / total * 100)
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.transform_to_sjtsk.Command._transform_pian.progress")
                    + " "
                    + str(percentage)
                    + "%",
                    ending="",
                )

            geom = transform_geom_to_sjtsk(pian.geometry)
            if geom[1] == "OK":
                with connection.cursor() as cursor:
                    cursor.execute(query_update, [geom[0], pian.id])
                success_count += 1
            else:
                error_count += 1
                logger.error(
                    "core.management.commands.transform_to_sjtsk.Command._transform_pian.error",
                    extra={"pian_id": pian.id, "error": geom[1]},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.transform_to_sjtsk.Command._transform_pian.error")
                        + " "
                        + str(pian.id)
                        + ": "
                        + str(geom[1])
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                _("core.management.commands.transform_to_sjtsk.Command._transform_pian.finished_transformed")
                + " "
                + str(success_count)
                + ", "
                + _("core.management.commands.transform_to_sjtsk.Command._transform_pian.finished_errors")
                + " "
                + str(error_count)
            )
        )

    def _transform_nalez(self):
        """
        Transformuje nalez.

        :return: Vrací výsledek provedené operace.
        """
        from pas.models import SamostatnyNalez

        self.stdout.write(_("core.management.commands.transform_to_sjtsk.Command._transform_nalez.processing"))

        query_select = (
            "select samostatny_nalez.id, ST_AsText(samostatny_nalez.geom) as geometry "
            " from public.samostatny_nalez "
            " where samostatny_nalez.geom is not null "
            " and (samostatny_nalez.geom_sjtsk is null)"
            " order by samostatny_nalez.id"
        )
        query_update = (
            "update public.samostatny_nalez "
            " set geom_sjtsk = ST_GeomFromText(%s) "
            " where samostatny_nalez.geom_sjtsk is null and samostatny_nalez.id=%s "
        )

        SNs = SamostatnyNalez.objects.raw(query_select)
        total = len(list(SNs))
        SNs = SamostatnyNalez.objects.raw(query_select)  # Re-execute query
        success_count = 0
        error_count = 0

        self.stdout.write(
            _("core.management.commands.transform_to_sjtsk.Command._transform_nalez.found") + " " + str(total)
        )

        for idx, SN in enumerate(SNs):
            if total > 0 and idx % max(total // 100, 1) == 0:
                percentage = round(idx / total * 100)
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.transform_to_sjtsk.Command._transform_nalez.progress")
                    + " "
                    + str(percentage)
                    + "%",
                    ending="",
                )

            geom = transform_geom_to_sjtsk(SN.geometry)
            if geom[1] == "OK":
                with connection.cursor() as cursor:
                    cursor.execute(query_update, [geom[0], SN.id])
                success_count += 1
            else:
                error_count += 1
                logger.error(
                    "core.management.commands.transform_to_sjtsk.Command._transform_nalez.error",
                    extra={"nalez_id": SN.id, "error": geom[1]},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.transform_to_sjtsk.Command._transform_nalez.error")
                        + " "
                        + str(SN.id)
                        + ": "
                        + str(geom[1])
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                _("core.management.commands.transform_to_sjtsk.Command._transform_nalez.finished_transformed")
                + " "
                + str(success_count)
                + ", "
                + _("core.management.commands.transform_to_sjtsk.Command._transform_nalez.finished_errors")
                + " "
                + str(error_count)
            )
        )

    def _transform_projekt(self):
        """
        Transformuje projekt.

        :return: Vrací výsledek provedené operace.
        """
        from projekt.models import Projekt

        self.stdout.write(_("core.management.commands.transform_to_sjtsk.Command._transform_projekt.processing"))

        query_select = (
            "select projekt.id,projekt.ident_cely,ST_AsText(projekt.geom) as geometry,ST_AsText(projekt.geom_sjtsk) as geometry_sjtsk "
            " from public.projekt "
            " where projekt.geom is not null "
            " and projekt.geom_sjtsk is null "
            " order by projekt.id"
        )
        query_update = (
            "update public.projekt "
            " set geom_sjtsk = ST_GeomFromText(%s) "
            " where projekt.geom_sjtsk is null and projekt.id=%s "
        )

        PRJs = Projekt.objects.raw(query_select)
        total = len(list(PRJs))
        PRJs = Projekt.objects.raw(query_select)  # Re-execute query
        success_count = 0
        error_count = 0

        self.stdout.write(
            _("core.management.commands.transform_to_sjtsk.Command._transform_projekt.found") + " " + str(total)
        )

        for idx, PRJ in enumerate(PRJs):
            if total > 100 and idx % max(total // 100, 1) == 0:
                percentage = round(idx / total * 100)
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.transform_to_sjtsk.Command._transform_projekt.progress")
                    + " "
                    + str(percentage)
                    + "%",
                    ending="",
                )

            geom = transform_geom_to_sjtsk(PRJ.geometry)
            if geom[1] == "OK":
                with connection.cursor() as cursor:
                    cursor.execute(query_update, [geom[0], PRJ.id])
                success_count += 1
            else:
                error_count += 1
                logger.error(
                    "core.management.commands.transform_to_sjtsk.Command._transform_projekt.error",
                    extra={"projekt_id": PRJ.id, "ident_cely": PRJ.ident_cely, "error": geom[1]},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.transform_to_sjtsk.Command._transform_projekt.error")
                        + " "
                        + str(PRJ.id)
                        + ": "
                        + str(geom[1])
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                _("core.management.commands.transform_to_sjtsk.Command._transform_projekt.finished_transformed")
                + " "
                + str(success_count)
                + ", "
                + _("core.management.commands.transform_to_sjtsk.Command._transform_projekt.finished_errors")
                + " "
                + str(error_count)
            )
        )

    def _transform_dokument(self):
        """
        Transformuje dokument.

        :return: Vrací výsledek provedené operace.
        """
        from dokument.models import DokumentExtraData

        self.stdout.write(_("core.management.commands.transform_to_sjtsk.Command._transform_dokument.processing"))

        query_select = (
            "select dokument_extra_data.dokument,ST_AsText(dokument_extra_data.geom) as geometry,ST_AsText(dokument_extra_data.geom_sjtsk) as geometry_sjtsk "
            " from public.dokument_extra_data "
            " where dokument_extra_data.geom is not null "
            " and dokument_extra_data.geom_sjtsk is null "
            " order by dokument_extra_data.dokument"
        )
        query_update = (
            "update public.dokument_extra_data "
            " set geom_sjtsk = ST_GeomFromText(%s) "
            " where dokument_extra_data.geom_sjtsk is null and dokument_extra_data.dokument=%s "
        )

        DOCs = DokumentExtraData.objects.raw(query_select)
        total = len(list(DOCs))
        DOCs = DokumentExtraData.objects.raw(query_select)  # Re-execute query
        success_count = 0
        error_count = 0

        self.stdout.write(
            _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.found") + " " + str(total)
        )

        for idx, DOC in enumerate(DOCs):
            if total > 100 and idx % max(total // 100, 1) == 0:
                percentage = round(idx / total * 100)
                self.stdout.write(
                    "\r"
                    + _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.progress")
                    + " "
                    + str(percentage)
                    + "%",
                    ending="",
                )

            try:
                geom = transform_geom_to_sjtsk(DOC.geometry)
                if geom[1] == "OK":
                    with connection.cursor() as cursor:
                        cursor.execute(query_update, [geom[0], DOC.pk])
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(
                        "core.management.commands.transform_to_sjtsk.Command._transform_dokument.error",
                        extra={"dokument_id": DOC.pk, "error": geom[1]},
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            "\n"
                            + _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.error")
                            + " "
                            + str(DOC.pk)
                            + ": "
                            + str(geom[1])
                        )
                    )
            except Exception as err:
                error_count += 1
                logger.warning(
                    "core.management.commands.transform_to_sjtsk.Command._transform_dokument.exception",
                    extra={"dokument_id": DOC.pk, "error": str(err)},
                )
                self.stdout.write(
                    self.style.ERROR(
                        "\n"
                        + _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.exception")
                        + " "
                        + str(DOC.pk)
                        + ": "
                        + str(err)
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.finished_transformed")
                + " "
                + str(success_count)
                + ", "
                + _("core.management.commands.transform_to_sjtsk.Command._transform_dokument.finished_errors")
                + " "
                + str(error_count)
            )
        )
