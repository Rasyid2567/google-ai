import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from textual.widgets import Button, Footer

from device_diagnostics import ConnectionStatus
from stage_history import read_offer_history
from tui import Approval, GoogleAITUI, OfferRow
from tui_core import observed_offers, outcome_for_stage, runnable_offer_step


class OfferDashboardTests(unittest.IsolatedAsyncioTestCase):
    def test_scan_sources_merge_without_adding_checkout_paths(self):
        product = "g1.2tb.ai.subs_variant"
        unnamed = {"product": product, "id": None, "period": "P1M", "micros": 19990000}
        monthly = {**unnamed, "id": "base-plan-monthly", "inspect_only": True}
        annual = {"product": product, "id": "12months-eft", "period": "P1Y", "micros": 0}
        rows = observed_offers([unnamed, annual, monthly, {**annual, "inspect_only": True}])
        self.assertEqual([row["id"] for row in rows], ["12months-eft", "base-plan-monthly"])
        self.assertEqual([runnable_offer_step(row) for row in rows], [2, None])
        self.assertEqual(len(observed_offers([unnamed, monthly, {**monthly, "id": "base-plan-other"}])), 3)

    async def test_scan_run_cancel_retry_and_history(self):
        account = "fixture@example.com"
        product = "g1.2tb.ai.subs_variant"
        initial = {"product": product, "id": "12months-eft", "micros": 0, "period": "P1Y"}
        extension = {"product": product, "id": "6months-eft", "micros": 0, "period": "P6M"}
        with tempfile.TemporaryDirectory() as directory:
            for size in ((90, 20), (110, 35), (155, 40)):
                with self.subTest(size=size):
                    repo = Path(directory) / str(size[0])
                    app = GoogleAITUI(repo=repo, offer_dashboard=True)
                    app.linux_mode = False
                    with patch.object(app, "run_stage") as worker, patch.object(app, "_poll_connection"):
                        async with app.run_test(size=size) as pilot:
                            await pilot.pause()
                            worker.assert_called_once_with(1)
                            self.assertTrue(app.query_one("#status_panel").region.height > 0)
                            self.assertLess(app.query_one("#status_panel").region.y, size[1] - 4)
                            self.assertFalse(app.query_one("#advanced_toggle").display)
                            self.assertFalse(list(app.query(Footer)))
                            scan = app.query_one("#quickstart", Button)
                            stop = app.query_one("#stop", Button)
                            self.assertEqual(scan.region.y, stop.region.y)
                            self.assertLess(stop.region.width, 20)
                            content = app.query_one("#screen").region
                            self.assertLessEqual(content.width, 108)
                            self.assertLessEqual(abs(2 * content.x + content.width - size[0]), 1)

                            def finish_scan(offers):
                                app._verified_account = account
                                app._checked_device = "test-device"
                                app._connection_state = ConnectionStatus("connected", ("test-device",))
                                report = {"offers": offers, "status": "listed"}
                                app._finished(1, outcome_for_stage(1, 0, report), report)

                            finish_scan([initial, extension])
                            await pilot.pause()
                            rows = list(app.query(OfferRow))
                            self.assertEqual([row.step for row in rows], [2, 3])
                            button = rows[0].query_one(Button)
                            button.press()
                            await pilot.pause()
                            self.assertIsInstance(app.screen, Approval)
                            app.screen.dismiss(False)
                            await pilot.pause()
                            self.assertEqual(worker.call_count, 1)
                            button.press()
                            await pilot.pause()
                            app.screen.dismiss(True)
                            await pilot.pause()
                            worker.assert_called_with(2)
                            self.assertFalse(app.sequence)
                            self.assertFalse(stop.display)
                            self.assertTrue(all(widget.disabled for widget in app.query(".offer-run")))
                            app._finished(2, outcome_for_stage(2, 1, None), None)
                            await pilot.pause()
                            self.assertEqual(str(app.query(OfferRow).first().query_one(Button).label), "Run again")

                            app.quickstart_pressed()
                            finish_scan([initial])
                            await pilot.pause()
                            rows = list(app.query(OfferRow))
                            self.assertIn("Earlier scan", rows[1].description)
                            self.assertIn("Absent from latest scan", rows[1].description)
                            self.assertTrue(rows[1].query_one(Button).disabled)
                            saved = read_offer_history(repo, account)
                            self.assertEqual(len(saved), 2)
                            self.assertTrue(next(item["ran"] for item in saved if item["id"] == initial["id"]))
                            self.assertEqual(read_offer_history(repo, "other@example.com"), [])
                            sku = {
                                "sku": "g1.30tb", "base_plan_id": "monthly", "offer_id": "example",
                                "phases": [{"price_amount_micros": "0", "currency": "USD", "billing_period": "P1M"}],
                            }
                            app._known_skus_finished({"status": "observed", "items": [sku]},
                                                     "test-device", account, app._extra_scan_generation)
                            await pilot.pause()
                            extra = next(row for row in app.query(OfferRow) if "g1.30tb" in row.description)
                            self.assertIn("Listing only", extra.description)
                            self.assertFalse(list(extra.query(Button)))
                            self.assertTrue(app.query_one("#sku_details").display)
                            self.assertEqual(len(read_offer_history(repo, account)), 3)
            reopened = GoogleAITUI(repo=repo, offer_dashboard=True)
            with (patch.object(reopened, "run_stage") as worker,
                  patch.object(reopened, "_inspect_connection_periodically") as poll):
                async with reopened.run_test(size=(90, 20)) as pilot:
                    await pilot.pause()
                    worker.assert_not_called()
                    reopened._poll_connection()
                    poll.assert_not_called()
                    self.assertEqual(str(reopened.query_one("#quickstart", Button).label), "Scan again")
                    self.assertFalse(reopened.query_one("#activity").display)
                    self.assertFalse(reopened.query_one("#elapsed").display)
                    rows = list(reopened.query(OfferRow))
                    self.assertEqual(len(rows), 3)
                    self.assertEqual(str(rows[0].query_one(Button).label), "Run again")
                    self.assertTrue(all(button.disabled for button in reopened.query(".offer-run")))
                    self.assertTrue(all("Scan required" in row.description for row in rows if row.step is not None))
                    self.assertTrue(any("Listing only" in row.description for row in rows))
                    reopened.query_one("#quickstart", Button).press()
                    await pilot.pause()
                    worker.assert_called_once_with(1)
                    self.assertTrue(reopened.query_one("#elapsed").display)
