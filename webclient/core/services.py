import io
import logging
import re
from typing import List, Union

import pandas as pd
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management import call_command
from django.db.models import Count, Exists, OuterRef, Q

from .constants import (
    PERMISSIONS_IMPORT_SHEET,
    PERMISSIONS_SHEET_ACTION_NAME,
    PERMISSIONS_SHEET_APP_NAME,
    PERMISSIONS_SHEET_PRISTUPNOST_NAME,
    PERMISSIONS_SHEET_STAV_NAME,
    PERMISSIONS_SHEET_URL_NAME,
    PERMISSIONS_SHEET_VLASTNICTVI_NAME,
    PERMISSIONS_SHEET_ZAKLADNI_NAME,
)
from .exceptions import WrongCSVError, WrongSheetError
from .models import Permissions

logger = logging.getLogger(__name__)


class PermissionService:
    """
    Třída pro načtení oprávnení.
    """

    def __init__(self):
        """Inicializuje instanci třídy.
        
        :return: Funkce nevrací hodnotu (``None``)."""
        pass

    def run(self, docfile: InMemoryUploadedFile) -> tuple[pd.DataFrame, list[str]]:
        """Spustí hodnotu.
        
        :param docfile: Vstupní hodnota ``docfile`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if docfile.name and docfile.name.lower().endswith(".csv"):
            sheet = pd.read_csv(docfile)
            sheet = self.validate_and_prepare_csv(sheet)
        else:
            sheet = pd.read_excel(docfile, PERMISSIONS_IMPORT_SHEET)
            sheet = self.validate_and_prepare_sheet(sheet)
        with io.StringIO() as out:
            call_command("show_urls", "--format", "json", stdout=out)
            url_list = pd.read_json(io.StringIO(out.getvalue()))
        missing = self.find_missing_urls(sheet, url_list)
        Permissions.objects.all().delete()
        sheet["result"] = sheet.apply(self.check_save_row, axis=1, args=(url_list,))
        # 1) existence unikátního páru
        unique_pair_exists = Exists(
            Permissions.objects.filter(
                address_in_app=OuterRef("address_in_app"),
                main_role=OuterRef("main_role"),
            )
            .values("address_in_app", "main_role")
            .annotate(cnt=Count("id"))
            .filter(cnt=1)
        )
        # 2) existence záznamu se stejnou kombinací, ale base = False
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
        sheet.drop(columns=sheet.columns[3:22], inplace=True)
        sheet = sheet.reset_index(drop=True)
        logger.debug(sheet.info())
        return sheet, missing

    def validate_and_prepare_csv(self, csv_sheet: pd.DataFrame) -> pd.DataFrame:
        """
        Metoda pro validaci importovaného csv.
        """
        expected = [
            "app",
            "URL",
            "action",
            "Základní_A",
            "Základní_B",
            "Základní_C",
            "Základní_D",
            "Základní_E",
            "Stav_B",
            "Stav_C",
            "Stav_D",
            "Stav_E",
            "Vlastnictví_B",
            "Vlastnictví_C",
            "Vlastnictví_D",
            "Vlastnictví_E",
            "Přístupnost_B",
            "Přístupnost_C",
            "Přístupnost_D",
            "Přístupnost_E",
        ]
        actual = [col.strip() for col in csv_sheet.columns]
        if actual[: len(expected)] != expected:
            raise WrongCSVError
        return csv_sheet

    def validate_and_prepare_sheet(self, sheet: pd.DataFrame) -> pd.DataFrame:
        """
        Metoda pro validaci importovaného excelu a jeho úpravu.
        """
        if (
            not sheet.columns[3] == PERMISSIONS_SHEET_ZAKLADNI_NAME
            or not sheet.columns[8] == PERMISSIONS_SHEET_STAV_NAME
            or not sheet.columns[12] == PERMISSIONS_SHEET_VLASTNICTVI_NAME
            or not sheet.columns[16] == PERMISSIONS_SHEET_PRISTUPNOST_NAME
        ):
            raise WrongSheetError
        sheet.columns = sheet.iloc[0]
        sheet = sheet[1:]
        sheet = sheet.reset_index(drop=True)
        if (
            not sheet.columns[0] == PERMISSIONS_SHEET_APP_NAME
            or not sheet.columns[1] == PERMISSIONS_SHEET_URL_NAME
            or not sheet.columns[2] == PERMISSIONS_SHEET_ACTION_NAME
            or not sheet.columns[3] == "A"
        ):
            raise WrongSheetError
        i = 4
        while i < 20:
            if (
                not sheet.columns[i] == "B"
                or not sheet.columns[i + 1] == "C"
                or not sheet.columns[i + 2] == "D"
                or not sheet.columns[i + 3] == "E"
            ):
                raise WrongSheetError
            i = i + 4

        return sheet

    def find_missing_urls(self, sheet: pd.DataFrame, url_list: pd.DataFrame) -> List[str]:
        """
        Najde URL, která chybí v importní tabulce, ale v projektu
        existují, a vrátí jejich seznam.
        ignorované URL ('admin/', '__debug__/')

        :param sheet: DataFrame se vstupní tabulkou oprávnění.
        :type sheet: pandas.DataFrame
        :param url_list: DataFrame se seznamem URL z projektu.
        :type url_list: pandas.DataFrame
        :return: Seznam chybějících URL.
        :rtype: list[str]
        """
        expected_urls = (
            sheet[["app", "URL"]]
            .apply(
                lambda r: (
                    f"{r['URL'].strip()}" if r["app"].strip() == "core" else f"{r['app'].strip()}/{r['URL'].strip()}"
                ),
                axis=1,
            )
            .str.replace("//+", "/", regex=True)
            .str.lstrip("/")
            .tolist()
        )
        expected_urls = set(expected_urls)
        project_urls = url_list["url"].str.lstrip("/").tolist()
        project_urls = set(project_urls)
        IGNORE_PREFIXES = ("admin/", "__debug__/")

        project_urls = {u for u in project_urls if not u.startswith(IGNORE_PREFIXES)}
        return sorted(project_urls - expected_urls)

    def check_save_row(
        self,
        row: pd.Series,
        url_list: pd.DataFrame,
    ) -> Union[str, list[str]]:
        """
        Zkontroluje a zpracuje jeden řádek importního souboru s oprávněními
        a uloží odpovídající záznamy do databáze.

        :param row: Řádek importovaných dat.
        :type row: pandas.Series
        :param url_list: Seznam dostupných URL v projektu.
        :type url_list: pandas.DataFrame
        :return: Textový stav výsledku nebo seznam výsledků pro jednotlivé role.
        :rtype: str nebo list[str]
        """
        number_to_role = ["B", "C", "D", "E"]
        if row.iloc[1] == "/":
            row.iloc[1] = ""

        url = "/" + str(row.iloc[0]) + "/" + str(row.iloc[1]) if row.iloc[0] != "core" else "/" + str(row.iloc[1])
        if url_list["url"].eq(url).any():
            if pd.isna(row.iloc[2]) or row.iloc[2] in Permissions.actionChoices.values:
                i = 0
                row_result = list()
                while i < 4:
                    row_result.append(self.save_permission(row, i))
                    i += 1
                if all(i is True for i in row_result):
                    return "ALL OK"
                else:
                    results = []
                    for idx, i in enumerate(row_result):
                        if i is True:
                            results.append(str(number_to_role[idx] + " OK"))
                        else:
                            results.append(str(number_to_role[idx] + " NOK"))
                return results
            else:
                return "NOK action"
        else:
            return "NOK address"

    def save_permission(self, row: pd.Series, i: int) -> bool:
        """
        Zkontroluje a uloží jedno konkrétní oprávnění z daného řádku
        importního souboru.

        :param row: Řádek s importovanými daty.
        :type row: pandas.Series
        :param i: Index zpracovávané role/sloupce.
        :type i: int
        :return: True při úspěšném uložení, jinak False.
        :rtype: bool
        """
        ROLE_COL_OFFSET = 4
        STATUS_COL_OFFSET = 8
        OWNERSHIP_COL_OFFSET = 12
        ACCESSIBILITY_COL_OFFSET = 16

        if row.iloc[0] != "core":
            address = str(row.iloc[0]) + "/" + str(row.iloc[1])
        else:
            address = str(row.iloc[1])
        if row.iloc[ROLE_COL_OFFSET + i] == "X":
            Permissions.objects.create(
                address_in_app=address,
                base=False,
                main_role=Group.objects.get(id=i + 1),
                action=None if pd.isna(row.iloc[2]) else row.iloc[2],
            )
            return True
        elif row.iloc[ROLE_COL_OFFSET + i] == "*":
            base = True
        else:
            return False
        if "|" in row.iloc[STATUS_COL_OFFSET + i]:
            n = 0
            results = list()
            for n, value in enumerate(row.iloc[STATUS_COL_OFFSET + i].split("|")):
                new_row = row.copy()
                new_row.iloc[STATUS_COL_OFFSET + i] = row.iloc[STATUS_COL_OFFSET + i].split("|")[n].strip()
                if len(row.iloc[OWNERSHIP_COL_OFFSET + i].split("|")) > 1:
                    new_row.iloc[OWNERSHIP_COL_OFFSET + i] = row.iloc[OWNERSHIP_COL_OFFSET + i].split("|")[n].strip()
                else:
                    new_row.iloc[OWNERSHIP_COL_OFFSET + i] = row.iloc[OWNERSHIP_COL_OFFSET + i]
                if len(row.iloc[ACCESSIBILITY_COL_OFFSET + i].split("|")) > 1:
                    new_row.iloc[ACCESSIBILITY_COL_OFFSET + i] = (
                        row.iloc[ACCESSIBILITY_COL_OFFSET + i].split("|")[n].strip()
                    )
                else:
                    new_row.iloc[ACCESSIBILITY_COL_OFFSET + i] = row.iloc[ACCESSIBILITY_COL_OFFSET + i]
                results.append(self.save_permission(new_row, i))
            if all(a is True for a in results):
                return True
            else:
                return False
        else:
            if row.iloc[STATUS_COL_OFFSET + i] == "*":
                status = None
            elif self.check_status_regex(row.iloc[STATUS_COL_OFFSET + i]):
                status = row.iloc[STATUS_COL_OFFSET + i]
            else:
                return False
        if row.iloc[OWNERSHIP_COL_OFFSET + i] == "*":
            ownership = None
        elif row.iloc[OWNERSHIP_COL_OFFSET + i].endswith(".my"):
            ownership = Permissions.ownershipChoices.my
        elif row.iloc[OWNERSHIP_COL_OFFSET + i].endswith(".ours"):
            ownership = Permissions.ownershipChoices.our
        else:
            return False
        if row.iloc[ACCESSIBILITY_COL_OFFSET + i] == "*":
            accessibility = None
        elif row.iloc[ACCESSIBILITY_COL_OFFSET + i].endswith("(my)"):
            accessibility = Permissions.ownershipChoices.my
        elif row.iloc[ACCESSIBILITY_COL_OFFSET + i].endswith("(ours)"):
            accessibility = Permissions.ownershipChoices.our
        else:
            return False
        Permissions.objects.create(
            address_in_app=address,
            base=base,
            main_role=Group.objects.get(id=i + 1),
            status=status,
            ownership=ownership,
            accessibility=accessibility,
            action=None if pd.isna(row.iloc[2]) else row.iloc[2],
        )
        return True

    def check_status_regex(self, cell: str) -> bool:
        """
        Metoda pro kontrolu správneho zadáni statusu v excelu.
        """
        return bool(re.fullmatch(r"(<|>|)[A-Z]{1,2}\d{1}", cell) or re.fullmatch(r"\D{1,2}\d{1}-\D{1,2}\d{1}", cell))
