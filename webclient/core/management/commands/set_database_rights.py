import logging
from django.core.management.base import BaseCommand
from django.conf import settings
import psycopg2


logger = logging.getLogger(__name__)
ROLE_NAME = "cz_archeologickamapa_api_view"


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug("core.views.set_database_rights.start")
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(host=settings.DATABASES["default"]["HOST"],
                                    database=settings.DATABASES["default"]["NAME"],
                                    user=settings.DATABASES["default"]["USER"],
                                    password=settings.DATABASES["default"]["PASSWORD"]
                                    )
            cur = conn.cursor()
            cur.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {ROLE_NAME};")
            cur.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {ROLE_NAME}")
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("core.views.set_database_rights.end", extra={"error": error})
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()
        logger.debug("core.views.set_database_rights.end")
