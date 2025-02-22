# flake8: noqa: E221, E222, W291, F541

import datetime
import io
import logging
import os
from abc import ABC, abstractmethod
from io import BytesIO

from core.constants import (
    DOC_KOMU,
    DOC_REDITEL,
    DOK_ADRESA,
    DOK_EMAIL,
    DOK_MESTO,
    DOK_TELEFON,
    DOK_VE_MESTE,
    OBLAST_CECHY,
)
from core.repository_connector import FedoraRepositoryConnector, RepositoryBinaryFile
from heslar.models import RuianKraj
from reportlab.lib import utils
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ListStyle, ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, PageBreak, Paragraph, SimpleDocTemplate, Table

from webclient.settings.base import STATIC_ROOT

logger_s = logging.getLogger(__name__)

PAGESIZE = (210 * mm, 297 * mm)
BASE_MARGIN = 20 * mm
HEADER_HEIGHT = 10 * mm
HEADER_IMAGES = ("logo-arup-cs.png", "logo-arub-cs.png", "logo-am-colored-cs.png")

# Try except because of failing sphinx-build

path = None
try:
    path = os.path.join(STATIC_ROOT, "fonts", "OpenSans-Regular.ttf")
    pdfmetrics.registerFont(TTFont("OpenSans", path))
    path = os.path.join(STATIC_ROOT, "fonts", "OpenSans-Bold.ttf")
    pdfmetrics.registerFont(TTFont("OpenSansBold", path))
    path = os.path.join(STATIC_ROOT, "fonts", "OpenSans-Italic.ttf")
    pdfmetrics.registerFont(TTFont("OpenSansItalic", path))
    path = os.path.join(STATIC_ROOT, "fonts", "OpenSans-BoldItalic.ttf")
    pdfmetrics.registerFont(TTFont("OpenSansBoldItalic", path))
    registerFontFamily(
        "OpenSans", normal="OpenSans", bold="OpenSansBold", italic="OpenSansItalic", boldItalic="OpenSansBoldItalic"
    )
except Exception:
    # This will be triggered during collectstatic
    logger_s.error("doc_utils.font.error", extra={"path": path})

Title = "Hello world"
pageinfo = "platypus example"


def draw_image(filename, canvas, counter):
    img = utils.ImageReader(filename)
    iw, ih = img.getSize()
    target_height = HEADER_HEIGHT
    target_width = target_height / ih * iw
    if counter == 0:
        x = BASE_MARGIN
    elif counter == 1:
        x = PAGESIZE[0] / 2 - target_width / 2
    elif counter == 2:
        x = PAGESIZE[0] - BASE_MARGIN - target_width
    else:
        return
    canvas.drawImage(
        filename,
        x=x,
        y=PAGESIZE[1] - target_height - 10 * mm,
        width=target_width,
        height=target_height,
        mask="auto",
    )


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("OpenSans", 10)
    page_number_text = "%d" % (doc.page)
    canvas.drawCentredString(PAGESIZE[0] / 2, 10 * mm, page_number_text)
    canvas.restoreState()


def draw_header(canvas, doc):
    counter = 0
    for filename in HEADER_IMAGES:
        draw_image(f"static/img/{filename}", canvas, counter)
        counter += 1
    add_page_number(canvas, doc)


