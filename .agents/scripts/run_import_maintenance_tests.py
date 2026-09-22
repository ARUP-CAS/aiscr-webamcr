"""Run maintenance/import tests against a disposable PostgreSQL database.

Run through stdin in the web container. The dedicated PostgreSQL container must
be named amcr-maintenance-guard-tests, with the test-only password below. No
application database or migrations are used: only the maintenance table is
created. The container and its database must be disposable.
"""

import logging
import os
import sys
from unittest.mock import patch


def main():
    """Spustí izolované testy a vrátí jejich návratový kód."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webclient.settings.dev")

    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "maintenance-test-only",
            "HOST": "amcr-maintenance-guard-tests",
            "PORT": "5432",
        }
    }
    settings.DATABASES["urgent"] = {**settings.DATABASES["default"], "TEST": {"MIRROR": "default"}}
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    settings.CACHEOPS_ENABLED = False
    settings.LOGGING_CONFIG = None
    logging.disable(logging.CRITICAL)

    import django

    django.setup()

    from core.models import OdstavkaSystemu
    from django.db import connection
    from django.test.runner import DiscoverRunner
    from django.test.utils import setup_test_environment, teardown_test_environment

    labels = sys.argv[1:] or [
        "core.tests.test_import_maintenance",
        "core.tests.test_admin_sites_import_data",
        "core.tests.test_views_data_import_start",
        "core.tests.test_data_import_views",
        "core.tests.test_fake_redis",
    ]

    setup_test_environment()
    try:
        with connection.schema_editor() as editor:
            editor.create_model(OdstavkaSystemu)
        runner = DiscoverRunner(verbosity=2)
        suite = runner.build_suite(labels)
        # This isolated schema has no auth/content-type tables; skip post-migrate
        # bookkeeping after flush, while preserving actual transactions and SQL.
        with patch("django.core.management.commands.flush.emit_post_migrate_signal"):
            result = runner.run_suite(suite)
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(OdstavkaSystemu)
        connection.close()
        teardown_test_environment()
    return not result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(main())
