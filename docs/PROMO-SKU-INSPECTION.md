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

## Exact ZIP findings: Ultra 20x / 30 TB

The archive's **`10_Ultra30TB_3个月1折_19.99.bat`** specifically claims the **Ultra 20x** tier (30 TB), **US$19.99 per month for the first three months**, not US$19.99 total for the entire three-month period. It states a US$199.99 monthly renewal from month four.

| Archive batch file | Claimed plan | Exact candidate product ID | Claimed months 1–3 | Claimed month 4 onward | Arithmetic for first 3 months |
| --- | --- | --- | --- | --- | --- |
| `10_Ultra30TB_3个月1折_19.99.bat` | Ultra 20x, 30 TB | `g1.ai.ultra.3months_ip_90p.acq` | US$19.99/month | US$199.99/month | US$59.97 |
| `9_Ultra30TB_3个月2.5折_49.99.bat` | Ultra 20x, 30 TB | `g1.ai.ultra.3months_ip_75p.acq` | US$49.99/month | US$199.99/month | US$149.97 |
| `7_Ultra20TB_3个月1折_9.99.bat` | Ultra 5x, 20 TB | `g1.20tb.3months_ip_90p` | US$9.99/month | US$99.99/month | US$29.97 |
| `8_Ultra20TB_3个月2折_19.99.bat` | Ultra 5x, 20 TB | `g1.20tb.3months_ip_80p` | US$19.99/month | US$99.99/month | US$59.97 |

These are **claims found in the supplied ZIP**, not verified Google-authorized regional offers. Google's public US plan information separately confirms the standard Ultra 5x / Ultra 20x prices of US$99.99 / US$199.99 per month (see [Google subscription prices](https://gemini.google/subscriptions/?currencyCode=USD)); it does not verify the 90% promotional offer. Validate the **actual payment due, currency, full three-month billing schedule, renewal terms and account** on the Google Play screen, rather than relying on the table, the SKU name, or its first pricing phase.

**Source prerequisites (not a guarantee of success):** The author's workflow specifies a MuMu emulator running an Android 12 image, root and ADB debugging enabled; Google Play Store and Google One installed; an account that has not previously used a trial offer; and the appropriate Frida version. The archive's setup instructions pin **Frida 16.5.9**. The current toolkit's other Android compatibility paths should not be removed or narrowed to this particular emulator image. In all cases, use an account and device you control and keep payments/manual confirmations separate from discovery.

**Source inconsistency and checkout risk:** The named batch file calls `ultra0.py --account "current@device" --no-add --force --allow-paid --sku g1.ai.ultra.3months_ip_90p.acq`. The `--force` switch skips Google Play account identity verification. `--allow-paid` permits opening the billing flow for a non-zero price; the archive's `confirm_zero` does *not* validate the claimed paid promotion and its documentation contradicts its automatic subscription-tap behavior for zero-price cases. Do **not** copy the batch file verbatim into maintained scripts or execute it as proof of eligibility. The archive's Chinese usage text also references batch filenames `10_查Ultra促销档.bat` and `11_Ultra30TB_3个月1折_19.99.bat` that are not present under those names in the supplied ZIP.

**The new `--inspect-sku` mode only lists the candidate offer metadata. It never opens checkout, never enables `--force`, and does not claim the 3-month price or expiry is verified.**

## Why the ZIP was not directly imported

The third-party archive uses switches that can bypass Play-account checks or force offer tokens, handles purchase tokens across potentially multiple Android accounts, prints sensitive checkout tokens, and infers transaction outcomes from incomplete screen text. Its docs also inconsistently describe Ultra as a 12-month free offer while the supplied new batch files describe paid three-month promotions. Those behaviors were **not** copied. Never assume a client-visible offer is valid for the active Google Play account, or that a discounted first phase determines future charges.

For the supported checkout steps, continue using the project’s existing explicit-approval flow and independently verify the final subscription state directly in Google Play. See [original source and credits](../THIRD_PARTY_NOTICES.md).

## Verification limits

Offline tests validate the SKU allowlist, JavaScript list-only guard and failure of mixed checkout/inspection arguments. They do **not** authenticate the claimed SKU IDs, discounts, trial duration, regional availability or Android/Frida behavior. No live subscription, payment, account eligibility or in-device checkout was tested for this feature.
