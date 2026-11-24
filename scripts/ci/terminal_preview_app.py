#!/usr/bin/env python3
"""Render real TUI screens with synthetic, non-transactional fixture states."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tui import GoogleAITUI  # noqa: E402
from tui_core import Outcome  # noqa: E402
from device_diagnostics import ConnectionStatus  # noqa: E402
from textual.widgets import Static  # noqa: E402
from offer_discovery import parse_step1  # noqa: E402
from sku_check_core import sanitize_offers  # noqa: E402

SCENARIOS = {"startup", "disconnected", "offer_found", "step_picker", "approval", "review",
             "linux_startup", "linux_step_picker", "sku_offers", "sku_missing",
             "sku_extra_steps"}
scenario = os.environ.get("PREVIEW_SCENARIO", "")
if scenario not in SCENARIOS:
    raise SystemExit("Invalid preview scenario")


class PreviewApp(GoogleAITUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Synthetic states; never invoke real Android/Google Play operations.
        # Linux scenarios explicitly activate the native Linux UI path.
        self.linux_mode = scenario.startswith("linux_")
        self.macos_mode = False
        self.native_mode = self.linux_mode

    def _poll_connection(self):
        pass  # Never probe host devices from a screenshot run.

    def run_stage(self, step):
        raise RuntimeError("Real stages are disabled in terminal previews")

    def on_mount(self):
        super().on_mount()
        self.set_timer(0.5, self.prepare_scenario)

    def prepare_scenario(self):
        if scenario in {"startup", "linux_startup"}:
            return
        if scenario in ("sku_offers", "sku_missing", "sku_extra_steps"):
            # Real dashboard widgets, simulated ProductDetails, no Android.
            primary = [
                {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft",
                 "micros": "0", "period": "P1Y"},
            ]
            if scenario == "sku_extra_steps":
                primary += [
                    {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft-ss-2026",
                     "micros": "0", "period": "P6M"},
                    {"product": "g1.play.20tb", "id": "promo-2026",
                     "micros": "19990000", "period": "P1M"},
                    # Real-world base-plan sentinel: must stay out of Steps 5+.
                    {"product": "g1.play.20tb", "id": "null",
                     "micros": "19990000", "period": "P1M"},
                ]
            self._offer_report = {"status": "listed", "offers": primary}
            requested = ["g1.2tb.ai.subs_variant", "g1.play.20tb",
                         "g1.play.ai.pro", "g1.30tb"]
            if scenario == "sku_missing":
                rows = [
                    {"sku": "g1.2tb.ai.subs_variant", "no_offers": True},
                    {"sku": "g1.play.20tb", "no_offers": True},
                ]
            else:
                rows = [
                    {"sku": "g1.2tb.ai.subs_variant",
                     "offer_id": "12months-eft", "base_plan_id": "annual",
                     "phases": [{"price_amount_micros": "0", "currency": "USD",
                                 "billing_period": "P1Y"}]},
                    {"sku": "g1.play.20tb",
                     "offer_id": "promo-2026", "base_plan_id": "monthly",
                     "phases": [{"price_amount_micros": "19990000",
                                 "currency": "USD", "billing_period": "P1M"}]},
                    {"sku": "g1.play.20tb",
                     "offer_id": "null", "base_plan_id": "monthly",
                     "phases": [{"price_amount_micros": "19990000",
                                 "currency": "USD", "billing_period": "P1M"}]},
                ]
            self._sku_report = sanitize_offers(rows, requested)
            self._update_discovered(parse_step1(self._offer_report))
            self._render_offer_catalog()
            self.query_one("#state", Static).update(
                "Step 1 complete · SKU scan results (SIMULATED)")
            self.query_one("#activity", Static).update(
                "Checked four candidate SKUs; see offer list below.")
            self.query_one("#status_panel").scroll_end(animate=False)
            return
        if scenario == "disconnected":
            self._connection_polled(ConnectionStatus("disconnected"))
        elif scenario == "offer_found":
            # The synthetic successful check needs the same device identity
            # that the real Step 1 status output supplies.
            self._received("Device emulator-5554")
            self._verified_account = "preview@example.invalid"
            self._finished(1, Outcome("listed", "Offers loaded", "Review offers"), {
                "status": "listed", "detected_play_account": "preview@example.invalid",
                "offers": [{"id": "12months-eft", "micros": "0", "period": "P1Y"}],
            })
        elif scenario in {"step_picker", "linux_step_picker"}:
            self.advanced_pressed()
        elif scenario == "approval":
            self._offer_check_ready = True
            self._confirm_stage(2, True)
        elif scenario == "review":
            self._offer_check_ready = True
            self.sequence = True
            self.current_step = 2
            self._finished(2, Outcome("checkout_requested", "Checkout submitted - not yet verified",
                                     "Check Google Play subscriptions and renewal date.", True), {})


PreviewApp(repo=Path(__file__).resolve().parents[2]).run()
