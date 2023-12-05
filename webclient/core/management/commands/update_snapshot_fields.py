import logging
from django.core.management.base import BaseCommand

from cron.tasks import update_snapshot_fields

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug("core.views.update_snapshot_fields.start")
        update_snapshot_fields()
        logger.debug("core.views.update_snapshot_fields.end")
