# Review of third-party Google AI promotion SKU candidates

This is an **inspection-only** supplement to the existing Offer Explorer. A third-party ZIP shared for review in November 2026 claimed several Google AI Pro / Ultra offer IDs, durations and prices. Those claims are **not independently verified**, and visible Google Play metadata does not establish eligibility, availability, an entitlement, or actual renewal pricing.

## What was added

Use the existing Android environment and the currently selected Google Play account to inspect **one candidate SKU at a time**:

```sh
python ultra0.py --inspect-sku g1.play.2tb.ai
python ultra0.py --inspect-sku g1.20tb.3months_ip_90p
python ultra0.py --inspect-sku g1.20tb.3months_ip_80p
python ultra0.py --inspect-sku g1.ai.ultra.3months_ip_75p.acq
python ultra0.py --inspect-sku g1.ai.ultra.3months_ip_90p.acq
```

`--inspect-sku` automatically enables `--list` and requires the built-in allowlist of candidate IDs. It rejects `--force`, subscription stacking/old purchase tokens, alternate plans, and account-file checkout inputs. It cannot initiate a checkout through the bundled Frida script. A candidate that returns no offers is **not** evidence of a bug or a method to overcome Google's restrictions.

The normal Windows/macOS Textual Steps **0–5 remain unchanged**. This optional inspection is available via the direct Python CLI and is **not** a new purchase stage. Device preflight may still alter emulator, proxy or Frida setup, as documented in [Security](../SECURITY.md). Do not run this inspection on a device or profile you do not control.

## Why the ZIP was not directly imported

The third-party archive uses switches that can bypass Play-account checks or force offer tokens, handles purchase tokens across potentially multiple Android accounts, prints sensitive checkout tokens, and infers transaction outcomes from incomplete screen text. Its docs also inconsistently describe Ultra as a 12-month free offer while the supplied new batch files describe paid three-month promotions. Those behaviors were **not** copied. Never assume a client-visible offer is valid for the active Google Play account, or that a discounted first phase determines future charges.

For the supported checkout steps, continue using the project’s existing explicit-approval flow and independently verify the final subscription state directly in Google Play. See [original source and credits](../THIRD_PARTY_NOTICES.md).

## Verification limits

Offline tests validate the SKU allowlist, JavaScript list-only guard and failure of mixed checkout/inspection arguments. They do **not** authenticate the claimed SKU IDs, discounts, trial duration, regional availability or Android/Frida behavior. No live subscription, payment, account eligibility or in-device checkout was tested for this feature.