class DocumentCreator(ABC):
    FILENAME_PREFIX = ""

    def __init__(self, oznamovatel, projekt, fedora_transaction, additional=False):
        from oznameni.models import Oznamovatel

        self.oznamovatel: Oznamovatel = oznamovatel
        from projekt.models import Projekt

        self.projekt: Projekt = projekt
        self.dok_index = 0 if OBLAST_CECHY in self.projekt.ident_cely.upper() else 1

        self.fedora_transaction = fedora_transaction
        self.additional = additional
        self.styles = getSampleStyleSheet()
        self._create_style_dict()
        self.texts = {}
        self._generate_text()

    def _create_signature(self):
        self.texts["doc_sign_1"] = "S pozdravem"
        self.texts["doc_sign_2"] = DOC_REDITEL[self.dok_index]
        self.texts["doc_sign_3"] = f"ředitel<br/>Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i."

    def _create_style_dict(self):
        self.styles.add(
            ParagraphStyle(
                "amBodyText",
                fontName="OpenSans",
                fontSize=12,
                parent=self.styles["BodyText"],
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                leading=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                "amBodyTextCenter", parent=self.styles["amBodyText"], alignment=TA_CENTER, fontName="OpenSans"
            )
        )
        self.styles.add(
            ParagraphStyle(
                "amBodyTextSmallerSpaceAfter",
                parent=self.styles["amBodyText"],
                spaceAfter=0,
                spaceBefore=0,
                fontName="OpenSans",
            )
        )
        self.styles.add(
            ParagraphStyle("amHeading1", parent=self.styles["amBodyText"], alignment=TA_CENTER, fontName="OpenSansBold")
        )
        self.styles.add(
            ParagraphStyle("amDatum", parent=self.styles["amBodyText"], alignment=TA_RIGHT, fontName="OpenSans")
        )
        self.styles.add(
            ParagraphStyle("amVec", parent=self.styles["amBodyText"], alignment=TA_LEFT, fontName="OpenSansBold")
        )
        self.styles.add(
            ParagraphStyle("amHeading2", parent=self.styles["amBodyText"], alignment=TA_CENTER, fontName="OpenSansBold")
        )
        self.styles.add(
            ParagraphStyle("amPodpis1", parent=self.styles["amBodyText"], alignment=TA_CENTER, fontName="OpenSans")
        )
        self.styles.add(
            ParagraphStyle("amPodpis2", parent=self.styles["amBodyText"], alignment=TA_CENTER, fontName="OpenSans")
        )
        self.styles.add(ParagraphStyle("amPodpis3", parent=self.styles["amPodpis2"], fontSize=10, fontName="OpenSans"))

        self.styles.add(
            ListStyle(
                "amListText",
                fontName="OpenSans",
                fontSize=12,
                parent=self.styles["OrderedList"],
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                leading=20,
            )
        )
        self.styles.add(
            ListStyle("amListTextIndent", parent=self.styles["amListText"], leftIndent=10, fontName="OpenSans")
        )
        self.styles.add(
            ParagraphStyle(
                "amSignature",
                parent=self.styles["amBodyText"],
                alignment=TA_RIGHT,
                spaceAfter=0,
                spaceBefore=0,
                fontName="OpenSans",
            )
        )

    def _initiate_document(self):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN + HEADER_HEIGHT,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        return pdf_buffer, my_doc

    def _generate_repository_file(self, my_doc, document_content, pdf_buffer):
        my_doc.build(document_content, onFirstPage=draw_header, onLaterPages=draw_header)
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()

        postfix = "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        file = io.BytesIO()
        file.write(pdf_value)
        file.seek(0)
        filename = f"{self.FILENAME_PREFIX}_{self.projekt.ident_cely}{postfix}.pdf"

        con = FedoraRepositoryConnector(self.projekt, self.fedora_transaction)
        rep_bin_file: RepositoryBinaryFile = con.save_binary_file(filename, "application/pdf", file)
        return rep_bin_file

    @property
    def body_style(self):
        return self.styles["amBodyText"]

    @abstractmethod
    def _generate_text(self):
        pass

    @abstractmethod
    def build_document(self):
        pass


