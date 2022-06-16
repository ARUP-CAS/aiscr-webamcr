import datetime
import struct
import sys

from PyRTF.Elements import Renderer, Document, Section, StyleSheet, ParagraphStyle
from PyRTF.PropertySets import TabPropertySet, ParagraphPropertySet
from PyRTF.Styles import TextStyle, TextPropertySet
from PyRTF.document.paragraph import Cell, Paragraph, Table
from historie.models import Historie
from projekt.doc_utils import DocumentCreator
from webclient.settings.base import MEDIA_ROOT

sys.path.append('../')


class ExpertniListCreator(DocumentCreator):
    @staticmethod
    def _utf16_decimals(char, chunk_size=2):
        encoded_char = char.encode('utf-16-be')
        # convert every `chunk_size` bytes to an integer
        decimals = []
        for i in range(0, len(encoded_char), chunk_size):
            chunk = encoded_char[i:i + chunk_size]
            decimals.append(int.from_bytes(chunk, 'big'))
        decimals = [str(x) for x in decimals]
        decimals = "".join(decimals)
        return f"\\u{decimals}G"

    @staticmethod
    def _convert_text(text):
        if text is None or len(str(text)) == 0:
            return ""
        text = [ExpertniListCreator._utf16_decimals(char) for char in str(text)]
        text = "".join(text)
        return text

    @staticmethod
    def _format_akce_str(akce):
        if akce.hlavni_typ is not None and akce.vedlejsi_typ is not None:
            return f"{akce.hlavni_typ}; {akce.vedlejsi_typ}"
        elif akce.hlavni_typ is not None:
            return str(akce.hlavni_typ)
        return ""

    @classmethod
    def _format_akce(cls, akce_all):
        if akce_all.count() > 0:
            akce_list = [cls._format_akce_str(akce) for akce in akce_all if akce.hlavni_typ is not None]
            return " ".join(akce_list)
        else:
            return ""

    def _get_vysledek_text(self):
        if self.popup_parametry["vysledek"] == "pozitivni":
            text = """Potvrzujeme, že došlo ke splnění oznamovací povinnosti a bylo umožněno provést na dotčeném 
            území záchranný archeologický výzkum podle ustanovení § 22, odst. 2, zákona č. 20/1987 Sb., o státní 
            památkové péči. V průběhu výzkumu byly vyzvednuty či dokumentovány archeologické nálezy.
            """
        elif self.popup_parametry["vysledek"] == "negativni":
            text = """Potvrzujeme, že došlo ke splnění oznamovací povinnosti a bylo umožněno provést na dotčeném 
            území záchranný archeologický výzkum podle ustanovení § 22, odst. 2, zákona č. 20/1987 Sb., o státní 
            památkové péči. V průběhu výzkumu nebyly vyzvednuty ani dokumentovány žádné archeologické nálezy.
            """
        else:
            text = self.popup_parametry["poznamka_popis"]
        return self._convert_text(text.replace("\n", ""))

    def _generate_text(self):
        result = StyleSheet()
        normal_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22))
        bold_text = TextStyle(TextPropertySet(result.Fonts.Arial, 22))
        bold_text.textProps.bold = True
        bold_text_par_style = ParagraphStyle('BoldText', bold_text.Copy())
        self.stylesheet.ParagraphStyles.append(bold_text_par_style)

        section = Section()
        self.docucment.Sections.append(section)

        if "cislo_jednaci" in self.popup_parametry:
            p = Paragraph(self._convert_text(f"Č.j.: {self.popup_parametry['cislo_jednaci']}"),
                          ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)
        p = Paragraph(self.stylesheet.ParagraphStyles.Heading1,
                      self._convert_text("POTVRZENÍ O PROVEDENÍ ARCHEOLOGICKÉHO VÝZKUMU – EXPERTNÍ LIST"),
                      ParagraphPropertySet(alignment=ParagraphPropertySet.CENTER))
        section.append(p)

        table = Table(TabPropertySet.DEFAULT_WIDTH * 6,
                      TabPropertySet.DEFAULT_WIDTH * 6)

        table_texts = [
            ("Číslo akce/oznámení v centrální evidenci (AMČR):", self.projekt.ident_cely),
            ("Datum přijetí oznámení:", self.historie.datum_zmeny.strftime("%d. %m. %Y") if self.historie else ""),
            ("Interní označení:", self.projekt.uzivatelske_oznaceni),
            ("Výzkum provedla organizace:",
             Paragraph(self.stylesheet.ParagraphStyles.BoldText, self._convert_text(self.projekt.organizace))),
            ("",
             f"{self.projekt.organizace.adresa}"),
            ("", f"E-mail: {self.projekt.organizace.email}"),
            ("", f"Tel.: {self.projekt.organizace.telefon}"),
            ("Katastrální území (okres):", self.projekt.hlavni_katastr.nazev),
            ("Lokalizace:", self.projekt.lokalizace),
            ("Parcelní číslo:", self.projekt.parcelni_cislo)
        ]
        if self.projekt.geom is not None:
            table_texts += [
                ("Souřadnice(WGS - 84):",
                 f"{self.projekt.geom.centroid.x} {self.projekt.geom.centroid.y}" if self.projekt.geom is not None else None)
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
            ("Zástupce oznamovatele / dodavatel:",
             self.projekt.oznamovatel.odpovedna_osoba if self.projekt.has_oznamovatel() else ""),
            ("Datum výzkumu:", f"{self.projekt.datum_zahajeni} - {self.projekt.datum_ukonceni}"),
            ("Typ výzkumu:", self.popup_parametry["typ_vyzkumu"]),
        ]

        if self.projekt.akce_set.count() > 0:
            table_texts += [
                ("Druh evidence:", self._format_akce(self.projekt.akce_set.all())),
                ("Uložení nálezů / dokumentace:", ""),
            ]

        table_texts += [
            ("Osoba odpovědná za výzkum:", self.projekt.vedouci_projektu),
        ]

        bold_text = ParagraphStyle('TableLeftColumnText', bold_text.Copy(),
                                   ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        self.stylesheet.ParagraphStyles.append(bold_text)
        for row in table_texts:
            c1 = Cell(Paragraph(self._convert_text(row[0]), self.stylesheet.ParagraphStyles.TableLeftColumnText))
            if row[1] is not None:
                if type(row[1]) is str:
                    if len(row[1]) > 0:
                        c2 = Cell(Paragraph(self._convert_text(row[1]), self.stylesheet.ParagraphStyles.Normal))
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

        p = Paragraph(self._get_vysledek_text(), ParagraphPropertySet(alignment=ParagraphPropertySet.JUSTIFY))
        section.append(p)

        p = Paragraph(self._convert_text(f"Dne {datetime.datetime.now().strftime('%d. %m. %Y')}"),
                      ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)

        p = Paragraph(self._convert_text("................................................"),
                      ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)

        p = Paragraph(self._convert_text("razítko a podpis"),
                      ParagraphPropertySet(alignment=ParagraphPropertySet.RIGHT))
        section.append(p)

    @staticmethod
    def _open_file(name):
        return open(name, 'w')

    def build_document(self):
        self._generate_text()
        path = f"{MEDIA_ROOT}/expertni_list_{self.projekt.ident_cely}.rtf"
        DR = Renderer()
        DR.Write(self.docucment, self._open_file(path))
        return path

    def __init__(self, projekt, popup_parametry=None):
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
