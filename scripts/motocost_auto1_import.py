"""
Motocost auto1 Import (ohne API-Key)

Liest die Daten aus den echten Grafana-/api/ds/query-Responses der Seite
https://dashboard.motocost.com/d/aehahbds97bpcb/auto1
und speichert sie als DRIVE-Importdatei.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = REPO_ROOT / "config" / "credentials.json"
OUT_DIR = REPO_ROOT / "data" / "imports" / "motocost"
LATEST_FILE = OUT_DIR / "latest.json"
AUTO1_URL = "https://dashboard.motocost.com/d/aehahbds97bpcb/auto1"
LOGIN_URL = "https://dashboard.motocost.com/login"


def _load_credentials() -> tuple[str, str]:
    data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    cfg = (data.get("external_systems") or {}).get("motocost") or {}
    user = (cfg.get("username") or "").strip()
    pwd = (cfg.get("password") or "").strip()
    if not user or not pwd:
        raise RuntimeError("Motocost Credentials fehlen unter external_systems.motocost")
    return user, pwd


def _frame_to_rows(frame: dict[str, Any]) -> list[dict[str, Any]]:
    schema = frame.get("schema") or {}
    data = frame.get("data") or {}
    fields = schema.get("fields") or []
    values = data.get("values") or []
    if not fields or not values:
        return []

    names = [f.get("name", "") for f in fields]
    row_count = max((len(col) for col in values if isinstance(col, list)), default=0)
    rows: list[dict[str, Any]] = []
    for i in range(row_count):
        row = {}
        for col_idx, name in enumerate(names):
            col = values[col_idx] if col_idx < len(values) else []
            row[name] = col[i] if isinstance(col, list) and i < len(col) else None
        rows.append(row)
    return rows


def _extract_rows_from_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    results = payload.get("results") or {}
    for result in results.values():
        frames = (result or {}).get("frames") or []
        for frame in frames:
            out.extend(_frame_to_rows(frame))
    return out


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    uniq = []
    for r in rows:
        key = (
            str(r.get("Bestandsnummer") or r.get("Nummer") or ""),
            str(r.get("Link") or ""),
            str(r.get("Preis") or ""),
            str(r.get("Modell") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq


def _score_rows(rows: list[dict[str, Any]]) -> int:
    """Bewertet Kandidaten: bevorzugt breite, große Tabellen mit Kernfeldern."""
    if not rows:
        return 0
    keys = set()
    for r in rows[: min(len(rows), 200)]:
        keys.update(r.keys())
    bonus = 0
    for k in ("Marke", "Modell", "Preis", "Marge", "Link", "KM", "EZ"):
        if k in keys:
            bonus += 50
    return len(rows) * max(len(keys), 1) + bonus


def main() -> int:
    username, password = _load_credentials()
    candidates: list[list[dict[str, Any]]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def on_response(resp):
            url = resp.url
            req = resp.request
            if "/api/ds/query" not in url:
                return
            body = req.post_data or ""
            lower = body.lower()
            # Nur die eigentlichen Datenqueries (refId A), nicht metricFindQuery
            if '"refid":"a"' not in lower and '"refid": "a"' not in lower:
                return
            try:
                payload = resp.json()
            except Exception:
                return
            rows = _extract_rows_from_response(payload)
            if not rows:
                return
            # Nur sinnvolle Tabellen als Kandidaten behalten
            field_count = len(rows[0].keys())
            if field_count >= 5 or len(rows) >= 20:
                candidates.append(rows)

        page.on("response", on_response)

        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.fill('input[name="user"]', username)
        page.fill('input[type="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_timeout(7000)

        if "/login" in page.url:
            browser.close()
            raise RuntimeError("Login fehlgeschlagen (weiterhin auf /login)")

        page.goto(AUTO1_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(15000)
        browser.close()

    if candidates:
        best = max(candidates, key=_score_rows)
    else:
        best = []
    rows = _dedupe_rows(best)
    now = datetime.now()
    payload = {
        "meta": {
            "source": "motocost_auto1_playwright",
            "dashboard_url": AUTO1_URL,
            "imported_at": now.isoformat(timespec="seconds"),
            "row_count": len(rows),
            "candidate_count": len(candidates),
        },
        "rows": rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    history = OUT_DIR / f"motocost_auto1_{now.strftime('%Y%m%d_%H%M%S')}.json"
    history.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"rows={len(rows)}")
    print(f"latest={LATEST_FILE}")
    print(f"history={history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
