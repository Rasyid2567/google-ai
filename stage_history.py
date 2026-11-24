"""Private local stage history, independent of checkout authorization."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time


def history_path(repo: Path, account: str) -> Path:
    digest = hashlib.sha256(account.strip().lower().encode("utf-8")).hexdigest()
    return repo / "logs" / "stage-history" / (digest + ".json")


def read_history(repo: Path, account: str) -> list:
    try:
        data = json.loads(history_path(repo, account).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def latest_history(repo: Path) -> list:
    try:
        paths = sorted((repo / "logs" / "stage-history").glob("*.json"),
                       key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for path in paths:
            if path.name.endswith(".offers.json"):
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
    except (OSError, ValueError):
        pass
    return []


def _write_history(path: Path, entries: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as output:
            temporary = output.name
            json.dump(entries, output)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def record_history(repo: Path, account: str, step: int, status: str) -> None:
    entries = read_history(repo, account)[-99:]
    entries.append({"step": step, "status": status, "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    _write_history(history_path(repo, account), entries)


def read_offer_history(repo: Path, account: str) -> list[dict]:
    path = history_path(repo, account).with_suffix(".offers.json")
    return _read_offer_file(path) or []


def _read_offer_file(path: Path) -> list[dict] | None:
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
        return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else None
    except (OSError, ValueError):
        return None


def latest_offer_history(repo: Path) -> list[dict] | None:
    """Restore the last local catalog for viewing without an account check."""
    try:
        paths = sorted((repo / "logs" / "stage-history").glob("*.offers.json"),
                       key=lambda path: path.stat().st_mtime_ns, reverse=True)
    except OSError:
        return None
    for path in paths:
        history = _read_offer_file(path)
        if history is not None:
            return history
    return None


def record_offer_scan(repo: Path, account: str, offers: list[dict]) -> None:
    entries = {(item["product"], item["id"]): item for item in read_offer_history(repo, account)
               if isinstance(item.get("product"), str) and isinstance(item.get("id"), str)}
    for item in offers:
        key = item["product"], item["id"]
        entries[key] = {**entries.get(key, {}), **item}
    _write_history(history_path(repo, account).with_suffix(".offers.json"), list(entries.values()))
