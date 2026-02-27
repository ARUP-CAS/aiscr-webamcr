import datetime
import io
import sys

from historie.models import Historie
from projekt.doc_utils import DocumentCreator
from PyRTF.document.paragraph import Cell, Paragraph, Table
from PyRTF.Elements import Document, ParagraphStyle, Renderer, Section, StyleSheet
from PyRTF.PropertySets import ParagraphPropertySet, TabPropertySet
from PyRTF.Styles import TextPropertySet, TextStyle

sys.path.append("../")


class ExpertniListCreator(DocumentCreator):
    """Zapouzdřuje chování třídy ``ExpertniListCreator`` pro modul ``webclient.projekt.rtf_utils``."""
    @staticmethod
    def _utf16_decimals(char, chunk_size=2):
        """Provádí funkci ``ExpertniListCreator._utf16_decimals`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        encoded_char = char.encode("utf-16-be")
        # Převede každých `chunk_size` bajtů na celé číslo.
        decimals = []
        for i in range(0, len(encoded_char), chunk_size):
            chunk = encoded_char[i : i + chunk_size]
            decimals.append(int.from_bytes(chunk, "big"))
        decimals = [str(x) for x in decimals]
        decimals = "".join(decimals)
        return f"\\u{decimals}G"

    @staticmethod
    def _convert_text(text):
        """Zpracuje volání ``ExpertniListCreator._convert_text`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        if text is None or len(str(text)) == 0:
            return ""
        text = [ExpertniListCreator._utf16_decimals(char) for char in str(text)]
        text = "".join(text)
        return text

    @staticmethod
    def _format_akce_str(akce):
        """Zpracuje volání ``ExpertniListCreator._format_akce_str`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        if akce.hlavni_typ is not None and akce.vedlejsi_typ is not None:
            return f"{akce.hlavni_typ}; {akce.vedlejsi_typ}"
        elif akce.hlavni_typ is not None:
            return str(akce.hlavni_typ)
        return ""

    @classmethod
    def _format_akce(cls, akce_all):
        """Zpracuje volání ``ExpertniListCreator._format_akce`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        if akce_all.count() > 0:
            akce_list = [cls._format_akce_str(akce) for akce in akce_all if akce.hlavni_typ is not None]
            return " ".join(akce_list)
        else:
            return ""

    def _get_vysledek_text(self):
        """Provádí funkci ``ExpertniListCreator._get_vysledek_text`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        if self.popup_parametry["vysledek"] == "pozitivni":
            text = """Potvrzujeme, že došlo ke splnění oznamovací povinnosti a bylo umožněno provést na dotčeném \n\
            území záchranný archeologický výzkum podle ustanovení § 22, odst. 2, zákona č. 20/1987 Sb., o státní \n\
            památkové péči. V průběhu výzkumu byly vyzvednuty či dokumentovány archeologické nálezy.
            """
        elif self.popup_parametry["vysledek"] == "negativni":
            text = """Potvrzujeme, že došlo ke splnění oznamovací povinnosti a bylo umožněno provést na dotčeném \n\
            území záchranný archeologický výzkum podle ustanovení § 22, odst. 2, zákona č. 20/1987 Sb., o státní \n\
            památkové péči. V průběhu výzkumu nebyly vyzvednuty ani dokumentovány žádné archeologické nálezy.
            """
        else:
            text = self.popup_parametry["poznamka_popis"]
        text = " ".join(text.split())
        return self._convert_text(text.replace("\n", ""))

    def _get_typ_vyzkumu_text(self):
        """Provádí funkci ``ExpertniListCreator._get_typ_vyzkumu_text`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        from projekt.forms import TYP_VYZKUMU_CHOICES

        return str(dict(TYP_VYZKUMU_CHOICES).get(self.popup_parametry["typ_vyzkumu"]))

    def _generate_text(self):
        """Provádí funkci ``ExpertniListCreator._generate_text`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        result = StyleSheet()
        normal_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22))
        normal_text_par_style = ParagraphStyle(
            "NormalText", normal_text.Copy(), ParagraphPropertySet(alignment=ParagraphPropertySet.JUSTIFY)
        )
        self.stylesheet.ParagraphStyles.append(normal_text_par_style)

        bold_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22))
        bold_text.textProps.bold = True
        bold_text_par_style = ParagraphStyle("BoldText", bold_text.Copy(), ParagraphPropertySet(space_before=30))
        self.stylesheet.ParagraphStyles.append(bold_text_par_style)

        italic_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22))
        italic_text.textProps.italic = True
        italic_text_par_style = ParagraphStyle("ItalicText", italic_text.Copy())
        self.stylesheet.ParagraphStyles.append(italic_text_par_style)

        footer_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22, colour=result.Colours.Grey))
        footer_text_par_style = ParagraphStyle(
            "FooterText", footer_text.Copy(), ParagraphPropertySet(alignment=ParagraphPropertySet.CENTER)
        )
        self.stylesheet.ParagraphStyles.append(footer_text_par_style)

        section = Section()
        self.docucment.Sections.append(section)

        if "cislo_jednaci" in self.popup_parametry and self.popup_parametry["cislo_jednaci"] != "":
            p = Paragraph(
                self._convert_text(f"Č.j.: {self.popup_parametry['cislo_jednaci']}"),
                ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT),
            )
            section.append(p)
        p = Paragraph(
            self.stylesheet.ParagraphStyles.Heading1,
            self._convert_text("POTVRZENÍ O PROVEDENÍ ARCHEOLOGICKÉHO VÝZKUMU – EXPERTNÍ LIST"),
            ParagraphPropertySet(alignment=ParagraphPropertySet.CENTER),
        )
        section.append(p)

        table = Table(TabPropertySet.DEFAULT_WIDTH * 6, TabPropertySet.DEFAULT_WIDTH * 6)

        table_texts = [
            (
                "Číslo akce/oznámení v centrální evidenci (AMČR):",
                Paragraph(self.stylesheet.ParagraphStyles.BoldText, self.projekt.ident_cely),
            ),
            ("Datum přijetí oznámení:", self.historie.datum_zmeny.strftime("%d. %m. %Y") if self.historie else ""),
            ("Interní označení:", self.projekt.uzivatelske_oznaceni),
            (
                "Výzkum provedla organizace:",
                Paragraph(self.stylesheet.ParagraphStyles.BoldText, self._convert_text(self.projekt.organizace.nazev)),
            ),
            *(
                []
                if self.projekt.organizace.adresa is None or self.projekt.organizace.adresa == ""
                else [("", f"{self.projekt.organizace.adresa}")]
            ),
            *(
                []
                if self.projekt.organizace.email is None or self.projekt.organizace.email == ""
                else [("", f"E-mail: {self.projekt.organizace.email}")]
            ),
            *(
                []
                if self.projekt.organizace.telefon is None or self.projekt.organizace.telefon == ""
                else [("", f"Tel.: {self.projekt.organizace.telefon}")]
            ),
            (
                "Katastrální území (okres):",
                f"{self.projekt.hlavni_katastr.nazev} ({self.projekt.hlavni_katastr.okres.nazev})",
            ),
            ("Lokalizace:", self.projekt.lokalizace),
            ("Parcelní číslo:", self.projekt.parcelni_cislo),
        ]
        if self.projekt.geom is not None:
            table_texts += [
                (
                    "Souřadnice (WGS-84):",
                    (
                        f"{self.projekt.geom.centroid.y}N, {self.projekt.geom.centroid.x}E"
                        if self.projekt.geom is not None
                        else None
                    ),
                )
            ]

        table_texts += [
            ("Podnět k provedení výzkumu:", self.projekt.podnet),
        ]
        if self.projekt.oznaceni_stavby is not None:
            table_texts += [
                ("Označení stavby:", self.projekt.oznaceni_stavby),
            ]

        table_texts += [
            ("Oznamovatel:", self.projekt.oznamovatel.oznamovatel if self.projekt.has_oznamovatel() else ""),
            (
                "Zástupce oznamovatele / dodavatel:",
                (
                    f"{self.projekt.oznamovatel.odpovedna_osoba} ({self.projekt.oznamovatel.telefon}; {self.projekt.oznamovatel.email})"
                    if self.projekt.has_oznamovatel()
                    else ""
                ),
            ),
            (
                ["Datum výzkumu:", f"{self.format_date(self.projekt.datum_zahajeni)}"]
                if self.projekt.datum_zahajeni == self.projekt.datum_ukonceni
                else [
                    "Datum výzkumu:",
                    f"{self.format_date(self.projekt.datum_zahajeni)} - {self.format_date(self.projekt.datum_ukonceni)}",
                ]
            ),
            ("Typ výzkumu:", self._get_typ_vyzkumu_text()),
        ]

        if self.projekt.akce_set.count() > 0:
            table_texts += [
                ("Druh evidence:", self._format_akce(self.projekt.akce_set.all())),
                ("Uložení nálezů / dokumentace:", ""),
            ]

        table_texts += [
            (
                "Osoba odpovědná za výzkum:",
                f"{self.projekt.vedouci_projektu.jmeno} {self.projekt.vedouci_projektu.prijmeni}",
            ),
        ]

        bold_text = ParagraphStyle(
            "TableLeftColumnText",
            bold_text.Copy(),
            ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT, space_before=30),
        )
        self.stylesheet.ParagraphStyles.append(bold_text)
        right_text = ParagraphStyle(
            "TableRightColumnText",
            normal_text.Copy(),
            ParagraphPropertySet(alignment=ParagraphPropertySet.LEFT, space_before=30),
        )
        self.stylesheet.ParagraphStyles.append(right_text)
        for row in table_texts:
            c1 = Cell(Paragraph(self._convert_text(row[0]), self.stylesheet.ParagraphStyles.TableLeftColumnText))
            if row[1] is not None:
                if type(row[1]) is str:
                    if len(row[1]) > 0:
                        c2 = Cell(
                            Paragraph(self._convert_text(row[1]), self.stylesheet.ParagraphStyles.TableRightColumnText)
                        )
                    else:
                        continue
                else:
                    c2 = Cell(row[1])
            else:
                continue
            table.AddRow(c1, c2)
        section.append(table)

        p = Paragraph(self.stylesheet.ParagraphStyles.Heading2, self._convert_text("Výsledek (poznámka):"))
        section.append(p)

        p = Paragraph(self.stylesheet.ParagraphStyles.NormalText, self._get_vysledek_text())
        section.append(p)

        p = Paragraph("", ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)

        p = Paragraph(
            self._convert_text(f"Dne {datetime.datetime.now().strftime('%d. %m. %Y')}"),
            ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT),
        )
        section.append(p)

        p = Paragraph("", ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)
        section.append(p)
        section.append(p)

        p = Paragraph(
            self._convert_text("................................................"),
            ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT),
        )
        section.append(p)

        p = Paragraph(
            self.stylesheet.ParagraphStyles.ItalicText,
            self._convert_text("razítko a podpis"),
            ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT),
        )
        section.append(p)

        p = Paragraph(
            self.stylesheet.ParagraphStyles.FooterText,
            self._convert_text(
                "Dokument byl vytvořen v systému Archeologická mapa České republiky (AMČR) web: http://www.archeologickamapa.cz/, e-mail: info@amapa.cz"
            ),
        )
        section.Footer.append(p)

    @staticmethod
    def _open_file(name):
        """Zpracuje volání ``ExpertniListCreator._open_file`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        return open(name, "w")

    def build_document(self) -> io.StringIO:
        """Provádí funkci ``ExpertniListCreator.build_document`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        self._generate_text()
        output = io.StringIO()
        DR = Renderer()
        self.docucment.DefaultLanguage = 1029
        DR.Write(self.docucment, output)
        output.seek(0)
        return output

    def __init__(self, projekt, popup_parametry=None):
        """Provádí funkci ``ExpertniListCreator.__init__`` v rámci modulu ``webclient.projekt.rtf_utils``."""
        from projekt.models import Projekt

        self.projekt: Projekt = projekt
        self.docucment = Document()
        self.stylesheet = self.docucment.StyleSheet
        self.popup_parametry = popup_parametry
        historie_query = self.projekt.historie.historie_set.filter(typ_zmeny__in=("PX0", "PX1"))
        if historie_query.count():
            self.historie: Historie = historie_query.last()
        else:
            self.historie = None
