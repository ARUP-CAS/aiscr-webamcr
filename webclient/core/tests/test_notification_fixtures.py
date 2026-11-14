"""Regrese izolace odeslání notifikační úlohy při přípravě testovacích dat."""

from unittest.mock import patch

from core.tests.notification_fixtures import mock_project_notifications
from django.test import SimpleTestCase
from notifikace_projekty.tasks import check_hlidaci_pes


class ProjectNotificationFixtureTest(SimpleTestCase):
    """Ověřuje, že fixture potlačí jen dispatch, nikoli explicitní běh úlohy."""

    def test_dispatch_is_mocked_but_explicit_task_execution_remains_available(self):
        """Delay neprovede úlohu ani v eager režimu; přímé run zůstává použitelné."""
        with patch.object(check_hlidaci_pes, "run", return_value="explicit-result") as run:
            with mock_project_notifications() as dispatch:
                check_hlidaci_pes.delay(123)
                dispatch.assert_called_once_with(123)
                run.assert_not_called()
                self.assertEqual(check_hlidaci_pes.run(123), "explicit-result")
                run.assert_called_once_with(123)

    def test_dispatch_is_restored_after_fixture_failure(self):
        """Selhání fixture nesmí zanechat mock v dalších testech."""
        original = check_hlidaci_pes.delay
        with self.assertRaisesRegex(ValueError, "fixture failed"):
            with mock_project_notifications():
                raise ValueError("fixture failed")
        self.assertEqual(check_hlidaci_pes.delay, original)
