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
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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


class DocumentCreator(ABC):
    @abstractmethod
    def _generate_text(self):
        pass

    @abstractmethod
    def build_document(self):
        pass


class OznameniPDFCreator(DocumentCreator):
    def _generate_text(self):
        dok_index = 0 if OBLAST_CECHY in self.projekt.ident_cely.upper() else 1
        self.texts["header_line_1"] = f"ARCHEOLOGICKÝ ÚSTAV AV ČR, {DOK_MESTO[dok_index]}, v. v. i."
        self.texts["header_line_2"] = "REFERÁT ARCHEOLOGICKÉ PAMÁTKOVÉ PÉČE"
        # Condition check for automated testing
        if self.projekt.hlavni_katastr:
            kraj: RuianKraj = self.projekt.hlavni_katastr.okres.kraj
        else:
            kraj: RuianKraj = RuianKraj.objects.first()
        telefon = DOK_TELEFON.get(kraj.kod, DOK_TELEFON.get(0))
        self.texts["header_line_3"] = f"{DOK_ADRESA[dok_index]}<br/>{telefon}<br/>e-mail: {DOK_EMAIL[dok_index]}"
        self.texts[
            "header_line_4"
        ] = f"{DOK_VE_MESTE[dok_index]} {datetime.datetime.today().date().strftime('%d. %m. %Y').replace(' 0', ' ')}"

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
        {self.projekt.parcelni_cislo} ({self.projekt.lokalizace}) {DOC_KOMU[dok_index]}. \n\
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

        self.texts["doc_sign_1"] = "S pozdravem"
        self.texts["doc_sign_2"] = DOC_REDITEL[dok_index]
        self.texts["doc_sign_3"] = f"ředitel<br/>Archeologický ústav AV ČR, {DOK_MESTO[dok_index]}, v. v. i."

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

    def build_document(self) -> RepositoryBinaryFile:
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

        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN + HEADER_HEIGHT,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        styles = self.styles
        body_style = styles["amBodyText"]
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
        my_doc.build(header + page_1 + attachment, onFirstPage=draw_header, onLaterPages=draw_header)
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()

        postfix = "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        file = io.BytesIO()
        file.write(pdf_value)
        file.seek(0)
        filename = f"oznameni_{self.projekt.ident_cely}{postfix}.pdf"

        con = FedoraRepositoryConnector(self.projekt, self.fedora_transaction)
        rep_bin_file: RepositoryBinaryFile = con.save_binary_file(filename, "application/pdf", file)
        return rep_bin_file

    def __init__(self, oznamovatel, projekt, fedora_transaction, additional=False):
        from oznameni.models import Oznamovatel

        self.oznamovatel: Oznamovatel = oznamovatel
        from projekt.models import Projekt

        self.projekt: Projekt = projekt
        self.fedora_transaction = fedora_transaction
        self.additional = additional
        self.styles = getSampleStyleSheet()
        self._create_style_dict()
        self.texts = {}
        self._generate_text()
