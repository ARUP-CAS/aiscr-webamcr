from core.constants import IDENTIFIKATOR_DOCASNY_PREFIX, PROJEKT_STAV_OZNAMENY
from projekt.models import Projekt


def get_project_ident(project: Projekt) -> str:
    if project.ident_cely:
        if project.stav != PROJEKT_STAV_OZNAMENY and not project.ident_cely.startswith(
            IDENTIFIKATOR_DOCASNY_PREFIX
        ):
            return project.ident_cely
    else:
        # Generate new identifier
        # prefix = IDENTIFIKATOR_DOCASNY_PREFIX if project.stav == PROJEKT_STAV_OZNAMENY else ""
        # cadastre = project.get_main_cadastre()
        # rada = cadastre.okres.kraj.rada_id
        # TODO What if temporary ident will have previous year? Maybe better to get the creation date from the history
        #  table.
        # year = datetime.datetime.now().year
        # Retrieve max project ident consecutive number for this year
        # for p in Projekt.object.filter()
        return None
        # return prefix + rada + "-" + year + consecutive_number
