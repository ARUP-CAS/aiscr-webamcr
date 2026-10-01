"""
Testy nabídky autorů ve formulářích dokumentu (issue #3421).

Našeptávací widget vykresluje jen vybrané hodnoty a popisek k nim hledá ve svých volbách. Testy
hlídají, že se po neúspěšné validaci zobrazí jména autorů, ne jejich čísla. Databáze se nepoužívá –
dotazy do ní jsou nahrazeny mockem.
"""

from unittest import mock

from django.test import SimpleTestCase


class _Pole:
    """Náhrada za formulářové pole nesoucí pouze widget s nabídkou."""

    def __init__(self):
        self.widget = mock.Mock(choices=None)


class _Form:
    """Odlehčená náhrada za formulář dokumentu s polem ``autori``."""

    def __init__(self, is_bound, hodnota=None, instance_pk=None):
        self.is_bound = is_bound
        self.fields = {"autori": _Pole()}
        self.instance = mock.Mock(pk=instance_pk)
        self._hodnota = hodnota

    def __getitem__(self, nazev):
        return mock.Mock(value=mock.Mock(return_value=self._hodnota))


def _s_osobami(dvojice, poradi=()):
    """
    Nahradí dotazy na osoby pevnými daty.

    :param dvojice: Seznam dvojic ``(id, vypis_cely)`` vracených pro dotaz na popisky.
    :param poradi: Identifikátory autorů navázaných na dokument v jejich pořadí.
    :return: Kontextový manažer s mockem manageru osob.
    """
    manager = mock.MagicMock()
    manager.filter.return_value.values_list.return_value = dvojice
    manager.filter.return_value.order_by.return_value.values_list.return_value = list(poradi)
    return mock.patch("dokument.forms.Osoba.objects", manager)


class NabidkaAutoruTest(SimpleTestCase):
    """Testy funkce :func:`dokument.forms.nastav_nabidku_autoru`."""

    def _nabidka(self, form):
        """
        Spustí naplnění nabídky a vrátí ji.

        :param form: Náhradní formulář, jehož pole ``autori`` se naplní.
        :return: Seznam dvojic ``(id, popisek)`` v nabídce widgetu.
        """
        from dokument.forms import nastav_nabidku_autoru

        nastav_nabidku_autoru(form)
        return form.fields["autori"].widget.choices

    def test_odeslane_hodnoty_dostanou_jmena(self):
        """Po odeslání formuláře se pro zadané autory nabídnou jejich jména, ne čísla."""
        form = _Form(is_bound=True, hodnota=["30958"])
        with _s_osobami([(30958, "Absolon, A.")]):
            self.assertEqual(self._nabidka(form), [(30958, "Absolon, A.")])

    def test_zachovava_poradi_odeslanych_autoru(self):
        """Pořadí v nabídce odpovídá pořadí odeslaných hodnot, ne pořadí z databáze."""
        form = _Form(is_bound=True, hodnota=["31146", "30958"])
        with _s_osobami([(30958, "Absolon, A."), (31146, "Abrahám, Milan")]):
            self.assertEqual(self._nabidka(form), [(31146, "Abrahám, Milan"), (30958, "Absolon, A.")])

    def test_neznama_hodnota_se_vynecha(self):
        """Hodnota bez odpovídající osoby se do nabídky nedostane, validace ji odmítne zvlášť."""
        form = _Form(is_bound=True, hodnota=["30958", "neexistuje"])
        with _s_osobami([(30958, "Absolon, A.")]):
            self.assertEqual(self._nabidka(form), [(30958, "Absolon, A.")])

    def test_novy_dokument_ma_prazdnou_nabidku(self):
        """Nevyplněný formulář nového dokumentu nenabízí žádné autory."""
        form = _Form(is_bound=False)
        with _s_osobami([]):
            self.assertEqual(self._nabidka(form), [])

    def test_existujici_dokument_bere_autory_ze_zaznamu(self):
        """U existujícího dokumentu vychází nabídka z navázaných autorů v jejich pořadí."""
        form = _Form(is_bound=False, instance_pk=42)
        with _s_osobami([(30958, "Absolon, A."), (31146, "Abrahám, Milan")], poradi=[31146, 30958]):
            self.assertEqual(self._nabidka(form), [(31146, "Abrahám, Milan"), (30958, "Absolon, A.")])