class OznameniPDFCreator(DocumentCreator):
    FILENAME_PREFIX = "oznameni"

    def _generate_text(self):
        self.texts["header_line_1"] = f"ARCHEOLOGICKÝ ÚSTAV AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i."
        self.texts["header_line_2"] = "REFERÁT ARCHEOLOGICKÉ PAMÁTKOVÉ PÉČE"
        # Condition check for automated testing
        if self.projekt.hlavni_katastr:
            kraj: RuianKraj = self.projekt.hlavni_katastr.okres.kraj
        else:
            kraj: RuianKraj = RuianKraj.objects.first()
        telefon = DOK_TELEFON.get(kraj.kod, DOK_TELEFON.get(0))
        self.texts[
            "header_line_3"
        ] = f"{DOK_ADRESA[self.dok_index]}<br/>{telefon}<br/>e-mail: {DOK_EMAIL[self.dok_index]}"
        self.texts[
            "header_line_4"
        ] = f"{DOK_VE_MESTE[self.dok_index]} {datetime.datetime.today().date().strftime('%d. %m. %Y').replace(' 0', ' ')}"

        self.texts[
            "doc_vec"
        ] = """
        Věc: Potvrzení o splnění oznamovací povinnosti dle § 22, odst. 2 zák. č. 20/1987
        """

        # Condition check for automated testing
        if self.projekt.historie.historie_set.exists():
            datum_zmeny = self.projekt.historie.historie_set.first().datum_zmeny
        else:
            datum_zmeny = datetime.datetime.today()

        self.texts[
            "doc_par_1"
        ] = f"""
        Potvrzujeme, že <strong>{self.oznamovatel.oznamovatel}</strong> ({self.oznamovatel.adresa}; tel: {self.oznamovatel.telefon}; \n\
        email: {self.oznamovatel.email}), jehož zastupuje {self.oznamovatel.odpovedna_osoba}, \n\
        ohlásil záměr <strong>{self.projekt.podnet}</strong> (označení stavby: {self.projekt.oznaceni_stavby}; \n\
        plánované zahájení: {self.projekt.planovane_zahajeni.lower.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''} - \n\
        {self.projekt.planovane_zahajeni.upper.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''} na \n\
        k. ú. <strong>{str(self.projekt.hlavni_katastr).replace("(", "(okr. ")}</strong>, parc. č. \n\
        {self.projekt.parcelni_cislo} ({self.projekt.lokalizace}) {DOC_KOMU[self.dok_index]}. \n\
        Oznámení provedl <strong>{datum_zmeny.strftime('%d. %m. %Y').replace(' 0', ' ')}</strong> pod evidenčním číslem \n\
        <strong>{self.projekt.ident_cely}</strong>. <strong>Tímto byla naplněna povinnost oznámit \n\
        zamýšlenou stavební nebo jinou činnost Archeologickému ústavu podle ustanovení § 22, odst. 2, zákona \n\
        č. 20/1987 Sb. Po schválení a registraci oznámení konkrétní organizací oprávněnou provádět archeologické \n\
        výzkumy Vás budeme informovat.</strong>
        """

        self.texts[
            "doc_par_2"
        ] = """TENTO DOKUMENT NESLOUŽÍ JAKO POTVRZENÍ O PROVEDENÍ ARCHEOLOGICKÉHO \n\
            VÝZKUMU PRO STAVEBNÍ ČI JINÉ ŘÍZENÍ."""

        self.texts[
            "doc_par_3"
        ] = """
        Oznamovatel je v návaznosti na oznámení povinen umožnit Archeologickému ústavu nebo oprávněné organizaci \n\
        provést na dotčeném území záchranný archeologický výzkum. O tomto mu bude potvrzení vystaveno samostatně, \n\
        a to organizací, která výzkum realizovala.
        """

        self._create_signature()

        self.texts["doc_attachment_heading_main_1"] = "PŘÍLOHA – INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ"

        self.texts["doc_attachment_heading_main_2"] = "POUČENÍ O PRÁVECH V SOUVISLOSTI S OCHRANOU OSOBNÍCH ÚDAJŮ"

        self.texts["doc_attachment_heading_1"] = "<u>ÚVODNÍ INFORMACE</u>"

        self.texts[
            "doc_attachment_par_1"
        ] = """
        Prosím, věnujte pozornost následujícímu dokumentu, jehož prostřednictvím Vám poskytujeme informace \n\
        o zpracování Vašich osobních údajů a o právech souvisejících s Vaší povinností jako stavebníka dle \n\
        § 22 odst. 2 zákona č. 20/1987 Sb., o státní památkové péči (dále rovněž jen „zákon“), poskytnout informace \n\
        o záměru provádět stavební činnost na území s archeologickými nálezy nebo jinou činnost, kterou by m
        ohlo být ohroženo provádění archeologických výzkumů, a to buď <strong>Archeologickému ústavu AV ČR, Praha, \n\
        v. v. i., IČ 67985912, se sídlem Letenská 4, 118 01 Praha 1,</strong> nebo <strong>Archeologickému ústavu \n\
        AV ČR, Brno, v. v. i., IČ 68081758, se sídlem Čechyňská 363/19, 602 00 Brno,</strong> jako oprávněným institucím \n\
        dle daného ustanovení zákona. Jakékoliv nakládání s osobními údaji se řídí platnými právními předpisy, \n\
        zejména zákonem o ochraně osobních údajů a nařízením Evropského parlamentu a Rady č. 2016/679 \n\
        ze dne 27. 4. 2016 o ochraně fyzických osob v souvislosti se zpracováním osobních údajů a o volném pohybu \n\
        těchto údajů a o zrušení směrnice 95/46/ES (dále jen „obecné nařízení o ochraně osobních údajů“). V souladu \n\
        s ustanovením čl. 13 a následujícího obecného nařízení o ochraně osobních údajů Vám jako tzv. subjektům \n\
        údajů poskytujeme následující informace. Tento dokument je veřejný a slouží k Vašemu řádnému informování \n\
        o rozsahu, účelu, době zpracování osobních údajů a k poučení o Vašich právech v souvislosti \n\
        s jejich ochranou.
        """

        self.texts[
            "doc_attachment_heading_2"
        ] = """
        <u>KDO JE SPRÁVCEM OSOBNÍCH ÚDAJŮ?</u>
        """

        self.texts[
            "doc_attachment_par_2"
        ] = """
        Společnými správci osobních údajů jsou Archeologický ústav AV ČR, Praha, v. v. i., IČ:67985912, \n\
        se sídlem Letenská 4, 118 01 Praha 1, a Archeologický ústav AV ČR, Brno, v. v. i., IČ:68081758, \n\
        se sídlem Čechyňská 363/19, 602 00 Brno (dále jen <strong>„Správce“</strong> či <strong>„Archeologický ústav“</strong>).
        """

        self.texts[
            "doc_attachment_heading_3"
        ] = """
        <u>OBECNĚ - CO VŠE PATŘÍ MEZI OSOBNÍ ÚDAJE?</u>
        """

        self.texts[
            "doc_attachment_par_3"
        ] = """
        Osobními údaji jsou veškeré informace vztahující se k identifikované či identifikovatelné fyzické osobě \n\
        (člověku), na základě kterých lze konkrétní fyzickou osobu přímo či nepřímo identifikovat. Mezi osobní údaje \n\
        tak patří široká škála informací, jako je například jméno, pohlaví, věk a datum narození, osobní stav, \n\
        fotografie (resp. jakékoliv zobrazení podoby), rodné číslo, místo trvalého pobytu, telefonní číslo, e-mail, \n\
        údaje o zdravotní pojišťovně, státní občanství, údaje o zdravotním stavu (fyzickém i psychickém), \n\
        ale také otisk prstu, podpis nebo IP adresa.
        """

        self.texts[
            "doc_attachment_heading_4"
        ] = """
        <u>ZA JAKÝM ÚČELEM A NA JAKÉM ZÁKLADĚ ZPRACOVÁVÁME VAŠE OSOBNÍ ÚDAJE?</u>
        """

        self.texts[
            "doc_attachment_par_4"
        ] = """
        Vaše osobní údaje zpracováváme, jelikož nám to ukládá zákon, konkrétně § 22 odst. 2 zákona č. 20/1987 Sb., \n\
        o státní památkové péči, který stanoví stavebníkovi, který má záměr provádět stavební činnost v území \n\
        s archeologickými nálezy, nebo jinou činnost, kterou by mohlo být ohroženo provádění archeologických \n\
        výzkumů, povinnost oznámit nejprve tento záměr Archeologickému ústavu. Odrazem této povinnosti stavebníka je \n\
        povinnost archeologického ústavu toto oznámení přijmout a zpracovat jej. Při zpracování oznámení stavebníka \n\
        dochází ze strany Archeologického ústavu ke zpracování osobních údajů stavebníka jako subjektu osobních údajů \n\
        dle čl. 6 odst. 1 písm. c), e) obecného nařízení o ochraně osobních údajů a Archeologický ústav je \n\
        v postavení Správce. Vaše osobní údaje v níže uvedeném rozsahu zpracováváme, pouze aby Vás \n\
        Archeologický ústav či jiná oprávněná organizace dle zákona mohly kontaktovat za účelem provedení \n\
        záchranného archeologického průzkumu.
        """

        self.texts[
            "doc_attachment_heading_5"
        ] = """
        <u>ROZSAH OSOBNÍCH ÚDAJŮ ZPRACOVÁVANÝCH SPRÁVCEM</u>
        """

        self.texts[
            "doc_attachment_par_5"
        ] = """
        Informujeme Vás, že Vaše osobní údaje jsou zpracovávány v rozsahu Vámi vyplněného formuláře, \n\
        a to konkrétně v rozsahu:"""

        self.texts["doc_attachment_par_5_bullets"] = ListFlowable(
            [
                Paragraph("jméno", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("příjmení", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("adresa", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("telefonní číslo", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("e-mail", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(
                    "údaje o nemovité věci (parcelní číslo a bližší specifikace předmětu oznámení).",
                    self.styles.get("amBodyTextSmallerSpaceAfter"),
                ),
            ],
            bulletType="bullet",
        )

        self.texts[
            "doc_attachment_heading_6"
        ] = """
        <u>DOBA ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
        """

        self.texts[
            "doc_attachment_par_6"
        ] = """
        Vaše osobní údaje budeme ukládat po dobu nezbytně nutnou maximálně však po dobu deseti let. Tyto lhůty \n\
        vyplývají ze zákonných požadavků a z titulu ochrany zájmu subjektu údajů na prokázání \n\
        splnění své zákonné povinnosti.
        """

        self.texts[
            "doc_attachment_heading_7"
        ] = """
        <u>DALŠÍ INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
        """

        self.texts[
            "doc_attachment_par_7_part_1"
        ] = """
        Osobní údaje subjektu údajů jsou zpracovávány automatizovaně v elektronické formě.
        Příjemci Vašich osobních údajů, resp. výsledků jejich zpracování jsou:
        """

        self.texts["doc_attachment_par_7_bullets"] = ListFlowable(
            [
                Paragraph("oprávněné organizace dle zákona", self.styles.get("amBodyTextSmallerSpaceAfter")),
            ],
            bulletType="bullet",
        )

        self.texts[
            "doc_attachment_par_7_part_2"
        ] = """
        Vaše osobní údaje nepředáváme a nemáme v úmyslu předat do třetí země nebo mezinárodní organizaci.
        """

        self.texts[
            "doc_attachment_heading_8"
        ] = """
        <u>POUČENÍ O PRÁVECH SUBJEKTŮ ÚDAJŮ</u>
        """

        self.texts[
            "doc_attachment_par_8_1"
        ] = """
        Subjekt údajů má právo požádat Správce o poskytnutí informace o zpracování jeho osobních údajů.
        """

        self.texts[
            "doc_attachment_par_8_2"
        ] = """
        Subjekt údajů má právo, aby Správce bez zbytečného odkladu opravil nepřesné osobní údaje, které se ho týkají. \n\
        S přihlédnutím k účelům zpracování má subjekt údajů právo na doplnění neúplných osobních údajů, a to i \n\
        poskytnutím dodatečného prohlášení.
        Subjekt údajů má právo, aby Správce bez zbytečného odkladu vymazal osobní údaje, které se daného subjektu \n\
        údajů týkají, a Správce má povinnost osobní údaje bez zbytečného odkladu vymazat, pokud je dán některý z důvodů \n\
        stanovených obecným nařízením o ochraně osobních údajů.
        """

        self.texts[
            "doc_attachment_par_8_3"
        ] = """
        Subjekt údajů má právo, aby Správce omezil zpracování osobních údajů, v případech stanovených obecným \n\
        nařízením o ochraně osobních údajů.
        """

        self.texts[
            "doc_attachment_par_8_4"
        ] = """
        Pokud se subjekt údajů domnívá, že došlo k porušení právních předpisů v souvislosti s ochranou jeho osobních \n\
        údajů, má právo podat stížnost u dozorového úřadu. Dozorovým úřadem je v České republice \n\
        Úřad pro ochranu osobních údajů.
        """

    def build_document(self) -> RepositoryBinaryFile:
        pdf_buffer, my_doc = self._initiate_document()
        styles = self.styles
        body_style = self.body_style
        header = [
            Paragraph(self.texts.get("header_line_1"), styles["amHeading1"]),
            Paragraph(self.texts.get("header_line_2"), styles["amBodyTextCenter"]),
            Paragraph(self.texts.get("header_line_3"), styles["amBodyTextCenter"]),
            Paragraph(self.texts.get("header_line_4"), styles["amDatum"]),
        ]

        tbl_data = [
            [Paragraph(self.texts.get("doc_sign_1"), styles["amPodpis1"]), Paragraph("", styles["amBodyText"])],
            [Paragraph("", styles["amBodyText"]), Paragraph(self.texts.get("doc_sign_2"), styles["amPodpis2"])],
            [Paragraph("", styles["amBodyText"]), Paragraph(self.texts.get("doc_sign_3"), styles["amPodpis3"])],
        ]
        tbl = Table(tbl_data)

        page_1 = [
            Paragraph(self.texts.get("doc_vec"), styles["amVec"]),
            Paragraph(self.texts.get("doc_par_1"), body_style),
            Paragraph(self.texts.get("doc_par_2"), styles["amHeading2"]),
            Paragraph(self.texts.get("doc_par_3"), body_style),
            tbl,
            PageBreak(),
        ]

        attachment = [
            Paragraph(self.texts.get("doc_attachment_heading_main_1"), styles["amHeading2"]),
            Paragraph(self.texts.get("doc_attachment_heading_main_2"), styles["amHeading2"]),
            Paragraph(self.texts.get("doc_attachment_heading_1"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_1"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_2"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_2"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_3"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_3"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_4"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_4"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_5"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_5"), body_style),
            self.texts.get("doc_attachment_par_5_bullets"),
            Paragraph(self.texts.get("doc_attachment_heading_6"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_6"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_7"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_7_part_1"), body_style),
            self.texts.get("doc_attachment_par_7_bullets"),
            Paragraph(self.texts.get("doc_attachment_par_7_part_2"), body_style),
            Paragraph(self.texts.get("doc_attachment_heading_8"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_8_1"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_8_2"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_8_3"), body_style),
            Paragraph(self.texts.get("doc_attachment_par_8_4"), body_style),
        ]
        document_content = header + page_1 + attachment
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)


class ZruseniPDFCreator(DocumentCreator):
    FILENAME_PREFIX = "zruseni"

    def _generate_text(self):
        self.texts["header_line_1"] = self.projekt.oznamovatel.oznamovatel
        self.texts["header_line_2"] = f"Zast.: {self.projekt.oznamovatel.odpovedna_osoba}"
        self.texts["header_line_3"] = self.projekt.oznamovatel.adresa
        self.texts["header_line_4"] = f"Email: {self.projekt.oznamovatel.email}"
        self.texts["header_line_5"] = f"Tel.: {self.projekt.oznamovatel.telefon}"

        self.texts["header_tab_1_1"] = "<strong>Oznámení ze dne</strong>"
        self.texts["header_tab_1_2"] = "<strong>Evidenční číslo</strong>"
        self.texts["header_tab_1_3"] = f"<strong>V {DOK_VE_MESTE[self.dok_index]} dne</strong>"
        self.texts["header_tab_2_1"] = (
            self.projekt.datum_oznameni.strftime("%d. %m. %Y") if self.projekt.datum_oznameni else ""
        )
        self.texts["header_tab_2_2"] = self.projekt.ident_cely
        self.texts["header_tab_2_3"] = datetime.datetime.now().strftime("%d. %m. %Y")

        self.texts["doc_vec"] = "Věc: Zrušení evidence záměru v informačním systému Archeologická mapa České republiky"

        self.texts["data_part_1"] = f"<strong>Podnět oznámení</strong>: {self.projekt.podnet}"
        self.texts[
            "data_part_2"
        ] = f"<strong>Katastrální území</strong>: {self.projekt.hlavni_katastr} ({self.projekt.hlavni_katastr.okres})"
        self.texts["data_part_3"] = f"<strong>Lokalizace</strong>: {self.projekt.lokalizace}"
        self.texts["data_part_4"] = f"<strong>Parcelní číslo</strong>: {self.projekt.parcelni_cislo}"
        self.texts["data_part_5"] = f"<strong>Označení stavby</strong>: {self.projekt.oznaceni_stavby}"
        self.texts[
            "data_part_6"
        ] = f"<strong>Plánované zahájení</strong>: {self.projekt.planovane_zahajeni.lower.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''} - {self.projekt.planovane_zahajeni.upper.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''}"

        self.texts[
            "doc_par_1"
        ] = f"""
        Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i., obdržel dne 
        {self.projekt.datum_oznameni.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.datum_oznameni else ''} 
        Vaše oznámení o zahájení stavebního (či jiného) záměru na území s archeologickými nálezy 
        {self.projekt.podnet} v k. ú. {self.projekt.hlavni_katastr} ({self.projekt.hlavni_katastr.okres}), který 
        eviduje pod evidenčním číslem {self.projekt.ident_cely}. 
        """

        self.texts[
            "doc_par_2"
        ] = f"""
        Ve věci uvedeného záměru si Vám dovolujeme sdělit, že předmětný projekt byl zrušen z následujícího důvodu:
        """

        self.texts["doc_par_3"] = f"<strong>{self.projekt.historie.historie_set.last().poznamka}</strong>"

        self.texts["notes_heading"] = "<strong>Poučení</strong>"
        self.texts["notes"] = ListFlowable(
            [
                Paragraph(
                    f"""
                    V případě dotazů se můžete na Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i., obracet 
                    skrze emailovou adresu {DOK_EMAIL[self.dok_index]}.
                    """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                    Jelikož nedošlo k provedení záchranného archeologického výzkumu, nelze po Archeologickém ústavu či jiné 
                    oprávněné organizaci, požadovat vydání potvrzení o jeho provedení pro potřeby správního řízení.
                    """,
                    self.body_style,
                ),
                [
                    Paragraph(
                        f"""
                    <strong>Bez ohledu na to, zda v souvislosti se stavební nebo jinou činností proběhl záchranný 
                    archeologický výzkum</strong>, Archeologický ústav AV ČR, 
                    {DOK_MESTO[self.dok_index]}, v. v. i., upozorňuje na:
                    """,
                        self.body_style,
                    ),
                    ListFlowable(
                        [
                            Paragraph(
                                """
                                    Ustanovení § 266 zákona č. 283/2021 Sb., stavební zákon, v platném znění, které stavebníkovi ukládá 
                                    <strong>povinnost oznámit stavebnímu úřadu nepředvídaný archeologický nebo paleontologický nález nebo 
                                    nález kulturně cenného předmětu, detailu stavby nebo chráněné části přírody</strong>. Stavebník je 
                                    také povinen učinit opatření nezbytná k tomu, aby nález nebyl poškozen nebo zničen, práce v místě 
                                    nálezu přerušit a zaznamenat do stavebního deníku čas a okolnosti nálezu, datum oznámení stavebnímu 
                                    úřadu a popis provedených opatření. <strong>Tato povinnost se na stavebníka vztahuje bez ohledu na 
                                    to, zda v souvislosti se stavební činností proběhl záchranný archeologický výzkum.</strong>
                                    """,
                                self.body_style,
                            ),
                            Paragraph(
                                """
                                Ustanovení § 23 odst. 2 a 3 zákona č. 20/1987 Sb., o státní památkové péči, v platném znění, které 
                                ukládá <strong>povinnost učinit oznámení o archeologickém nálezu</strong>, který nebyl učiněn při 
                                provádění archeologických výzkumů, a to Archeologickému ústavu nebo nejbližšímu muzeu buď přímo 
                                nebo prostřednictvím obce, v jejímž územním obvodu k archeologickému nálezu došlo. 
                                <strong>Oznámení o archeologickém nálezu je povinen učinit nálezce nebo osoba odpovědná za 
                                provádění prací, při nichž došlo k archeologickému nálezu, a to nejpozději druhého dne po 
                                archeologickém nálezu nebo potom, kdy se o archeologickém nálezu dověděl. Archeologický nález 
                                i naleziště musí být ponechány beze změny až do prohlídky Archeologickým ústavem nebo muzeem, 
                                nejméně však po dobu pěti pracovních dnů po učiněném oznámení. Tato povinnost se vztahuje ke všem 
                                archeologickým nálezům učiněným mimo archeologický výzkum nebo stavební činnost.</strong>
                                """,
                                self.body_style,
                            ),
                        ],
                        bulletType="a",
                        bulletFormat="%s.",
                    ),
                ],
            ],
            bulletType="1",
            bulletFormat="%s.",
        )

        self._create_signature()

    def build_document(self) -> RepositoryBinaryFile:
        pdf_buffer, my_doc = self._initiate_document()
        styles = self.styles
        body_style = self.body_style

        tbl_data = [
            [
                Paragraph(self.texts.get("header_tab_1_1"), styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(self.texts.get("header_tab_1_2"), styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(self.texts.get("header_tab_1_3"), styles.get("amBodyTextSmallerSpaceAfter")),
            ],
            [
                Paragraph(self.texts.get("header_tab_2_1"), body_style),
                Paragraph(self.texts.get("header_tab_2_2"), body_style),
                Paragraph(self.texts.get("header_tab_2_3"), body_style),
            ],
        ]
        tbl = Table(tbl_data)

        header = [
            Paragraph(self.texts.get("header_line_1"), styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_2"), styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_3"), styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_4"), styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_5"), styles.get("amBodyTextSmallerSpaceAfter")),
            tbl,
        ]

        doc = [
            Paragraph(self.texts.get("doc_vec"), styles["amVec"]),
            Paragraph(self.texts.get("data_part_1"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_2"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_3"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_4"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_5"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_6"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("doc_par_1"), body_style),
            Paragraph(self.texts.get("doc_par_2"), body_style),
            Paragraph(self.texts.get("doc_par_3"), body_style),
            Paragraph(self.texts.get("notes_heading"), body_style),
            self.texts.get("notes", body_style),
        ]

        signature = [
            Paragraph(self.texts.get("doc_sign_1"), styles.get("amSignature")),
            Paragraph(self.texts.get("doc_sign_2"), styles.get("amSignature")),
            Paragraph(self.texts.get("doc_sign_3"), styles.get("amSignature")),
        ]

        document_content = header + doc + signature
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)
