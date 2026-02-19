# flake8: noqa: E221, E222, W291, F541

import datetime
import io
import logging
import os
from abc import ABC, abstractmethod
from io import BytesIO
from typing import List

from core.constants import DOC_REDITEL, DOK_EMAIL, DOK_MESTO, DOK_VE_MESTE, OBLAST_CECHY
from core.repository_connector import FedoraRepositoryConnector, RepositoryBinaryFile
from reportlab.lib import utils
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ListStyle, ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, PageBreak, Paragraph, SimpleDocTemplate, Table

from webclient.settings.base import STATIC_ROOT

logger = logging.getLogger(__name__)

PAGESIZE = (210 * mm, 297 * mm)
BASE_MARGIN = 20 * mm
HEADER_HEIGHT = 10 * mm
HEADER_IMAGES = ("logo-arup-cs.png", "logo-arub-cs.png", "logo-am-colored-cs.png")

# Ošetření výjimky kvůli selhávajícímu běhu sphinx-build.

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
    # Toto se spustí během `collectstatic`.
    logger.error("doc_utils.font.error", extra={"info": path})

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

    @classmethod
    def format_date(cls, date_obj: datetime.datetime | None) -> str:
        if date_obj is None:
            return ""
        if os.name == "nt":
            return date_obj.strftime("%#d. %#m. %Y")
        else:
            return date_obj.strftime("%-d. %-m. %Y")

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

    def _create_header_oznamovatel(self):
        self.texts["header_line_1"] = self.projekt.oznamovatel.oznamovatel
        self.texts["header_line_2"] = f"Zast.: {self.projekt.oznamovatel.odpovedna_osoba}"
        self.texts["header_line_3"] = self.projekt.oznamovatel.adresa
        self.texts["header_line_4"] = f"Email: {self.projekt.oznamovatel.email}"
        self.texts["header_line_5"] = f"Tel.: {self.projekt.oznamovatel.telefon}"

    def _create_header_oznamovatel_doc(self) -> List[Paragraph]:
        return [
            Paragraph(self.texts.get("header_line_1"), self.styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_2"), self.styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_3"), self.styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_4"), self.styles.get("amBodyTextSmallerSpaceAfter")),
            Paragraph(self.texts.get("header_line_5"), self.styles.get("amBodyTextSmallerSpaceAfter")),
        ]

    def _create_header_tab_dates(self):
        self.texts["header_tab_1_1"] = "<strong>Oznámení ze dne</strong>"
        self.texts["header_tab_1_2"] = "<strong>Evidenční číslo</strong>"
        self.texts["header_tab_1_3"] = f"<strong>{DOK_VE_MESTE[self.dok_index]} dne</strong>"
        self.texts["header_tab_2_1"] = self.format_date(self.projekt.datum_oznameni)
        self.texts["header_tab_2_2"] = self.projekt.ident_cely
        self.texts["header_tab_2_3"] = self.format_date(datetime.datetime.now())

    def _create_header_tab_dates_doc(self) -> Table:
        tbl_data = [
            [
                Paragraph(self.texts.get("header_tab_1_1"), self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(self.texts.get("header_tab_1_2"), self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(self.texts.get("header_tab_1_3"), self.styles.get("amBodyTextSmallerSpaceAfter")),
            ],
            [
                Paragraph(self.texts.get("header_tab_2_1"), self.body_style),
                Paragraph(self.texts.get("header_tab_2_2"), self.body_style),
                Paragraph(self.texts.get("header_tab_2_3"), self.body_style),
            ],
        ]
        tbl = Table(tbl_data)
        return tbl

    def _create_data_document_part(self):
        self.texts["data_part_1"] = f"<strong>Podnět oznámení</strong>: {self.projekt.podnet}"
        self.texts["data_part_2"] = f"<strong>Katastrální území</strong>: {self.projekt.hlavni_katastr}"
        self.texts["data_part_3"] = f"<strong>Lokalizace</strong>: {self.projekt.lokalizace}"
        self.texts["data_part_4"] = f"<strong>Parcelní číslo</strong>: {self.projekt.parcelni_cislo}"
        self.texts["data_part_5"] = f"<strong>Označení stavby</strong>: {self.projekt.oznaceni_stavby}"
        self.texts["data_part_6"] = (
            f"<strong>Plánované zahájení</strong>: {self.format_date(self.projekt.planovane_zahajeni.lower) if self.projekt.planovane_zahajeni else ''} - {self.format_date(self.projekt.planovane_zahajeni.upper) if self.projekt.planovane_zahajeni else ''}"
        )

    def _create_signature(self):
        self.texts["doc_sign_1"] = "S pozdravem"
        self.texts["doc_sign_2"] = DOC_REDITEL[self.dok_index]
        self.texts["doc_sign_3"] = (
            f"ředitel<br/>Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i."
        )

    def _create_signature_doc(self):
        return [
            Paragraph("", self.body_style),
            Paragraph(self.texts.get("doc_sign_1"), self.styles.get("amSignature")),
            Paragraph(self.texts.get("doc_sign_2"), self.styles.get("amSignature")),
            Paragraph(self.texts.get("doc_sign_3"), self.styles.get("amSignature")),
        ]

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
        self._create_header_oznamovatel()
        self._create_header_tab_dates()
        self.texts["doc_vec"] = """
        Věc: Potvrzení o&nbsp;splnění oznamovací povinnosti dle §&nbsp;22, odst.&nbsp;2 zák.&nbsp;č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči,
        v&nbsp;platném znění
        """
        self._create_data_document_part()

        self.texts["doc_par_1"] = f"""
        Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i., obdržel dne 
        {self.format_date(self.projekt.datum_oznameni)} 
        Vaše oznámení o&nbsp;zahájení stavebního (či jiného) záměru na území s&nbsp;archeologickými nálezy 
        {self.projekt.podnet} v&nbsp;k.&nbsp;ú.&nbsp;{self.projekt.hlavni_katastr}, který 
        eviduje pod evidenčním číslem {self.projekt.ident_cely}. Archeologický ústav AV ČR, 
        {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i. sděluje, že tímto krokem byla splněna zákonná oznamovací povinnost 
        dle ustanovení §&nbsp;22 odst.&nbsp;2 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, ve znění pozdějších předpisů.
        """

        self.texts["doc_par_2"] = """
        Oznamovatel je v&nbsp;návaznosti na oznámení povinen umožnit Archeologickému ústavu nebo oprávněné 
        archeologické organizaci provést na dotčeném území záchranný archeologický výzkum. Informaci o&nbsp;konkrétní 
        organizaci, která má zájem archeologický výzkum provést obdržíte automatickou zprávu. V&nbsp;případě, že záchranný 
        archeologický výzkum nebude třeba provést, obdržíte automatickou zprávu o&nbsp;zrušení projektu.
        """

        self.texts["doc_par_3"] = """
        <strong>Toto potvrzení neslouží jako doklad o&nbsp;provedení záchranného archeologického výzkumu, ani jako 
        doklad pro dodatečné stavební povolení.</strong>
        """

        self.texts["notes_heading"] = "<strong>Poučení</strong>"
        self.texts["notes"] = ListFlowable(
            [
                Paragraph(
                    f"""
                            V&nbsp;případě dotazů se můžete na Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i., obracet 
                            skrze emailovou adresu {DOK_EMAIL[self.dok_index]}.
                            """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                            Výzkum je dle §&nbsp;22 odst.&nbsp;1 a&nbsp;odst.&nbsp;2 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, 
                            v&nbsp;platném znění, prováděn na základě dohody uzavřené mezi stavebníkem a&nbsp;Archeologickým 
                            ústavem AV ČR nebo oprávněnou organizací. Stavebník má právo uzavřít dohodu s&nbsp;kteroukoliv 
                            organizací, oprávněnou provádět archeologické výzkumy na dotčeném území. Seznam všech 
                            oprávněných organizací s&nbsp;územním rozsahem jejich působnosti naleznete na internetových 
                            stránkách Mapa archeologických organizací 
                            (<a href="https://oao.aiscr.cz/">https://oao.aiscr.cz/</a>).
                            """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                        <strong>V&nbsp;případě nedohody určí podmínky výzkumu příslušný krajský úřad na základě 
                        §&nbsp;22 odst.&nbsp;1 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, v&nbsp;platném znění.</strong>
                        """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                        Za standardních okolností je záchranný archeologický výzkum prováděn formou dohledu 
                        zemních prací, případně formou plošného terénního výzkumu předstihově nebo souběžně 
                        se stavební činností. Konkrétní podmínky a&nbsp;metodika provedení záchranného archeologického 
                        výzkumu jsou blíže specifikovány v&nbsp;příslušné dohodě, uzavřené mezi stavebníkem 
                        a&nbsp;Archeologickým ústavem AV ČR nebo oprávněnou organizací dle §&nbsp;22 odst.&nbsp;1 
                        zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, v&nbsp;platném znění.
                        """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                        Úhrada nákladů záchranného archeologického výzkumu se řídí ustanovením §&nbsp;22 odst.&nbsp;2 
                        zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, v&nbsp;platném znění.
                        """,
                    self.body_style,
                ),
                [
                    Paragraph(
                        f"""
                            <strong>Bez ohledu na to, zda v&nbsp;souvislosti se stavební nebo jinou činností proběhl 
                            záchranný archeologický výzkum</strong>, Archeologický ústav AV ČR, 
                            {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i. upozorňuje na:
                            """,
                        self.body_style,
                    ),
                    ListFlowable(
                        [
                            Paragraph(
                                """
                                    Ustanovení §&nbsp;266 zákona č.&nbsp;283/2021 Sb., stavební zákon, v&nbsp;platném znění, 
                                    které stavebníkovi ukládá <strong>povinnost oznámit stavebnímu úřadu 
                                    nepředvídaný archeologický nebo paleontologický nález nebo nález kulturně 
                                    cenného předmětu, detailu stavby nebo chráněné části přírody.</strong> 
                                    Stavebník je také povinen učinit opatření nezbytná k&nbsp;tomu, aby nález nebyl 
                                    poškozen nebo zničen, práce v&nbsp;místě nálezu přerušit a&nbsp;zaznamenat do 
                                    stavebního deníku čas a&nbsp;okolnosti nálezu, datum oznámení stavebnímu úřadu 
                                    a&nbsp;popis provedených opatření. <strong>Tato povinnost se na stavebníka 
                                    vztahuje bez ohledu na to, zda v&nbsp;souvislosti se stavební činností 
                                    proběhl záchranný archeologický výzkum.</strong>
                                    """,
                                self.body_style,
                            ),
                            Paragraph(
                                """
                                    Ustanovení §&nbsp;23 odst.&nbsp;2 a&nbsp;3 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, 
                                    v&nbsp;platném znění, které ukládá <strong>povinnost učinit oznámení o&nbsp;archeologickém 
                                    nálezu</strong>, který nebyl učiněn při provádění archeologických výzkumů, 
                                    a&nbsp;to Archeologickému ústavu nebo nejbližšímu muzeu buď přímo nebo 
                                    prostřednictvím obce, v&nbsp;jejímž územním obvodu k&nbsp;archeologickému nálezu došlo. 
                                    <strong>Oznámení o&nbsp;archeologickém nálezu je povinen učinit nálezce nebo osoba 
                                    odpovědná za provádění prací</strong>, při nichž došlo k&nbsp;archeologickému nálezu, 
                                    <strong>a&nbsp;to nejpozději druhého dne po archeologickém nálezu nebo potom, 
                                    kdy se o&nbsp;archeologickém nálezu dověděl. Archeologický nález i&nbsp;naleziště 
                                    musí být ponechány beze změny až do prohlídky Archeologickým ústavem nebo muzeem, 
                                    nejméně však po dobu pěti pracovních dnů</strong> po učiněném oznámení. 
                                    <strong>Tato povinnost se vztahuje ke všem archeologickým nálezům učiněným 
                                    mimo archeologický výzkum nebo stavební činnost.</strong>
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

        self.texts["doc_attachment_heading_main_1"] = "PŘÍLOHA – INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ"

        self.texts["doc_attachment_heading_main_2"] = "POUČENÍ O PRÁVECH V SOUVISLOSTI S OCHRANOU OSOBNÍCH ÚDAJŮ"

        self.texts["doc_attachment_heading_1"] = "<u>ÚVODNÍ INFORMACE</u>"

        self.texts["doc_attachment_par_1"] = """
               Prosím, věnujte pozornost následujícímu dokumentu, jehož prostřednictvím Vám poskytujeme informace
               o&nbsp;zpracování Vašich osobních údajů a&nbsp;o&nbsp;právech souvisejících s&nbsp;Vaší povinností jako stavebníka dle
               §&nbsp;22 odst.&nbsp;2 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči (dále rovněž jen „zákon“), poskytnout informace
               o&nbsp;záměru provádět stavební činnost na území s&nbsp;archeologickými nálezy nebo jinou činnost, kterou by m
               ohlo být ohroženo provádění archeologických výzkumů, a&nbsp;to buď <strong>Archeologickému ústavu AV ČR, Praha,
               v.&nbsp;v.&nbsp;i., IČ 67985912, se sídlem Letenská 4, 118 01 Praha 1,</strong> nebo <strong>Archeologickému ústavu
               AV ČR, Brno, v.&nbsp;v.&nbsp;i., IČ 68081758, se sídlem Čechyňská 363/19, 602 00 Brno,</strong> jako oprávněným institucím
               dle daného ustanovení zákona. Jakékoliv nakládání s&nbsp;osobními údaji se řídí platnými právními předpisy,
               zejména zákonem o&nbsp;ochraně osobních údajů a&nbsp;nařízením Evropského parlamentu a&nbsp;Rady č.&nbsp;2016/679
               ze dne 27. 4. 2016 o&nbsp;ochraně fyzických osob v&nbsp;souvislosti se zpracováním osobních údajů a&nbsp;o&nbsp;volném pohybu
               těchto údajů a&nbsp;o&nbsp;zrušení směrnice 95/46/ES (dále jen „obecné nařízení o&nbsp;ochraně osobních údajů“). V&nbsp;souladu
               s&nbsp;ustanovením čl.&nbsp;13 a&nbsp;následujícího obecného nařízení o&nbsp;ochraně osobních údajů Vám jako tzv. subjektům
               údajů poskytujeme následující informace. Tento dokument je veřejný a&nbsp;slouží k&nbsp;Vašemu řádnému informování
               o&nbsp;rozsahu, účelu, době zpracování osobních údajů a&nbsp;k&nbsp;poučení o&nbsp;Vašich právech v&nbsp;souvislosti
               s&nbsp;jejich ochranou.
               """

        self.texts["doc_attachment_heading_2"] = """
               <u>KDO JE SPRÁVCEM OSOBNÍCH ÚDAJŮ?</u>
               """

        self.texts["doc_attachment_par_2"] = """
               Společnými správci osobních údajů jsou Archeologický ústav AV ČR, Praha, v.&nbsp;v.&nbsp;i., IČ:67985912,
               se sídlem Letenská 4, 118 01 Praha 1, a&nbsp;Archeologický ústav AV ČR, Brno, v.&nbsp;v.&nbsp;i., IČ:68081758,
               se sídlem Čechyňská 363/19, 602 00 Brno (dále jen <strong>„Správce“</strong> či <strong>„Archeologický ústav“</strong>).
               """

        self.texts["doc_attachment_heading_3"] = """
               <u>OBECNĚ - CO VŠE PATŘÍ MEZI OSOBNÍ ÚDAJE?</u>
               """

        self.texts["doc_attachment_par_3"] = """
               Osobními údaji jsou veškeré informace vztahující se k&nbsp;identifikované či identifikovatelné fyzické osobě
               (člověku), na základě kterých lze konkrétní fyzickou osobu přímo či nepřímo identifikovat. Mezi osobní údaje
               tak patří široká škála informací, jako je například jméno, pohlaví, věk a&nbsp;datum narození, osobní stav,
               fotografie (resp. jakékoliv zobrazení podoby), rodné číslo, místo trvalého pobytu, telefonní číslo, e-mail,
               údaje o&nbsp;zdravotní pojišťovně, státní občanství, údaje o&nbsp;zdravotním stavu (fyzickém i&nbsp;psychickém),
               ale také otisk prstu, podpis nebo IP adresa.
               """

        self.texts["doc_attachment_heading_4"] = """
               <u>ZA JAKÝM ÚČELEM A NA JAKÉM ZÁKLADĚ ZPRACOVÁVÁME VAŠE OSOBNÍ ÚDAJE?</u>
               """

        self.texts["doc_attachment_par_4"] = """
               Vaše osobní údaje zpracováváme, jelikož nám to ukládá zákon, konkrétně §&nbsp;22 odst.&nbsp;2 zákona č.&nbsp;20/1987 Sb.,
               o&nbsp;státní památkové péči, který stanoví stavebníkovi, který má záměr provádět stavební činnost v&nbsp;území
               s&nbsp;archeologickými nálezy, nebo jinou činnost, kterou by mohlo být ohroženo provádění archeologických
               výzkumů, povinnost oznámit nejprve tento záměr Archeologickému ústavu. Odrazem této povinnosti stavebníka je
               povinnost archeologického ústavu toto oznámení přijmout a&nbsp;zpracovat jej. Při zpracování oznámení stavebníka
               dochází ze strany Archeologického ústavu ke zpracování osobních údajů stavebníka jako subjektu osobních údajů
               dle čl.&nbsp;6 odst.&nbsp;1 písm.&nbsp;c), e) obecného nařízení o&nbsp;ochraně osobních údajů a&nbsp;Archeologický ústav je
               v&nbsp;postavení Správce. Vaše osobní údaje v&nbsp;níže uvedeném rozsahu zpracováváme, pouze aby Vás
               Archeologický ústav či jiná oprávněná organizace dle zákona mohly kontaktovat za účelem provedení
               záchranného archeologického průzkumu."""

        self.texts["doc_attachment_heading_5"] = """
               <u>ROZSAH OSOBNÍCH ÚDAJŮ ZPRACOVÁVANÝCH SPRÁVCEM</u>
               """

        self.texts["doc_attachment_par_5"] = """
               Informujeme Vás, že Vaše osobní údaje jsou zpracovávány v&nbsp;rozsahu Vámi vyplněného formuláře,
               a&nbsp;to konkrétně v&nbsp;rozsahu:"""

        self.texts["doc_attachment_par_5_bullets"] = ListFlowable(
            [
                Paragraph("jméno", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("příjmení", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("adresa", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("telefonní číslo", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph("e-mail", self.styles.get("amBodyTextSmallerSpaceAfter")),
                Paragraph(
                    "údaje o&nbsp;nemovité věci (parcelní číslo a&nbsp;bližší specifikace předmětu oznámení).",
                    self.styles.get("amBodyTextSmallerSpaceAfter"),
                ),
            ],
            bulletType="bullet",
        )

        self.texts["doc_attachment_heading_6"] = """
               <u>DOBA ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
               """

        self.texts["doc_attachment_par_6"] = """
               Vaše osobní údaje budeme ukládat po dobu nezbytně nutnou maximálně však po dobu deseti let. Tyto lhůty
               vyplývají ze zákonných požadavků a&nbsp;z&nbsp;titulu ochrany zájmu subjektu údajů na prokázání
               splnění své zákonné povinnosti.
               """

        self.texts["doc_attachment_heading_7"] = """
               <u>DALŠÍ INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
               """

        self.texts["doc_attachment_par_7_part_1"] = """
               Osobní údaje subjektu údajů jsou zpracovávány automatizovaně v&nbsp;elektronické formě.
               Příjemci Vašich osobních údajů, resp. výsledků jejich zpracování jsou:
               """

        self.texts["doc_attachment_par_7_bullets"] = ListFlowable(
            [
                Paragraph("oprávněné organizace dle zákona", self.styles.get("amBodyTextSmallerSpaceAfter")),
            ],
            bulletType="bullet",
        )

        self.texts["doc_attachment_par_7_part_2"] = """
               Vaše osobní údaje nepředáváme a&nbsp;nemáme v&nbsp;úmyslu předat do třetí země nebo mezinárodní organizaci.
               """

        self.texts["doc_attachment_heading_8"] = """
               <u>POUČENÍ O PRÁVECH SUBJEKTŮ ÚDAJŮ</u>
               """

        self.texts["doc_attachment_par_8_1"] = """
               Subjekt údajů má právo požádat Správce o&nbsp;poskytnutí informace o&nbsp;zpracování jeho osobních údajů.
               """

        self.texts["doc_attachment_par_8_2"] = """
               Subjekt údajů má právo, aby Správce bez zbytečného odkladu opravil nepřesné osobní údaje, které se ho týkají.
               S&nbsp;přihlédnutím k&nbsp;účelům zpracování má subjekt údajů právo na doplnění neúplných osobních údajů, a&nbsp;to
               i&nbsp;poskytnutím dodatečného prohlášení.
               Subjekt údajů má právo, aby Správce bez zbytečného odkladu vymazal osobní údaje, které se daného subjektu
               údajů týkají, a&nbsp;Správce má povinnost osobní údaje bez zbytečného odkladu vymazat, pokud je dán některý z&nbsp;důvodů
               stanovených obecným nařízením o&nbsp;ochraně osobních údajů.
               """

        self.texts["doc_attachment_par_8_3"] = """
               Subjekt údajů má právo, aby Správce omezil zpracování osobních údajů, v&nbsp;případech stanovených obecným
               nařízením o&nbsp;ochraně osobních údajů.
               """

        self.texts["doc_attachment_par_8_4"] = """
               Pokud se subjekt údajů domnívá, že došlo k&nbsp;porušení právních předpisů v&nbsp;souvislosti s&nbsp;ochranou jeho osobních
               údajů, má právo podat stížnost u&nbsp;dozorového úřadu. Dozorovým úřadem je v&nbsp;České republice
               Úřad pro ochranu osobních údajů.
               """

    def build_document(self) -> RepositoryBinaryFile:
        pdf_buffer, my_doc = self._initiate_document()
        styles = self.styles
        body_style = self.body_style
        header: List[Paragraph] = self._create_header_oznamovatel_doc()
        tbl = self._create_header_tab_dates_doc()
        header: List[Paragraph, Table]
        header.append(Paragraph("", body_style))
        header.append(tbl)

        doc = [
            Paragraph("", body_style),
            Paragraph(self.texts.get("doc_vec"), styles["amVec"]),
            Paragraph("", body_style),
            Paragraph(self.texts.get("data_part_1"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_2"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_3"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_4"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_5"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_6"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph("", body_style),
            Paragraph(self.texts.get("doc_par_1"), body_style),
            Paragraph(self.texts.get("doc_par_2"), body_style),
            Paragraph(self.texts.get("doc_par_3"), styles["amBodyTextCenter"]),
            Paragraph("", body_style),
            Paragraph(self.texts.get("notes_heading"), body_style),
            self.texts.get("notes", body_style),
        ]

        signature = self._create_signature_doc()

        attachment = [
            PageBreak(),
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

        document_content = header + doc + signature + attachment
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)


class ZruseniPDFCreator(DocumentCreator):
    FILENAME_PREFIX = "zruseni"

    def _generate_text(self):
        self._create_header_oznamovatel()
        self._create_header_tab_dates()
        self.texts["doc_vec"] = (
            "Věc: Zrušení evidence záměru v&nbsp;informačním systému Archeologická mapa České republiky"
        )
        self._create_data_document_part()

        self.texts["doc_par_1"] = f"""
        Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i., obdržel dne 
        {self.format_date(self.projekt.datum_oznameni)} 
        Vaše oznámení o&nbsp;zahájení stavebního (či jiného) záměru na území s&nbsp;archeologickými nálezy 
        {self.projekt.podnet} v&nbsp;k.&nbsp;ú.&nbsp;{self.projekt.hlavni_katastr}, který 
        eviduje pod evidenčním číslem {self.projekt.ident_cely}. 
        """

        self.texts["doc_par_2"] = f"""
        Ve věci uvedeného záměru si Vám dovolujeme sdělit, že předmětný projekt byl zrušen z&nbsp;následujícího důvodu:
        """

        self.texts["doc_par_3"] = f"<strong>{self.projekt.historie.historie_set.last().poznamka}</strong>"

        self.texts["notes_heading"] = "<strong>Poučení</strong>"
        self.texts["notes"] = ListFlowable(
            [
                Paragraph(
                    f"""
                    V&nbsp;případě dotazů se můžete na Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i., obracet 
                    skrze emailovou adresu {DOK_EMAIL[self.dok_index]}.
                    """,
                    self.body_style,
                ),
                Paragraph(
                    f"""
                    Jelikož nedošlo k&nbsp;provedení záchranného archeologického výzkumu, nelze po Archeologickém ústavu či jiné 
                    oprávněné organizaci, požadovat vydání potvrzení o&nbsp;jeho provedení pro potřeby správního řízení.
                    """,
                    self.body_style,
                ),
                [
                    Paragraph(
                        f"""
                    <strong>Bez ohledu na to, zda v&nbsp;souvislosti se stavební nebo jinou činností proběhl záchranný 
                    archeologický výzkum</strong>, Archeologický ústav AV ČR, 
                    {DOK_MESTO[self.dok_index]}, v.&nbsp;v.&nbsp;i., upozorňuje na:
                    """,
                        self.body_style,
                    ),
                    ListFlowable(
                        [
                            Paragraph(
                                """
                                    Ustanovení §&nbsp;266 zákona č.&nbsp;283/2021 Sb., stavební zákon, v&nbsp;platném znění, které stavebníkovi ukládá 
                                    <strong>povinnost oznámit stavebnímu úřadu nepředvídaný archeologický nebo paleontologický nález nebo 
                                    nález kulturně cenného předmětu, detailu stavby nebo chráněné části přírody</strong>. Stavebník je 
                                    také povinen učinit opatření nezbytná k&nbsp;tomu, aby nález nebyl poškozen nebo zničen, práce v&nbsp;místě 
                                    nálezu přerušit a&nbsp;zaznamenat do stavebního deníku čas a&nbsp;okolnosti nálezu, datum oznámení stavebnímu 
                                    úřadu a&nbsp;popis provedených opatření. <strong>Tato povinnost se na stavebníka vztahuje bez ohledu na 
                                    to, zda v&nbsp;souvislosti se stavební činností proběhl záchranný archeologický výzkum.</strong>
                                    """,
                                self.body_style,
                            ),
                            Paragraph(
                                """
                                Ustanovení §&nbsp;23 odst.&nbsp;2 a&nbsp;3 zákona č.&nbsp;20/1987 Sb., o&nbsp;státní památkové péči, v&nbsp;platném znění, které 
                                ukládá <strong>povinnost učinit oznámení o&nbsp;archeologickém nálezu</strong>, který nebyl učiněn při 
                                provádění archeologických výzkumů, a&nbsp;to Archeologickému ústavu nebo nejbližšímu muzeu buď přímo 
                                nebo prostřednictvím obce, v&nbsp;jejímž územním obvodu k&nbsp;archeologickému nálezu došlo. 
                                <strong>Oznámení o&nbsp;archeologickém nálezu je povinen učinit nálezce nebo osoba odpovědná za 
                                provádění prací, při nichž došlo k&nbsp;archeologickému nálezu, a&nbsp;to nejpozději druhého dne po 
                                archeologickém nálezu nebo potom, kdy se o&nbsp;archeologickém nálezu dověděl. Archeologický nález 
                                i&nbsp;naleziště musí být ponechány beze změny až do prohlídky Archeologickým ústavem nebo muzeem, 
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
        header: List[Paragraph] = self._create_header_oznamovatel_doc()
        tbl = self._create_header_tab_dates_doc()
        header: List[Paragraph, Table]
        header.append(Paragraph("", body_style))
        header.append(tbl)

        doc = [
            Paragraph("", body_style),
            Paragraph(self.texts.get("doc_vec"), styles["amVec"]),
            Paragraph("", body_style),
            Paragraph(self.texts.get("data_part_1"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_2"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_3"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_4"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_5"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph(self.texts.get("data_part_6"), styles["amBodyTextSmallerSpaceAfter"]),
            Paragraph("", body_style),
            Paragraph(self.texts.get("doc_par_1"), body_style),
            Paragraph(self.texts.get("doc_par_2"), body_style),
            Paragraph(self.texts.get("doc_par_3"), body_style),
            Paragraph("", body_style),
            Paragraph(self.texts.get("notes_heading"), body_style),
            self.texts.get("notes", body_style),
        ]

        signature = self._create_signature_doc()

        document_content = header + doc + signature
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)
