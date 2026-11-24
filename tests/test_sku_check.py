"""SKU Explorer safety and offline regression tests; no Android/emulator needed."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import sku_check_core as core
import sku_check_runner as runner

ROOT = Path(__file__).resolve().parents[1]


class SKUMetadataTests(unittest.TestCase):
    def test_requires_explicit_bounded_skus(self):
        self.assertEqual(
            core.validate_skus(["g1.2tb.ai.subs_variant", "g1.2tb.ai.subs_variant"]),
            ["g1.2tb.ai.subs_variant"])
        for invalid in ([], ["not-sku"], ["g1.x;rm -rf"], ["g1.2tb"] * 11):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                core.validate_skus(invalid)

    def test_ordered_phases_and_token_stripping(self):
        payload = [{
            "sku": "g1.2tb.ai.subs_variant",
            "offer_id": "test-offer",
            "base_plan_id": "yearly",
            "token": "SECRET-DO-NOT-STORE",
            "email": "secret@example.com",
            "phases": [
                {
                    "price_amount_micros": "0",
                    "currency": "USD", "billing_period": "P1M",
                    "billing_cycle_count": 1, "recurrence_mode": 2,
                    "purchaseToken": "VERY-SECRET",
                },
                {
                    "price_amount_micros": "19990000",
                    "currency": "USD", "billing_period": "P1M",
                    "billing_cycle_count": 0, "recurrence_mode": 1,
                },
            ],
        }]
        got = core.sanitize_offers(payload, ["g1.2tb.ai.subs_variant"])
        self.assertEqual(got["status"], "observed")
        self.assertEqual(len(got["items"][0]["phases"]), 2)
        self.assertFalse(got["eligibility_verified"])
        self.assertFalse(got["subscription_active_verified"])
        self.assertNotIn("SECRET", str(got))
        self.assertNotIn("secret@example.com", str(got))
        text = core.render_result(got)
        self.assertIn("0.00 USD / P1M", text)
        self.assertIn("19.99 USD / P1M", text)
        self.assertIn("UNVERIFIED", text)
        self.assertNotIn("token", text.lower())

    def test_rejects_missing_currency_and_malformed_phases(self):
        result = core.sanitize_offers([{
            "sku": "g1.play.20tb", "offer_id": "example",
            "base_plan_id": "monthly", "phases": [{
                "price_amount_micros": "19990000",
                "billing_period": "P1M", "currency": "UNKNOWN"
            }]
        }], ["g1.play.20tb"])
        self.assertEqual(result["status"], "not_returned")
        self.assertEqual(result["items"], [])

    def test_literal_null_offer_is_base_plan_not_extra_promotion(self):
        result = core.sanitize_offers([{
            "sku": "g1.2tb.ai.subs_variant",
            "offer_id": "null",
            "base_plan_id": "monthly",
            "phases": [{"price_amount_micros": "19990000",
                        "currency": "USD", "billing_period": "P1M"}],
        }], ["g1.2tb.ai.subs_variant"])
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["items"][0]["offer_id"], "")
        rendered = core.render_result(result)
        self.assertIn("Offer: (base plan)", rendered)
        self.assertIn("19.99 USD / P1M (1 month)", rendered)
        self.assertNotIn("Offer: null", rendered)

    def test_missing_and_no_offers_are_distinct(self):
        self.assertEqual(
            core.sanitize_offers([], ["g1.play.20tb"])["status"], "not_returned")
        self.assertEqual(
            core.sanitize_offers([{"sku": "g1.play.20tb", "no_offers": True}],
                                 ["g1.play.20tb"])["status"],
            "no_offers")

    def test_runner_fails_closed_without_adb(self):
        with patch.object(runner, "find_adb", return_value=None):
            out = runner.check_skus("emulator-5554", ["g1.play.20tb"])
        self.assertEqual(out["status"], "device_not_ready")
        self.assertEqual(out["items"], [])

    def test_runner_fails_closed_for_invalid_serial(self):
        with patch.object(runner, "find_adb", side_effect=RuntimeError("must not be called")) as find:
            out = runner.check_skus("../../bad", ["g1.play.20tb"])
            find.assert_not_called()
        self.assertEqual(out["status"], "device_not_ready")

    def test_query_javascript_has_no_checkout_path(self):
        js = (ROOT / "assets/frida/sku_query_readonly.js").read_text(encoding="utf-8")
        for forbidden in (
            "launchBillingFlow", "BillingFlowParams", "setOfferToken",
            "getOfferToken", "getPurchaseToken", "queryPurchasesAsync",
            "setOldPurchaseToken", "input tap"
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, js)
        self.assertIn("queryProductDetailsAsync", js)

    def test_step_one_uses_one_button_and_sku_runner_never_starts_checkout(self):
        ui = (ROOT / "tui.py").read_text(encoding="utf-8")
        runner = (ROOT / "sku_check_runner.py").read_text(encoding="utf-8")
        self.assertIn("sku_check_runner.py", ui)
        self.assertIn("SKU CATALOG", ui)
        self.assertNotIn('id="sku_explorer"', ui)
        self.assertNotIn("SKUExplorer(", ui)
        self.assertNotIn("launchBillingFlow", runner)

    def test_result_lists_skus_base_plans_offers_and_missing_candidates(self):
        raw = [{"sku": "g1.play.20tb", "offer_id": "intro",
                "base_plan_id": "monthly", "phases": [{
                    "price_amount_micros": "19990000", "currency": "USD",
                    "billing_period": "P1M"
                }]}]
        parsed = core.sanitize_offers(raw, ["g1.play.20tb", "g1.30tb"])
        output = core.render_result(parsed)
        self.assertIn("SKU: g1.play.20tb", output)
        self.assertIn("Offer: intro", output)
        self.assertIn("19.99 USD / P1M", output)
        self.assertIn("SKU: g1.30tb", output)
        self.assertIn("Not returned", output)
        self.assertNotIn("SECRET", output)
        self.assertEqual(parsed["missing_skus"], ["g1.30tb"])


@unittest.skipUnless(importlib.util.find_spec("textual") is not None,
                     "Textual is tested in Terminal UI previews with dependencies installed")
class StepOneSKUUITests(unittest.IsolatedAsyncioTestCase):
    async def test_one_step_one_button_and_inline_sku_catalogue(self):
        from tempfile import TemporaryDirectory
        from textual.widgets import Button, Select, Static, RichLog
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                self.assertEqual(app.query_one("#step", Select).value, 1)
                self.assertEqual(len(app.query("#sku_explorer")), 0)
                self.assertGreater(app.query_one("#quickstart", Button).region.width, 25)
                self.assertEqual(len(app.query("#workflow .workflow-step")), 6)
                self.assertFalse(app.query_one("#stage_5", Static).display)
                app._offer_report = {"offers": [
                    {"id": "12months-eft", "product": "g1.2tb.ai.subs_variant",
                     "micros": "0", "period": "P1Y"}
                ]}
                app._sku_report = core.sanitize_offers([{
                    "sku": "g1.play.20tb", "offer_id": "promo-2026",
                    "base_plan_id": "monthly", "phases": [{
                        "price_amount_micros": "19990000",
                        "currency": "USD", "billing_period": "P1M"
                    }]
                }], ["g1.play.20tb", "g1.30tb"])
                app._render_offer_catalog()
                await pilot.pause()
                self.assertTrue(app.query_one("#offer_view", RichLog).display)
                self.assertTrue(app.query_one("#offers_title", Static).display)
                rendered = "\n".join(segment.text for strip in
                                     app.query_one("#offer_view", RichLog).lines
                                     for segment in strip)
                self.assertIn("g1.play.20tb", rendered)
                self.assertIn("promo-2026", rendered)
                self.assertIn("19.99 USD", rendered)
                self.assertIn("g1.30tb", rendered)
                self.assertIn("12months-eft", rendered)

    async def test_real_step_one_launches_automatic_sku_scan(self):
        from tempfile import TemporaryDirectory
        from tui import GoogleAITUI
        from tui_core import Outcome

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                from device_diagnostics import ConnectionStatus
                app._checked_device = "emulator-5554"
                app._selected_account = "verified@example.test"
                app._verified_account = "verified@example.test"
                app._connection_state = ConnectionStatus(
                    "connected", ("emulator-5554",))
                app._real_step1_run = True
                with patch.object(app, "scan_known_skus") as scan:
                    app._finished(1, Outcome("listed", "Offers listed",
                                             "Review the available offers."), {
                        "status": "listed",
                        "detected_play_account": "verified@example.test",
                        "offers": [{"id": "12months-eft", "micros": "0",
                                    "product": "g1.2tb.ai.subs_variant"}],
                    })
                    self.assertTrue(app._offer_check_ready)
                    scan.assert_called_once_with("emulator-5554",
                                                 "verified@example.test",
                                                 app._extra_scan_generation)
                await pilot.pause()
                self.assertEqual(len(app.query("#sku_explorer")), 0)

    async def test_new_offers_appear_from_step_five_without_checkout(self):
        from tempfile import TemporaryDirectory
        from textual.widgets import Button, Select, Static
        from offer_discovery import parse_step1
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)) as pilot:
                self.assertFalse(app.query_one("#stage_5", Static).display)
                app._offer_check_ready = True
                app._offer_ready_device = "emulator-5554"
                app._update_discovered(parse_step1({"offers": [
                    {"product": "g1.play.20tb", "id": "offer-a"},
                    {"product": "g1.30tb", "id": "offer-b"},
                ]}))
                await pilot.pause()
                self.assertEqual(len(app._extra_offers), 2)
                self.assertIn("5. 30TB", str(app.query_one("#stage_5", Static).render()))
                self.assertIn("6. 20TB", str(app.query_one("#stage_6", Static).render()))
                app.query_one("#step", Select).value = 5
                await pilot.pause()
                self.assertEqual(str(app.query_one("#run", Button).label), "Inspect observed offer")
                with patch.object(app, "_start") as checkout:
                    app.selected_pressed()
                    await pilot.pause()
                    checkout.assert_not_called()
                self.assertEqual(len(app.screen_stack), 1)  # No SKU modal opened.
                self.assertIn("metadata", str(app.query_one("#state", Static).render()).lower())
                self.assertFalse(app.busy)

                app._update_discovered([], replace=True)
                await pilot.pause()
                self.assertFalse(app.query_one("#stage_5", Static).display)
                self.assertFalse(app.query_one("#stage_6", Static).display)
                self.assertEqual(app.query_one("#step", Select).value, 1)

    async def test_sku_scan_requires_same_verified_step_one_identity(self):
        from tempfile import TemporaryDirectory
        from textual.widgets import RichLog
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)):
                app._offer_report = {"offers": [
                    {"id": "12months-eft", "product": "g1.2tb.ai.subs_variant",
                     "micros": "0", "period": "P1Y"}
                ]}
                app._offer_check_ready = True
                app._offer_ready_device = "emulator-5554"
                app._offer_ready_account = "verified@example.test"
                result = core.sanitize_offers([{
                    "sku": "g1.play.20tb", "offer_id": "extra",
                    "base_plan_id": "monthly", "phases": [{
                        "price_amount_micros": "0", "currency": "USD",
                        "billing_period": "P1M",
                    }]
                }], ["g1.play.20tb"])
                app._known_skus_finished(result, "other-device",
                                         "verified@example.test", app._extra_scan_generation)
                self.assertIsNone(app._sku_report)
                app._known_skus_finished(result, "emulator-5554",
                                         "verified@example.test", app._extra_scan_generation)
                self.assertEqual(app._sku_report["status"], "observed")
                self.assertEqual(len(app._extra_offers), 1)
                self.assertTrue(app.query_one("#offer_view", RichLog).display)
                previous = app._sku_report
                app._extra_scan_generation += 1
                app._known_skus_finished({"status": "timeout"},
                                         "emulator-5554", "verified@example.test",
                                         app._extra_scan_generation - 1)
                self.assertIs(app._sku_report, previous)

    async def test_no_unobserved_step_five_execution(self):
        from tempfile import TemporaryDirectory
        from tui import GoogleAITUI

        with TemporaryDirectory() as directory:
            app = GoogleAITUI(repo=Path(directory))
            async with app.run_test(size=(110, 35)):
                app._start(5, False)
                app._start(6, False)
                self.assertFalse(app.busy)
                self.assertIsNone(app.current_step)


if __name__ == "__main__":
    unittest.main()
