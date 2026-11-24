"""Offer discovery and dynamic Step 5+ allocation tests (entirely offline)."""
from __future__ import annotations

import unittest

from offer_discovery import (
    ExtraOffer, MAX_EXTRA_OFFERS, merge_extra_offers, offer_details,
    offer_step_label, parse_sku_check, parse_step1,
)


class OfferDiscoveryTests(unittest.TestCase):
    def test_fixed_steps_2_to_4_not_duplicated(self):
        report = {"offers": [
            {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft", "micros": "0"},
            {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft", "micros": "0"},
            {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft-2", "micros": "0"},
            {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft-ss-2026", "micros": "0"},
            {"product": "g1.play.20tb", "id": "promo-2026", "micros": "19990000", "period": "P1M"},
            {"product": "g1.play.20tb", "id": "promo-2026", "micros": "19990000", "period": "P1M"},
        ]}
        offers = merge_extra_offers(parse_step1(report))
        self.assertEqual(len(offers), 2)
        self.assertTrue(offers[0].legacy_checkout_supported)
        self.assertEqual(offer_step_label(5, offers[0]), "5. +6mo optional")
        self.assertIn("20TB", offer_step_label(6, offers[1]))
        self.assertFalse(offers[1].legacy_checkout_supported)

    def test_null_and_base_plans_never_become_new_steps(self):
        """This reproduces the extra 'Offer: null' and empty sidebar rows."""
        report = {"offers": [
            {"product": "g1.2tb.ai.subs_variant", "id": "null", "period": "P1M"},
            {"product": "g1.2tb.ai.subs_variant", "id": None, "period": "P1M"},
            {"product": "g1.2tb.ai.subs_variant", "id": "undefined", "period": "P1M"},
            {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft", "period": "P1Y"},
        ]}
        sku_result = {"status": "observed", "items": [
            {"sku": "g1.2tb.ai.subs_variant", "base_plan_id": "monthly",
             "offer_id": "", "phases": [{"billing_period": "P1M",
                                          "currency": "USD", "price_amount_micros": "19990000"}]},
            {"sku": "g1.play.20tb", "base_plan_id": "monthly",
             "offer_id": "null", "phases": [{"billing_period": "P1M",
                                             "currency": "USD", "price_amount_micros": "19990000"}]},
            {"sku": "g1.play.20tb", "base_plan_id": "monthly",
             "offer_id": "promo-2026", "phases": [{"billing_period": "P1M",
                                                  "currency": "USD", "price_amount_micros": "19990000"}]}
        ]}
        offers = merge_extra_offers(parse_step1(report), parse_sku_check(sku_result))
        self.assertEqual([(x.product, x.offer_id) for x in offers],
                         [("g1.play.20tb", "promo-2026")])
        self.assertEqual(offer_step_label(5, offers[0]), "5. 20TB promo-2026")
        self.assertLessEqual(len(offer_step_label(5, offers[0])), 19)

    def test_supported_optional_offer_stays_first_and_labels_fit_sidebar(self):
        rows = merge_extra_offers([
            ExtraOffer("g1.play.ai.pro", "additional-long-promotion-id-2026"),
            ExtraOffer("g1.2tb.ai.subs_variant", "6months-eft-ss-2026"),
            ExtraOffer("g1.play.20tb", "deal-20tb"),
        ])
        self.assertEqual(rows[0].offer_id, "6months-eft-ss-2026")
        self.assertTrue(all(len(offer_step_label(index + 5, item)) <= 19
                            for index, item in enumerate(rows)))
        self.assertFalse(any("null" in offer_step_label(i+5, item).lower()
                             for i, item in enumerate(rows)))

    def test_step_one_report_explains_offer_codes_and_base_plans(self):
        from tui_core import offer_explorer_lines, report_summary

        report = {"offers": [
            {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft",
             "period": "P1Y", "micros": "0"},
            {"product": "g1.2tb.ai.subs_variant", "id": "6months-eft",
             "period": "P6M", "micros": "0"},
            {"product": "g1.2tb.ai.subs_variant", "id": "null",
             "period": "P1M", "micros": "19990000"}
        ]}
        self.assertIn("2 offer(s), 1 base plan(s)", report_summary(report))
        lines = "\n".join(offer_explorer_lines(report))
        self.assertIn("AI Pro 12 months (Step 2)", lines)
        self.assertIn("AI Pro +6 months (Step 3)", lines)
        self.assertIn("Standard/base plan (not a promo offer)", lines)
        self.assertNotIn("/ null", lines)
        self.assertIn("nonzero (currency unknown)", lines)

    def test_no_extra_offers_does_not_create_step_five(self):
        self.assertEqual(merge_extra_offers(parse_step1({"offers": [
            {"product": "g1.2tb.ai.subs_variant", "id": "12months-eft"}
        ]})), [])

    def test_custom_sku_merge_is_deterministic_and_token_free(self):
        sku_result = {"status": "observed", "items": [{
            "sku": "g1.play.20tb",
            "offer_id": "promo-2026",
            "base_plan_id": "monthly",
            "token": "DO_NOT_DISPLAY",
            "phases": [{
                "price_amount_micros": "19990000", "currency": "USD",
                "billing_period": "P1M", "purchaseToken": "SECRET",
            }],
        }]}
        after = merge_extra_offers(
            parse_step1({"offers": [
                {"product": "g1.play.20tb", "id": "promo-2026", "micros": "19990000"},
            ]}), parse_sku_check(sku_result)
        )
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0].currency, "USD")
        self.assertNotIn("DO_NOT_DISPLAY", repr(after))
        self.assertNotIn("SECRET", offer_details(after[0]))

    def test_cannot_treat_an_arbitrary_offer_as_legacy_checkout(self):
        self.assertFalse(ExtraOffer("g1.play.20tb", "6months-eft-ss-2026").legacy_checkout_supported)
        self.assertFalse(ExtraOffer("g1.2tb.ai.subs_variant", "new-offer").legacy_checkout_supported)

    def test_bounded_sanitized_and_no_observation_on_error(self):
        items = [{"product": "g1.play.20tb", "id": "o" + str(i)}
                 for i in range(MAX_EXTRA_OFFERS + 10)]
        items.append({"product": "g1.play.20tb;rm -rf", "id": "bad"})
        offers = merge_extra_offers(parse_step1({"offers": items}))
        self.assertEqual(len(offers), MAX_EXTRA_OFFERS)
        self.assertEqual(parse_sku_check({"status": "timeout", "items": items}), [])
        self.assertTrue(all(";" not in row.product for row in offers))


if __name__ == "__main__":
    unittest.main()
