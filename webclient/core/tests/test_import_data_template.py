"""Test pro ``admin/import_data/import_data.html`` — pořadí větví ``job_id``/``import_data_running``
vůči ``maintenance``.

Ověřuje přímo vykreslením šablony (bez ``AmcrCustomAdminSite.import_data``/``change_list.html``
scaffoldingu), že polling UI běžící úlohy a lock-busy reset zůstávají dosažitelné i po skončení
odstávky (``{% if not maintenance %}`` dřív blokoval obě větve, zatímco polling ``<script>``
byl vázaný jen na ``job_id`` a padal na chybějících
DOM elementech).
"""

from django.template.loader import get_template
from django.test import SimpleTestCase

TEMPLATE_NAME = "admin/import_data/import_data.html"

BASE_CONTEXT = {
    "app_list": [],
    "is_popup": False,
    "has_permission": True,
    "site_url": "/",
    "available_apps": [],
}


class ImportDataTemplateBranchOrderTest(SimpleTestCase):
    """Ověřuje, že šablona řadí ``job_id``/``import_data_running`` před ``not maintenance``."""

    def _render(self, **context_overrides):
        """Vykreslí šablonu s ``BASE_CONTEXT`` doplněným o zadané klíče.

        :param context_overrides: Klíče kontextu specifické pro daný scénář (``maintenance``,
            ``import_data_running``, ``job_id`` …).
        :return: Vykreslený HTML výstup jako řetězec.
        """
        template = get_template(TEMPLATE_NAME)
        return template.render(dict(BASE_CONTEXT, **context_overrides))

    def test_own_job_polling_ui_renders_after_maintenance_ends(self):
        """Vlastní běžící úloha musí vykreslit polling shell i skript, i když ``maintenance`` skončila.

        Jobs mají TTL až 48 h, takže admin může úlohu znovu otevřít poté, co odstávka skončí.
        """
        html = self._render(
            maintenance=False,
            import_data_running=True,
            job_id="job-123",
            url="/progress/",
            url_stop="/stop/",
            url_start="/start/",
            url_cancel="/cancel/",
            url_reset="/reset/",
            performed_action_label="Insert",
        )
        self.assertIn('id="progressBarBoxData"', html)
        self.assertIn('id="processCurrentStatus"', html)
        # The polling <script> must accompany the polling markup, not render on its own.
        self.assertIn("const requestUrl", html)
        self.assertNotIn("core.templates.admin.import_data.not_maintenance", html)

    def test_lock_busy_reset_renders_after_maintenance_ends(self):
        """Lock jiného admina musí zůstat viditelný s dostupným resetem i mimo odstávku."""
        html = self._render(
            maintenance=False,
            import_data_running=True,
            url_reset="/reset-active/",
        )
        self.assertIn('id="resetImportBusy"', html)
        self.assertIn("core.templates.admin.import_data.import_is_running", html)
        self.assertNotIn("core.templates.admin.import_data.not_maintenance", html)
        # No job_id in this context, so the polling shell/script must not render.
        self.assertNotIn('id="progressBarBoxData"', html)
        self.assertNotIn("const requestUrl", html)

    def test_idle_state_still_shows_not_maintenance_message(self):
        """Bez běžící úlohy a bez cizího locku musí mimo odstávku zůstat původní chování."""
        html = self._render(maintenance=False, import_data_running=False)
        self.assertIn("core.templates.admin.import_data.not_maintenance", html)
        self.assertNotIn('id="id_data_file"', html)
        self.assertNotIn('id="progressBarBoxData"', html)

    def test_upload_form_renders_during_maintenance_when_idle(self):
        """Beze změny: v odstávce bez běžící úlohy se pořád nabízí upload formulář."""
        html = self._render(maintenance=True, import_data_running=False)
        self.assertIn('id="id_data_file"', html)
        self.assertNotIn("core.templates.admin.import_data.not_maintenance", html)
