"""
Motocost/Grafana Netzwerk-Probe

Ziel:
- Browser-Login mit Selenium ausführen
- Relevante Grafana-Requests erfassen (insb. /api/ds/query)
- Prüfen, ob limit/offset/skip in den Query-Bodies vorkommen
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


REPO_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = REPO_ROOT / "config" / "credentials.json"
OUT_DIR = REPO_ROOT / "docs" / "workstreams" / "verkauf"
LOGIN_URL = "https://dashboard.motocost.com/login"
# Standardquelle für DRIVE-Integration: Subpage "auto1"
DASHBOARD_UID_URL = "https://dashboard.motocost.com/d/aehahbds97bpcb/auto1"


def load_credentials() -> tuple[str, str]:
    data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    mc = (data.get("external_systems") or {}).get("motocost") or {}
    username = (mc.get("username") or "").strip()
    password = (mc.get("password") or "").strip()
    if not username or not password:
        raise RuntimeError("Motocost-Credentials fehlen in config/credentials.json unter external_systems.motocost")
    return username, password


def setup_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=opts)


def try_login(driver: webdriver.Chrome, username: str, password: str) -> dict:
    result = {"login_success": False, "final_url": "", "error": None}
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 25)
        user = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='user'], input[type='email']")))
        pwd = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
        user.clear()
        user.send_keys(username)
        pwd.clear()
        pwd.send_keys(password)

        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], button[aria-label='Login button']"))
        )
        submit.click()

        # Warten bis URL wechselt oder Dashboard-typische Elemente erscheinen
        time.sleep(4)
        for _ in range(10):
            if "/login" not in driver.current_url:
                break
            time.sleep(1)

        result["final_url"] = driver.current_url
        result["login_success"] = "/login" not in driver.current_url
        return result
    except Exception as e:
        result["error"] = str(e)
        result["final_url"] = driver.current_url
        return result


def collect_network_logs(driver: webdriver.Chrome) -> dict:
    entries = []
    for log in driver.get_log("performance"):
        try:
            msg = json.loads(log["message"]).get("message", {})
        except Exception:
            continue
        method = msg.get("method")
        params = msg.get("params", {})
        if method == "Network.requestWillBeSent":
            req = params.get("request", {})
            url = req.get("url", "")
            if "/api/" in url:
                entries.append(
                    {
                        "kind": "request",
                        "requestId": params.get("requestId"),
                        "url": url,
                        "http_method": req.get("method"),
                        "postData": req.get("postData", ""),
                    }
                )
        elif method == "Network.responseReceived":
            resp = params.get("response", {})
            url = resp.get("url", "")
            if "/api/" in url:
                entries.append(
                    {
                        "kind": "response",
                        "requestId": params.get("requestId"),
                        "url": url,
                        "status": resp.get("status"),
                        "mimeType": resp.get("mimeType"),
                    }
                )
    return {"entries": entries}


def summarize(entries: list[dict]) -> dict:
    requests = [e for e in entries if e.get("kind") == "request"]
    responses = [e for e in entries if e.get("kind") == "response"]
    ds_query_reqs = [e for e in requests if "/api/ds/query" in (e.get("url") or "")]

    flags = {"contains_limit": False, "contains_offset": False, "contains_skip": False}
    samples = []
    for req in ds_query_reqs[:5]:
        body = req.get("postData") or ""
        low = body.lower()
        flags["contains_limit"] = flags["contains_limit"] or ("limit" in low or "$limit" in low)
        flags["contains_offset"] = flags["contains_offset"] or ("offset" in low)
        flags["contains_skip"] = flags["contains_skip"] or ("$skip" in low or '"skip"' in low)
        samples.append({"url": req.get("url"), "body_preview": body[:1200]})

    # Statuscodes für ds/query Responses
    ds_resp_status = []
    for resp in responses:
        if "/api/ds/query" in (resp.get("url") or ""):
            ds_resp_status.append(resp.get("status"))

    return {
        "api_request_count": len(requests),
        "api_response_count": len(responses),
        "ds_query_request_count": len(ds_query_reqs),
        "ds_query_response_statuses": ds_resp_status,
        "pagination_flags": flags,
        "ds_query_samples": samples,
    }


def main() -> int:
    username, password = load_credentials()
    driver = setup_driver()
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "login": {},
        "dashboard_url": DASHBOARD_UID_URL,
        "summary": {},
    }
    try:
        report["login"] = try_login(driver, username, password)
        if report["login"]["login_success"]:
            driver.get(DASHBOARD_UID_URL)
            time.sleep(10)
        raw = collect_network_logs(driver)
        report["summary"] = summarize(raw["entries"])
        report["summary"]["login_success"] = report["login"]["login_success"]
        report["summary"]["final_url"] = report["login"].get("final_url", "")
        report["summary"]["entry_count"] = len(raw["entries"])
        report["raw"] = raw
    finally:
        driver.quit()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUT_DIR / f"motocost_live_probe_{stamp}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "motocost_live_probe_latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"report_file={out_file}")
    print(f"login_success={report['login'].get('login_success')}")
    print(f"final_url={report['login'].get('final_url')}")
    print(f"api_requests={report['summary'].get('api_request_count')}")
    print(f"ds_query_requests={report['summary'].get('ds_query_request_count')}")
    print(f"pagination_flags={report['summary'].get('pagination_flags')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
