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
        self.texts["header_tab_1_3"] = f"<strong>V {DOK_VE_MESTE[self.dok_index]} dne</strong>"
        self.texts["header_tab_2_1"] = (
            self.projekt.datum_oznameni.strftime("%d. %m. %Y") if self.projekt.datum_oznameni else ""
        )
        self.texts["header_tab_2_2"] = self.projekt.ident_cely
        self.texts["header_tab_2_3"] = datetime.datetime.now().strftime("%d. %m. %Y")

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
        self.texts[
            "data_part_2"
        ] = f"<strong>Katastrální území</strong>: {self.projekt.hlavni_katastr} ({self.projekt.hlavni_katastr.okres})"
        self.texts["data_part_3"] = f"<strong>Lokalizace</strong>: {self.projekt.lokalizace}"
        self.texts["data_part_4"] = f"<strong>Parcelní číslo</strong>: {self.projekt.parcelni_cislo}"
        self.texts["data_part_5"] = f"<strong>Označení stavby</strong>: {self.projekt.oznaceni_stavby}"
        self.texts[
            "data_part_6"
        ] = f"<strong>Plánované zahájení</strong>: {self.projekt.planovane_zahajeni.lower.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''} - {self.projekt.planovane_zahajeni.upper.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.planovane_zahajeni else ''}"

    def _create_signature(self):
        self.texts["doc_sign_1"] = "S pozdravem"
        self.texts["doc_sign_2"] = DOC_REDITEL[self.dok_index]
        self.texts["doc_sign_3"] = f"ředitel<br/>Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i."

    def _create_signature_doc(self):
        return [
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
        self.texts[
            "doc_vec"
        ] = """
        Věc: Potvrzení o splnění oznamovací povinnosti dle § 22, odst. 2 zák. č. 20/1987 Sb., o státní památkové péči,
        v platném znění
        """
        self._create_data_document_part()

        self.texts[
            "doc_par_1"
        ] = f"""
        Archeologický ústav AV ČR, {DOK_MESTO[self.dok_index]}, v. v. i., obdržel dne 
        {self.projekt.datum_oznameni.strftime('%d. %m. %Y').replace(' 0', ' ') if self.projekt.datum_oznameni else ''} 
        Vaše oznámení o zahájení stavebního (či jiného) záměru na území s archeologickými nálezy 
        {self.projekt.podnet} v k. ú. {self.projekt.hlavni_katastr} ({self.projekt.hlavni_katastr.okres}), který 
        eviduje pod evidenčním číslem {self.projekt.ident_cely}. Archeologický ústav AV ČR, 
        {DOK_MESTO[self.dok_index]}, v. v. i. sděluje, že tímto krokem byla splněna zákonná oznamovací povinnost 
        dle ustanovení § 22 odst. 2 zákona č. 20/1987 Sb., o státní památkové péči, ve znění pozdějších předpisů.
        """

        self.texts[
            "doc_par_2"
        ] = """
        Oznamovatel je v návaznosti na oznámení povinen umožnit Archeologickému ústavu nebo oprávněné 
        archeologické organizaci provést na dotčeném území záchranný archeologický výzkum. Informaci o konkrétní 
        organizaci, která má zájem archeologický výzkum provést obdržíte automatickou zprávu. V případě, že záchranný 
        archeologický výzkum nebude třeba provést, obdržíte automatickou zprávu o zrušení projektu.
        """

        self.texts[
            "doc_par_3"
        ] = """
        <strong>Toto potvrzení neslouží jako doklad o provedení záchranného archeologického výzkumu, ani jako 
        doklad pro dodatečné stavební povolení.</strong>
        """

        self._create_signature()

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
                            Výzkum je dle § 22 odst. 1 a odst. 2 zákona č. 20/1987 Sb., o státní památkové péči, 
                            v platném znění, prováděn na základě dohody uzavřené mezi stavebníkem a Archeologickým 
                            ústavem AV ČR nebo oprávněnou organizací. Stavebník má právo uzavřít dohodu s kteroukoliv 
                            organizací, oprávněnou provádět archeologické výzkumy na dotčeném území. Seznam všech 
                            oprávněných organizací s územním rozsahem jejich působnosti naleznete na internetových 
                            stránkách Mapa archeologických organizací (https://oao.aiscr.cz/).
                            """,
                    self.body_style,
                ),
                [
                    Paragraph(
                        f"""
                            <strong>V případě nedohody určí podmínky výzkumu příslušný krajský úřad na základě 
                            § 22 odst. 1 zákona č. 20/1987 Sb., o státní památkové péči, v platném znění.</strong>
                            """,
                        self.body_style,
                    ),
                    Paragraph(
                        f"""
                            Za standardních okolností je záchranný archeologický výzkum prováděn formou dohledu 
                            zemních prací, případně formou plošného terénního výzkumu předstihově nebo souběžně 
                            se stavební činností. Konkrétní podmínky a metodika provedení záchranného archeologického 
                            výzkumu jsou blíže specifikovány v příslušné dohodě, uzavřené mezi stavebníkem 
                            a Archeologickým ústavem AV ČR nebo oprávněnou organizací dle § 22 odst. 1 
                            zákona č. 20/1987 Sb., o státní památkové péči, v platném znění.
                            """,
                        self.body_style,
                    ),
                    Paragraph(
                        f"""
                            Úhrada nákladů záchranného archeologického výzkumu se řídí ustanovením § 22 odst. 
                            2 zákona č. 20/1987 Sb., o státní památkové péči, v platném znění.
                            """,
                        self.body_style,
                    ),
                    Paragraph(
                        f"""
                            <strong>Bez ohledu na to, zda v souvislosti se stavební nebo jinou činností proběhl 
                            záchranný archeologický výzkum</strong>, Archeologický ústav AV ČR, 
                            {DOK_EMAIL[self.dok_index]}, v. v. i., upozorňuje na:
                            """,
                        self.body_style,
                    ),
                    ListFlowable(
                        [
                            Paragraph(
                                """
                                    Ustanovení § 266 zákona č. 283/2021 Sb., stavební zákon, v platném znění, 
                                    které stavebníkovi ukládá <strong>povinnost oznámit stavebnímu úřadu 
                                    nepředvídaný archeologický nebo paleontologický nález nebo nález kulturně 
                                    cenného předmětu, detailu stavby nebo chráněné části přírody.</strong> 
                                    Stavebník je také povinen učinit opatření nezbytná k tomu, aby nález nebyl 
                                    poškozen nebo zničen, práce v místě nálezu přerušit a zaznamenat do 
                                    stavebního deníku čas a okolnosti nálezu, datum oznámení stavebnímu úřadu 
                                    a popis provedených opatření. <strong>Tato povinnost se na stavebníka 
                                    vztahuje bez ohledu na to, zda v souvislosti se stavební činností 
                                    proběhl záchranný archeologický výzkum.</strong>
                                    """,
                                self.body_style,
                            ),
                            Paragraph(
                                """
                                    Ustanovení § 23 odst. 2 a 3 zákona č. 20/1987 Sb., o státní památkové péči, 
                                    v platném znění, které ukládá <strong>povinnost učinit oznámení o archeologickém 
                                    nálezu</strong>, který nebyl učiněn při provádění archeologických výzkumů, 
                                    a to Archeologickému ústavu nebo nejbližšímu muzeu buď přímo nebo 
                                    prostřednictvím obce, v jejímž územním obvodu k archeologickému nálezu došlo. 
                                    <strong>Oznámení o archeologickém nálezu je povinen učinit nálezce nebo osoba 
                                    odpovědná za provádění prací</strong>, při nichž došlo k archeologickému nálezu, 
                                    <strong>a to nejpozději druhého dne po archeologickém nálezu nebo potom, 
                                    kdy se o archeologickém nálezu dověděl. Archeologický nález i naleziště 
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

    def build_document(self) -> RepositoryBinaryFile:
        pdf_buffer, my_doc = self._initiate_document()
        styles = self.styles
        body_style = self.body_style
        header: List[Paragraph] = self._create_header_oznamovatel_doc()
        tbl = self._create_header_tab_dates_doc()
        header: List[Paragraph, Table]
        header.append(tbl)

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
            Paragraph(self.texts.get("doc_par_3"), styles["amBodyTextCenter"]),
        ]

        signature = self._create_signature_doc()

        notes = [
            PageBreak(),
            Paragraph(self.texts.get("notes_heading"), body_style),
            self.texts.get("notes", body_style),
        ]

        document_content = header + doc + signature + notes
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)


class ZruseniPDFCreator(DocumentCreator):
    FILENAME_PREFIX = "zruseni"

    def _generate_text(self):
        self._create_header_oznamovatel()
        self._create_header_tab_dates()
        self.texts["doc_vec"] = "Věc: Zrušení evidence záměru v informačním systému Archeologická mapa České republiky"
        self._create_data_document_part()

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
        header: List[Paragraph] = self._create_header_oznamovatel_doc()
        tbl = self._create_header_tab_dates_doc()
        header: List[Paragraph, Table]
        header.append(tbl)

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

        signature = self._create_signature_doc()

        document_content = header + doc + signature
        return self._generate_repository_file(my_doc, document_content, pdf_buffer)
