from io import BytesIO

from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

PAGESIZE = (210 * mm, 297 * mm)
BASE_MARGIN = 20 * mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import (ParagraphStyle, getSampleStyleSheet)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

pdfmetrics.registerFont(TTFont('OpenSans', 'OpenSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('OpenSansBold', 'OpenSans-Bold.ttf'))

header_line_1 = "ARCHEOLOGICKÝ ÚSTAV AV ČR, {#MESTO}, v. v. i."
header_line_2 = "REFERÁT ARCHEOLOGICKÉ PAMÁTKOVÉ PÉČE"
header_line_3 = "{#ADRESA}<br/>{#TELEFON}{#FAX}<br/>e-mail: {#EMAIL}"
header_line_4 = "V {#V_MESTE} {#DNESNI_DATUM}"

doc_vec = """
Věc: Potvrzení o splnění oznamovací povinnosti dle § 22, odst. 2 zák. č. 20/1987
"""

doc_par_1 = """
Potvrzujeme, že {OZNAMOVATEL} ({ADRESA}; tel: {TELEFON}; email: {EMAIL}), jehož zastupuje {ODPOVEDNA_OSOBA}, ohlásil záměr {PODNET} (označení stavby: {OZNACENI_STAVBY}; plánované zahájení: {PLANOVANE_ZAHAJENI}) na k. ú. {KATASTR} (okr. {OKRES}), parc. č. {PARCELNI_CISLO} ({LOKALITA}) {#KOMU}. Oznámení provedl {DATUM_OZNAMENI} pod evidenčním číslem {IDENT_CELY}. Tímto byla naplněna povinnost oznámit zamýšlenou stavební nebo jinou činnost Archeologickému ústavu podle ustanovení § 22, odst. 2, zákona č. 20/1987 Sb. Po schválení a registraci oznámení konkrétní organizací oprávněnou provádět archeologické výzkumy Vás budeme informovat.
"""

doc_par_2 = """TENTO DOKUMENT NESLOUŽÍ JAKO POTVRZENÍ O PROVEDENÍ ARCHEOLOGICKÉHO VÝZKUMU PRO STAVEBNÍ ČI JINÉ ŘÍZENÍ."""

doc_par_3 = """
Oznamovatel je v návaznosti na oznámení povinen umožnit Archeologickému ústavu nebo oprávněné organizaci provést na dotčeném území záchranný archeologický výzkum. O tomto mu bude potvrzení vystaveno samostatně, a to organizací, která výzkum realizovala.
"""

doc_sign_1 = "S pozdravem"
doc_sign_2 = "{#REDITEL}"
doc_sign_3 = "ředitel<br/>Archeologický ústav AV ČR, {#MESTO}, v. v. i."

doc_attachment_heading_main_1 = "PŘÍLOHA – INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ"

doc_attachment_heading_main_2 = "POUČENÍ O PRÁVECH V SOUVISLOSTI S OCHRANOU OSOBNÍCH ÚDAJŮ"

doc_attachment_heading_1 = "<u>ÚVODNÍ INFORMACE</u>"

doc_attachment_par_1 = """
Prosím, věnujte pozornost následujícímu dokumentu, jehož prostřednictvím Vám poskytujeme informace o zpracování Vašich osobních údajů a o právech souvisejících s Vaší povinností jako stavebníka dle § 22 odst. 2 zákona č. 20/1987 Sb., o státní památkové péči (dále rovněž jen „zákon“), poskytnout informace o záměru provádět stavební činnost na území s archeologickými nálezy nebo jinou činnost, kterou by mohlo být ohroženo provádění archeologických výzkumů, a to buď Archeologickému ústavu AV ČR, Praha, v. v. i., IČ 67985912, se sídlem Letenská 4, 118 01 Praha 1, nebo Archeologickému ústavu AV ČR, Brno, v. v. i., IČ 68081758, se sídlem Čechyňská 363/19, 602 00 Brno, jako oprávněným institucím dle daného ustanovení zákona. Jakékoliv nakládání s osobními údaji se řídí platnými právními předpisy, zejména zákonem o ochraně osobních údajů a nařízením Evropského parlamentu a Rady č. 2016/679 ze dne 27. 4. 2016 o ochraně fyzických osob v souvislosti se zpracováním osobních údajů a o volném pohybu těchto údajů a o zrušení směrnice 95/46/ES (dále jen „obecné nařízení o ochraně osobních údajů“). V souladu s ustanovením čl. 13 a následujícího obecného nařízení o ochraně osobních údajů Vám jako tzv. subjektům údajů poskytujeme následující informace. Tento dokument je veřejný a slouží k Vašemu řádnému informování o rozsahu, účelu, době zpracování osobních údajů a k poučení o Vašich právech v souvislosti s jejich ochranou.
"""

doc_attachment_heading_2 = """
<u>KDO JE SPRÁVCEM OSOBNÍCH ÚDAJŮ?</u>
"""

doc_attachment_par_2 = """
Společnými správci osobních údajů jsou Archeologický ústav AV ČR, Praha, v. v. i., IČ:67985912, se sídlem Letenská 4, 118 01 Praha 1, a Archeologický ústav AV ČR, Brno, v. v. i., IČ:68081758, se sídlem Čechyňská 363/19, 602 00 Brno (dále jen „Správce“ či „Archeologický ústav“).
"""

doc_attachment_heading_3 = """
<u>OBECNĚ - CO VŠE PATŘÍ MEZI OSOBNÍ ÚDAJE?</u>
"""

doc_attachment_par_3 = """
Osobními údaji jsou veškeré informace vztahující se k identifikované či identifikovatelné fyzické osobě (člověku), na základě kterých lze konkrétní fyzickou osobu přímo či nepřímo identifikovat. Mezi osobní údaje tak patří široká škála informací, jako je například jméno, pohlaví, věk a datum narození, osobní stav, fotografie (resp. jakékoliv zobrazení podoby), rodné číslo, místo trvalého pobytu, telefonní číslo, e-mail, údaje o zdravotní pojišťovně, státní občanství, údaje o zdravotním stavu (fyzickém i psychickém), ale také otisk prstu, podpis nebo IP adresa.
"""

doc_attachment_heading_4 = """
<u>ZA JAKÝM ÚČELEM A NA JAKÉM ZÁKLADĚ ZPRACOVÁVÁME VAŠE OSOBNÍ ÚDAJE?</u>
"""

doc_attachment_par_4 = """
Vaše osobní údaje zpracováváme, jelikož nám to ukládá zákon, konkrétně § 22 odst. 2 zákona č. 20/1987 Sb., o státní památkové péči, který stanoví stavebníkovi, který má záměr provádět stavební činnost v území s archeologickými nálezy, nebo jinou činnost, kterou by mohlo být ohroženo provádění archeologických výzkumů, povinnost oznámit nejprve tento záměr Archeologickému ústavu. Odrazem této povinnosti stavebníka je povinnost archeologického ústavu toto oznámení přijmout a zpracovat jej. Při zpracování oznámení stavebníka dochází ze strany Archeologického ústavu ke zpracování osobních údajů stavebníka jako subjektu osobních údajů dle čl. 6 odst. 1 písm. c), e) obecného nařízení o ochraně osobních údajů a Archeologický ústav je v postavení Správce. Vaše osobní údaje v níže uvedeném rozsahu zpracováváme, pouze aby Vás Archeologický ústav či jiná oprávněná organizace dle zákona mohly kontaktovat za účelem provedení záchranného archeologického průzkumu.
"""

doc_attachment_heading_5 = """
<u>ROZSAH OSOBNÍCH ÚDAJŮ ZPRACOVÁVANÝCH SPRÁVCEM</u>
"""

doc_attachment_par_5 = """
Informujeme Vás, že Vaše osobní údaje jsou zpracovávány v rozsahu Vámi vyplněného formuláře, a to konkrétně v rozsahu:
    • jméno,
    • příjmení,
    • adresa,
    • telefonní číslo,
    • e-mail,
    • údaje o nemovité věci (parcelní číslo a bližší specifikace předmětu oznámení).
"""

doc_attachment_heading_6 = """
<u>DOBA ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
"""

doc_attachment_par_6 = """
Vaše osobní údaje budeme ukládat po dobu nezbytně nutnou maximálně však po dobu deseti let. Tyto lhůty vyplývají ze zákonných požadavků a z titulu ochrany zájmu subjektu údajů na prokázání splnění své zákonné povinnosti.
"""

doc_attachment_heading_7 = """
<u>DALŠÍ INFORMACE O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ</u>
"""

doc_attachment_par_7 = """
Osobní údaje subjektu údajů jsou zpracovávány automatizovaně v elektronické formě.
Příjemci Vašich osobních údajů, resp. výsledků jejich zpracování jsou:
    • oprávněné organizace dle zákona
Vaše osobní údaje nepředáváme a nemáme v úmyslu předat do třetí země nebo mezinárodní organizaci.
"""

doc_attachment_heading_8 = """
<u>POUČENÍ O PRÁVECH SUBJEKTŮ ÚDAJŮ</u>
"""

doc_attachment_par_8_1 = """
Subjekt údajů má právo požádat Správce o poskytnutí informace o zpracování jeho osobních údajů.
"""

doc_attachment_par_8_2 = """
Subjekt údajů má právo, aby Správce bez zbytečného odkladu opravil nepřesné osobní údaje, které se ho týkají. S přihlédnutím k účelům zpracování má subjekt údajů právo na doplnění neúplných osobních údajů, a to i poskytnutím dodatečného prohlášení.
Subjekt údajů má právo, aby Správce bez zbytečného odkladu vymazal osobní údaje, které se daného subjektu údajů týkají, a Správce má povinnost osobní údaje bez zbytečného odkladu vymazat, pokud je dán některý z důvodů stanovených obecným nařízením o ochraně osobních údajů.
"""

doc_attachment_par_8_3 = """
Subjekt údajů má právo, aby Správce omezil zpracování osobních údajů, v případech stanovených obecným nařízením o ochraně osobních údajů.
"""

doc_attachment_par_8_4 = """
Pokud se subjekt údajů domnívá, že došlo k porušení právních předpisů v souvislosti s ochranou jeho osobních údajů, má právo podat stížnost u dozorového úřadu. Dozorovým úřadem je v České republice Úřad pro ochranu osobních údajů.
"""


class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(
            0.75 * inch,
            0.75 * inch,
            page_number_text
        )
        canvas.restoreState()

    def get_style_dict(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle('amBodyText',
                                  fontName="OpenSans",
                                  fontSize=12,
                                  parent=styles['BodyText'],
                                  alignment=TA_JUSTIFY,
                                  spaceAfter=14,
                                  leading=20))
        styles.add(ParagraphStyle("amBodyTextCenter",
                                  parent=styles["amBodyText"],
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle("amHeading1",
                                  parent=styles["amBodyText"],
                                  alignment=TA_CENTER,
                                  fontName="OpenSansBold"))
        styles.add(ParagraphStyle("amDatum",
                                  parent=styles["amBodyText"],
                                  alignment=TA_RIGHT))
        styles.add(ParagraphStyle("amVec",
                                  parent=styles["amBodyText"],
                                  alignment=TA_LEFT,
                                  fontName="OpenSansBold"))
        styles.add(ParagraphStyle("amHeading2",
                                  parent=styles["amBodyText"],
                                  alignment=TA_CENTER,
                                  fontName="OpenSansBold"))
        styles.add(ParagraphStyle("amPodpis1",
                                  parent=styles["amBodyText"],
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle("amPodpis2",
                                  parent=styles["amBodyText"],
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle("amPodpis3",
                                  parent=styles["amPodpis2"],
                                  fontSize=10))
        return styles

    def build_pdf(self):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN
        )
        styles = self.get_style_dict()
        body_style = styles["amBodyText"]
        header = [
            Paragraph(header_line_1, styles["amHeading1"]),
            Paragraph(header_line_2, styles["amBodyTextCenter"]),
            Paragraph(header_line_3, styles["amBodyTextCenter"]),
            Paragraph(header_line_4, styles["amDatum"]),
        ]

        tbl_data = [
            [Paragraph(doc_sign_1, styles["amPodpis1"]), Paragraph("", styles["amBodyText"])],
            [Paragraph("", styles["amBodyText"]), Paragraph(doc_sign_2, styles["amPodpis2"])],
            [Paragraph("", styles["amBodyText"]), Paragraph(doc_sign_3, styles["amPodpis3"])],
        ]
        tbl = Table(tbl_data)

        page_1 = [
            Paragraph(doc_vec, styles["amVec"]),
            Paragraph(doc_par_1, body_style),
            Paragraph(doc_par_2, styles["amHeading2"]),
            Paragraph(doc_par_3, body_style),
            tbl
        ]

        attachment = [
            Paragraph(doc_attachment_heading_main_1, styles["amHeading2"]),
            Paragraph(doc_attachment_heading_main_2, styles["amHeading2"]),
            Paragraph(doc_attachment_heading_1, body_style),
            Paragraph(doc_attachment_par_1, body_style),
            Paragraph(doc_attachment_heading_2, body_style),
            Paragraph(doc_attachment_par_2, body_style),
            Paragraph(doc_attachment_heading_3, body_style),
            Paragraph(doc_attachment_par_3, body_style),
            Paragraph(doc_attachment_heading_4, body_style),
            Paragraph(doc_attachment_par_4, body_style),
            Paragraph(doc_attachment_heading_5, body_style),
            Paragraph(doc_attachment_par_5, body_style),
            Paragraph(doc_attachment_heading_6, body_style),
            Paragraph(doc_attachment_par_6, body_style),
            Paragraph(doc_attachment_heading_7, body_style),
            Paragraph(doc_attachment_par_7, body_style),
            Paragraph(doc_attachment_heading_8, body_style),
            Paragraph(doc_attachment_par_8_1, body_style),
            Paragraph(doc_attachment_par_8_2, body_style),
            Paragraph(doc_attachment_par_8_3, body_style),
            Paragraph(doc_attachment_par_8_4, body_style),
        ]
        my_doc.build(
            header + page_1 + attachment,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value


creator = PdfCreator()
with open("output.pdf", "wb") as file:
    file.write(creator.build_pdf())
