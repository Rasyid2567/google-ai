"""Deterministic, account-agnostic display model for offers found during Step 1.

This module never starts checkout. Unknown offers are INSPECT-ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re

_PRO = "g1.2tb.ai.subs_variant"
_FIXED_IDS = {"12months-eft", "6months-eft", "6months-eft-2"}
_OPTIONAL_ID = "6months-eft-ss-2026"
_SAFE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
MAX_EXTRA_OFFERS = 12


@dataclass(frozen=True)
class ExtraOffer:
    product: str
    offer_id: str
    base_plan: str = ""
    period: str = ""
    price_micros: str = ""
    currency: str = ""
    source: str = "step1"

    @property
    def legacy_checkout_supported(self) -> bool:
        # Only the repository's pre-existing Step 5 is explicitly implemented.
        return self.product == _PRO and self.offer_id == _OPTIONAL_ID

    @property
    def key(self) -> tuple[str, str, str]:
        return self.product, self.offer_id, self.base_plan


def _safe(value: object) -> str:
    """Treat API sentinel strings as missing IDs, never as named offers."""
    if not isinstance(value, str) or not _SAFE.fullmatch(value):
        return ""
    if value.casefold() in {"null", "none", "undefined", "nan", "false"}:
        return ""
    return value


def _micros(value: object) -> str:
    value = str(value) if isinstance(value, (int, str)) and not isinstance(value, bool) else ""
    return value if value.isascii() and value.isdecimal() and len(value) <= 18 else ""


def parse_step1(report: dict | None) -> list[ExtraOffer]:
    """Parse only the sanitized offer identifiers from a fresh Step 1 report."""
    if not isinstance(report, dict) or not isinstance(report.get("offers"), list):
        return []
    entries = []
    for raw in report["offers"][:100]:
        if not isinstance(raw, dict):
            continue
        product, offer_id = _safe(raw.get("product")), _safe(raw.get("id"))
        if not product or not offer_id or (product == _PRO and offer_id in _FIXED_IDS):
            continue
        entries.append(ExtraOffer(
            product=product, offer_id=offer_id, period=_safe(raw.get("period")),
            price_micros=_micros(raw.get("micros")), source="step1"))
    return entries


def parse_sku_check(result: dict | None) -> list[ExtraOffer]:
    """Map token-free ProductDetails observations to offer descriptions."""
    if not isinstance(result, dict) or result.get("status") != "observed":
        return []
    rows = result.get("items")
    if not isinstance(rows, list):
        return []
    entries = []
    for row in rows[:100]:
        if not isinstance(row, dict):
            continue
        product = _safe(row.get("sku"))
        offer_id = _safe(row.get("offer_id"))
        base = _safe(row.get("base_plan_id"))
        if not product or not base or (product == _PRO and offer_id in _FIXED_IDS):
            continue
        # Google Play includes standard/base plans with no promotional offer ID.
        # They belong in Step 1 SKU details, NOT in the actionable Step 5+ list.
        if not offer_id:
            continue
        phases = row.get("phases")
        first = phases[0] if isinstance(phases, list) and phases and isinstance(phases[0], dict) else {}
        entries.append(ExtraOffer(
            product=product, offer_id=offer_id, base_plan=base,
            period=_safe(first.get("billing_period")), currency=_safe(first.get("currency")),
            price_micros=_micros(first.get("price_amount_micros")), source="sku"))
    return entries


def merge_extra_offers(*groups: list[ExtraOffer]) -> list[ExtraOffer]:
    """Deduplicate and allocate stable positions. Prefer the known optional offer at Step 5."""
    by_key: dict[tuple[str, str], ExtraOffer] = {}
    for group in groups:
        for item in group:
            if (not isinstance(item, ExtraOffer)
                    or not _safe(item.product) or not _safe(item.offer_id)
                    or item.offer_id.startswith("base-plan-")
                    or (item.product == _PRO and item.offer_id in _FIXED_IDS)):
                continue
            key = (item.product, item.offer_id)
            existing = by_key.get(key)
            if existing is None or (item.source == "sku" and existing.source != "sku"):
                by_key[key] = item
    return sorted(by_key.values(), key=lambda x: (
        0 if x.legacy_checkout_supported else 1, x.product, x.offer_id
    ))[:MAX_EXTRA_OFFERS]


def offer_step_label(step: int, offer: ExtraOffer) -> str:
    """Keep sidebar rows legible in a 26-column Textual controls pane.

    Full SKU and offer IDs remain available in the Step 1 catalogue and the
    selected offer's details; never truncate identifiers in those views.
    """
    if offer.legacy_checkout_supported:
        return f"{step}. +6mo optional"
    product = offer.product.lower()
    if "30tb" in product:
        group = "30TB"
    elif "20tb" in product:
        group = "20TB"
    elif "ai.pro" in product or "2tb.ai" in product:
        group = "AI Pro"
    else:
        group = "SKU"
    prefix = f"{step}. {group} "
    room = max(1, 19 - len(prefix))
    return prefix + offer.offer_id[:room]


def offer_details(offer: ExtraOffer) -> str:
    price = "Unknown"
    if offer.price_micros.isdecimal():
        price = f"{Decimal(offer.price_micros) / Decimal(1_000_000):,.2f}"
        price += f" {offer.currency}" if offer.currency else " (currency not returned)"
    lines = [
        f"Product SKU: {offer.product}",
        f"Offer ID: {offer.offer_id}",
        f"Base plan: {offer.base_plan or 'Not returned'}",
        f"First pricing phase: {price} / {offer.period or 'unknown billing period'}",
        "Later renewal price: NOT VERIFIED",
        "Eligibility: NOT VERIFIED",
        "This observation does not authorize checkout or change subscriptions.",
    ]
    return "\n".join(lines)
