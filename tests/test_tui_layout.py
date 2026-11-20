"""Offline checks for the redesigned dashboard's visible controls and content."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_update import UpdateInfo
from tui_core import Outcome


class DashboardLayoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_idle_layout_shows_full_cards_warning_and_primary_controls(self):
        from tui import GoogleAITUI
        for size in ((110, 35), (90, 20), (60, 20), (48, 20)):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                app = GoogleAITUI(repo=Path(directory))
                with patch("tui.check_for_update", return_value=UpdateInfo("current", "Up to date · abcdef12")), \
                     patch.object(GoogleAITUI, "run_stage") as stage:
                    async with app.run_test(size=size) as pilot:
                        await pilot.pause()
                        for selector in ("#device", "#account"):
                            self.assertGreaterEqual(app.query_one(selector).content_region.height, 2)
                        for selector in ("#brand_title", "#quickstart", "#advanced_toggle",
                                         "#payment_notice_compact", "#state", "#message", "#elapsed",
                                         "#nav_help", "#diagnose", "#debug", "#exit", "#update"):
                            region = app.query_one(selector).region
                            self.assertGreater(region.height, 0, selector)
                            self.assertGreaterEqual(region.x, 0, selector)
                            self.assertLessEqual(region.right, size[0], selector)
                            self.assertLessEqual(region.bottom, size[1] - 1, selector)
                        welcome = app.query_one("#welcome_panel")
                        self.assertEqual(welcome.max_scroll_y, 0, "Default warning must not need scrolling")
                        self.assertFalse(app.ENABLE_COMMAND_PALETTE)
                        self.assertFalse(app.busy)
                        stage.assert_not_called()

    async def test_toolbar_labels_fit_and_remain_accessible_by_keyboard(self):
        from tui import GoogleAITUI
        for size in ((110, 35), (90, 20), (60, 20), (48, 20)):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                app = GoogleAITUI(repo=Path(directory))
                async with app.run_test(size=size) as pilot:
                    await pilot.pause()
                    for selector in ("#nav_help", "#diagnose", "#debug", "#exit", "#update"):
                        button = app.query_one(selector)
                        self.assertLessEqual(len(str(button.label)), button.content_region.width, selector)
                        button.focus()
                        await pilot.pause()
                        self.assertIs(app.focused, button)

    async def test_stop_and_next_are_visible_without_opening_advanced_settings(self):
        from tui import GoogleAITUI
        for size in ((110, 35), (90, 20), (60, 20)):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory:
                app = GoogleAITUI(repo=Path(directory))
                with patch.object(GoogleAITUI, "run_stage"):
                    async with app.run_test(size=size) as pilot:
                        app._start(1, False)
                        await pilot.pause()
                        stop = app.query_one("#stop")
                        self.assertTrue(stop.display)
                        self.assertLessEqual(stop.region.bottom, app.query_one("#content").region.bottom)
                        self.assertFalse(app.query_one("#workflow_actions").display)
                        app._finished(1, Outcome("listed", "Offers loaded", "Review the account."), None)
                        app._start(2, True)
                        app._finished(2, Outcome("checkout_requested", "Check Google Play", "Verify manually.", True), None)
                        await pilot.pause()
                        next_button = app.query_one("#next")
                        self.assertTrue(next_button.display)
                        self.assertLessEqual(next_button.region.bottom, app.query_one("#content").region.bottom)
                        app.next_pressed()
                        await pilot.pause()
                        from tui import Approval
                        self.assertIsInstance(app.screen, Approval)
                        for selector in ("#cancel", "#approve"):
                            region = app.screen.query_one(selector).region
                            self.assertGreaterEqual(region.y, 0)
                            self.assertLessEqual(region.bottom, size[1])
                            self.assertLessEqual(region.right, size[0])
                        await pilot.click("#cancel")

    async def test_update_state_is_quiet_for_dev_and_highlights_available_version(self):
        from tui import GoogleAITUI
        with tempfile.TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test() as pilot:
                await pilot.pause()
                reason = "Automatic updates require main. Update development branches manually."
                app._update_check_done(UpdateInfo("error", reason))
                self.assertIn("Development build", str(app.query_one("#update_status").render()))
                self.assertEqual(app.query_one("#update_status").tooltip, reason)
                self.assertFalse(app.query_one("#update_bar").has_class("available"))
                app._update_check_done(UpdateInfo("available", "New version · abcdef12 → 12345678"))
                self.assertTrue(app.query_one("#update_bar").has_class("available"))
                self.assertEqual(str(app.query_one("#update").label), "Update & Restart")
