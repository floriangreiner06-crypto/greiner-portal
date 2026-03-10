"""
ecoDMS API – Anbindung für Greiner Portal DRIVE
================================================
Suche nach Belegen (z. B. für Bankenspiegel-Kategorisierung).
Credentials: ECODMS_USER, ECODMS_PASSWORD aus config/.env (nicht versioniert).

Beleg-Download (aus Swagger/ecoDMS-Doku und get-dms-doc Quelle):
  GET {BASE_URL}/api/document/{docId}  mit Basic Auth → liefert die Datei (z. B. PDF).
  Im Portal wird ein Proxy verwendet, damit Nutzer ohne ecoDMS-Login den Beleg herunterladen können.

Referenzen:
- scripts/test_ecodms_api.py (Verbindung, searchDocumentsExtv2)
- docs/VFW_UPE_ANREICHERUNG_ECODMS.md (Werksrechnungen/UPE)
- docs/workstreams/integrations/CONTEXT.md (ecoDMS Abschnitt)
- get-dms-doc (Codeberg): URL = base + /api/document/ + id
"""

import os
import re
import requests
from typing import Optional, List, Any, Dict
from datetime import date, datetime

# Optional: dotenv aus Projekt-Code (wird von Flask/App bereits geladen)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_file = os.path.join(_project_root, "config", ".env")
if os.path.isfile(_env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

BASE_URL = os.environ.get("ECODMS_BASE_URL", "http://10.80.80.3:8180")
# Optional: Vollständige URL oder Pfad zur OpenAPI/Swagger-Spec (z. B. /v3/api-docs oder http://10.80.80.3:8180/custom/api-docs).
# Wenn gesetzt, wird zuerst diese URL verwendet; sonst Discovery über bekannte Pfade. Siehe docs/workstreams/controlling/ecodms/ECODMS_SWAGGER_EINBINDUNG.md
ECODMS_OPENAPI_SPEC_URL = (os.environ.get("ECODMS_OPENAPI_SPEC_URL") or "").strip() or None
# Ordner für Belege zu Bankbuchungen (evtl. später klären; Default wie Test-Skript Kontoauszüge)
FOLDER_BELEGE = os.environ.get("ECODMS_FOLDER_BELEGE", "1.2")
# Optional: ecoDMS-Feld-ID für „Bemerkung“ (Belegnummer z. B. Rechnung_DE2600038886_...). In ecoDMS unter Klassifizierung nachschauen (dyn_*-ID); ohne Setzung werden alle classifyAttributes trotzdem angezeigt (unter ihrer dyn_*-ID).
# Optional: ecoDMS-Feld-ID für „Kreditor“; wenn gesetzt und Kreditor aus Verwendungszweck erkennbar, wird danach gefiltert (weniger Treffer, bessere Zuordnung).
ECODMS_FIELD_KREDITOR_DEFAULT = "dyn_0_1517927104726"
# Optional: ecoDMS-Feld-ID für „Rechnungsnummer“/Belegnummer (z. B. DE2600038886). Default für Greiner-Archiv.
ECODMS_FIELD_RECHNUNGSNUMMER_DEFAULT = "dyn_1_1517843102084"
# Direkte ecoDMS-Document-URL (GET mit Basic Auth = Datei-Download). Für Portal: Proxy nutzen.
DOCUMENT_URL_TEMPLATE = "{{base}}/api/document/{{docId}}"

# Klassifizierungsfelder (Kontoauszüge/Belege) – aus test_ecodms_api.py / TAG 53
# Schlüssel = lesbarer Name für UI, Wert = ecoDMS-Feld-ID (classifyAttributes)
# Bemerkung (Belegnummer z. B. Rechnung_DE2600038886_...) optional per ECODMS_FIELD_BEMERKUNG
FIELD_MAP = {
    "bank": "dyn_4_1763372371642",
    "iban": "dyn_2_1763372371642",
    "bic": "dyn_0_1763389577199",
    "datum": "dyn_1_1763372371642",
    "endsaldo": "dyn_0_1763372371641",
    "belegdatum": "dyn_0_1517843102084",
}
FIELD_LABELS = {
    "belegdatum": "Belegdatum",
    "datum": "Datum",
    "bank": "Bank",
    "iban": "IBAN",
    "bic": "BIC",
    "endsaldo": "Endsaldo",
    "bemerkung": "Bemerkung",
}


def _get_field_map_with_bemerkung() -> dict:
    """FIELD_MAP inkl. optionaler Bemerkung aus ECODMS_FIELD_BEMERKUNG."""
    m = dict(FIELD_MAP)
    bemerkung_id = (os.environ.get("ECODMS_FIELD_BEMERKUNG") or "").strip()
    if bemerkung_id:
        m["bemerkung"] = bemerkung_id
    return m


def _classify_attributes_to_display(attrs: dict) -> dict:
    """Mappt ecoDMS classifyAttributes auf lesbare Attribute; unbekannte Keys werden mit angezeigt."""
    out = {}
    field_map = _get_field_map_with_bemerkung()
    for key, field_id in field_map.items():
        val = (attrs or {}).get(field_id)
        if val is not None and str(val).strip() != "":
            label = FIELD_LABELS.get(key, key)
            out[label] = str(val).strip()
    for field_id, val in (attrs or {}).items():
        if field_id in field_map.values():
            continue
        if val is not None and str(val).strip() != "":
            out[field_id] = str(val).strip()
    return out


def _kreditor_aus_transaktionstext(text: Optional[str]) -> Optional[str]:
    """Erkennt Kreditor aus Transaktionstext (nach LASTSCHRIFT/GUTSCHRIFT oder erstes namenähnliches Segment)."""
    if not text or not str(text).strip():
        return None
    t = str(text).strip()
    # 1) Klassisch: nach LASTSCHRIFT/GUTSCHRIFT bis zu Zahl, IBAN, MANDAT, REF, Doppelpunkt oder Ende
    m = re.search(
        r"(?:LASTSCHRIFT|GUTSCHRIFT)\s+([A-Za-z0-9.\s&\-\']+?)(?=\s+[A-Z]{2,}\s*/\s*|\s+MANDAT|\s+REF\s|\s+[0-9]{5,}|\s*[;:]|$)",
        t,
        re.IGNORECASE,
    )
    if m:
        k = m.group(1).strip()
        if len(k) >= 3 and not k.isdigit():
            return k
    # 2) Auftraggeber: / Empfänger: / Zahlung an:
    m = re.search(r"(?:Auftraggeber|Empfänger|Zahlung an|Kreditor)\s*[:\-]\s*([A-Za-z0-9.\s&\-\']+)", t, re.IGNORECASE)
    if m:
        k = m.group(1).strip()
        if len(k) >= 2:
            return k
    # 3) Erste längere Wortfolge (2+ Wörter), die wie ein Name/Unternehmen aussieht (Buchstaben, Punkte, &, -)
    m = re.search(r"^([A-Za-z0-9.\s&\-\']{4,}?)(?=\s+[A-Z]{2,}\s|\s+[0-9]{5,}|\s*$)", t)
    if m:
        k = m.group(1).strip()
        if len(k) >= 4 and " " in k and not k.isdigit():
            return k
    return None


def _belegnummer_aus_referenz(text: Optional[str]) -> Optional[str]:
    """Extrahiert eine Beleg-/Rechnungsnummer aus dem Verwendungszweck (z. B. DE2600038886 oder längere Zahlen)."""
    if not text or not str(text).strip():
        return None
    t = str(text).strip()
    m = re.search(r"DE\d{8,}", t, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    m = re.search(r"\d{6,}", t)
    if m:
        return m.group(0)
    return None


def _referenz_tokens(text: Optional[str]) -> List[str]:
    """Extrahiert Such-Token aus Transaktionstext (z. B. Belegnummer DE2600038886 oder längere Zahlen)."""
    if not text or not str(text).strip():
        return []
    t = str(text).strip()
    tokens = []
    for m in re.finditer(r"DE\d{8,}", t, re.IGNORECASE):
        tokens.append(m.group(0).upper())
    for m in re.finditer(r"\d{6,}", t):
        tokens.append(m.group(0))
    if not tokens:
        words = re.findall(r"\S{4,}", t)
        tokens.extend(words[:5])
    return tokens


def _doc_matches_referenz(display_attrs: dict, tokens: List[str]) -> bool:
    """Prüft, ob einer der Referenz-Token in den (Anzeige-)Attributen vorkommt."""
    if not tokens:
        return False
    combined = " ".join(str(v) for v in (display_attrs or {}).values()).upper()
    for tok in tokens:
        if tok.upper() in combined:
            return True
    return False


def _get_auth() -> Optional[tuple]:
    user = os.environ.get("ECODMS_USER", "").strip()
    password = os.environ.get("ECODMS_PASSWORD", "").strip()
    if user and password:
        return (user, password)
    return None


def document_url_ecodms(doc_id: str) -> str:
    """Direkte ecoDMS-URL zum Dokument (GET /api/document/{id} mit Basic Auth = Datei)."""
    return DOCUMENT_URL_TEMPLATE.replace("{{base}}", BASE_URL.rstrip("/")).replace("{{docId}}", str(doc_id))


def get_document_stream(doc_id: str):
    """
    Lädt ein Dokument von ecoDMS (GET /api/document/{id}) und streamt die Antwort.
    Yield: (bytes chunk, content_type aus Header).
    Bei Fehler: (None, None), Fehlerdetails per side-effect loggen oder Exception.
    """
    auth = _get_auth()
    if not auth:
        return None, None
    url = document_url_ecodms(doc_id)
    try:
        r = requests.get(url, auth=auth, timeout=30, stream=True)
        if r.status_code != 200:
            return None, None
        content_type = r.headers.get("Content-Type") or "application/octet-stream"
        return r.iter_content(chunk_size=65536), content_type
    except requests.RequestException:
        return None, None


def search_belege(
    buchungsdatum: Optional[date] = None,
    betrag: Optional[float] = None,
    referenz: Optional[str] = None,
    max_count: int = 40,
) -> Dict[str, Any]:
    """
    Sucht im ecoDMS nach Belegen zum Buchungsdatum (ohne Filter nach Transaktionstext).

    Ansatz: Nur Belegdatum + Ordner als Filter. Der Nutzer wählt den passenden Beleg manuell.
    Transaktionstext (referenz) wird nur noch als Hinweis mitgeliefert und ggf. zur Hervorhebung
    genutzt (vorgeschlagen), wenn ein Beleg die Referenz in den Attributen enthält.

    Parameter:
        buchungsdatum: Datum der Buchung → Filter Belegdatum in ecoDMS.
        betrag: ungenutzt (ecoDMS-Felder je Archiv unterschiedlich).
        referenz: Optional; nur für Anzeige/Hinweis und optionales „Vorgeschlagen“ (wenn in Attributen).
    """
    auth = _get_auth()
    if not auth:
        return {
            "success": False,
            "documents": [],
            "error": "ecoDMS-Zugangsdaten nicht konfiguriert (ECODMS_USER/ECODMS_PASSWORD).",
        }

    kreditor_vermutet = _kreditor_aus_transaktionstext(referenz) if referenz else None
    referenz_tokens = _referenz_tokens(referenz) if referenz else []

    folder_id = resolve_folder_id(FOLDER_BELEGE)
    datum_str = None
    if buchungsdatum:
        datum_str = buchungsdatum.isoformat() if hasattr(buchungsdatum, "isoformat") else str(buchungsdatum)

    # Nur Ordner + Belegdatum – kein Filter nach Kreditor/Rechnungsnummer (Transaktionstext-Ansatz verworfen).
    def _do_search(sfilter: list, max_docs: Optional[int] = None) -> list:
        limit = max_docs if max_docs is not None else min(max_count, 50)
        payload = {"searchFilter": sfilter, "maxDocumentCount": limit}
        try:
            rr = requests.post(
                f"{BASE_URL.rstrip('/')}/api/searchDocumentsExtv2",
                json=payload,
                headers={"Content-Type": "application/json", "accept": "application/json"},
                auth=auth,
                timeout=15,
            )
        except requests.RequestException:
            return []
        if rr.status_code != 200:
            return []
        try:
            data = rr.json()
        except Exception:
            return []
        return data if isinstance(data, list) else []

    # Suche: konfigurierter Ordner + Belegdatum
    search_filter = [
        {"classifyAttribute": "folderonly", "searchValue": folder_id, "searchOperator": "="}
    ]
    if datum_str:
        search_filter.append({
            "classifyAttribute": FIELD_MAP["belegdatum"],
            "searchValue": datum_str,
            "searchOperator": "=",
        })
    docs = _do_search(search_filter)
    existing_ids = {str(d.get("docId") or d.get("clDocId")) for d in docs if (d.get("docId") or d.get("clDocId"))}

    # Zusätzlich Ordner „Buchhaltung“ (1) zum gleichen Datum
    if folder_id != "1":
        fallback_filter = [
            {"classifyAttribute": "folderonly", "searchValue": "1", "searchOperator": "="}
        ]
        if datum_str:
            fallback_filter.append({
                "classifyAttribute": FIELD_MAP["belegdatum"],
                "searchValue": datum_str,
                "searchOperator": "=",
            })
        for d in _do_search(fallback_filter):
            did = d.get("docId") or d.get("clDocId")
            if did and str(did) not in existing_ids:
                docs.append(d)
                existing_ids.add(str(did))

    if not isinstance(docs, list):
        docs = []

    download_path_prefix = "/api/bankenspiegel/transaktionen/ecodms/document"
    out = []
    for d in docs:
        doc_id = d.get("docId") or d.get("clDocId")
        if not doc_id:
            continue
        raw_attrs = d.get("classifyAttributes") or {}
        display_attrs = _classify_attributes_to_display(raw_attrs)
        vorgeschlagen = bool(referenz_tokens and _doc_matches_referenz(display_attrs, referenz_tokens))
        out.append({
            "docId": doc_id,
            "clDocId": d.get("clDocId"),
            "archiveName": d.get("archiveName"),
            "viewUrl": f"{download_path_prefix}/{doc_id}/download",
            "classifyAttributes": raw_attrs,
            "attributes": display_attrs,
            "vorgeschlagen": vorgeschlagen,
        })
    out.sort(key=lambda x: (not x.get("vorgeschlagen"), x.get("docId") or 0))

    return {
        "success": True,
        "documents": out,
        "kreditor_vermutet": kreditor_vermutet,
        "referenz_hinweis": (referenz or "").strip()[:200] if referenz else None,
        "buchungsdatum": datum_str,
        "error": None,
    }


# Cache für Ordnerliste (API nicht bei jeder Suche belasten)
_folders_cache: Optional[List[Dict[str, Any]]] = None
_folders_cache_time: Optional[float] = None
_FOLDERS_CACHE_SECONDS = 300  # 5 Minuten

# Cache für OpenAPI-Spec (Swagger) – zentrale Quelle für Endpunkte und Schemas
_openapi_spec_cache: Optional[Dict[str, Any]] = None
_openapi_spec_cache_time: Optional[float] = None
_OPENAPI_CACHE_SECONDS = 600  # 10 Minuten
_DISCOVERY_PATHS = (
    "/v3/api-docs",
    "/v2/api-docs",
    "/api-docs",
    "/api/v3/api-docs",
    "/api/v2/api-docs",
    "/swagger-ui/v3/api-docs",
    "/swagger/v3/api-docs",
)


def _normalize_folders_response(data: Any) -> List[Dict[str, Any]]:
    """Mappt verschiedene ecoDMS-Antwortformate auf einheitlich [{"id": str, "name": str}, ...]."""
    out: List[Dict[str, Any]] = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("folders") or data.get("folder") or data.get("data") or data.get("children") or []
        if not isinstance(items, list) and isinstance(data.get("id"), (str, int)):
            items = [data]
        elif not isinstance(items, list):
            items = []
    else:
        return []
    for item in items:
        if not isinstance(item, dict):
            continue
        fid = item.get("id") or item.get("oId") or item.get("folderId") or item.get("folderID") or item.get("folder_id")
        name = item.get("name") or item.get("foldername") or item.get("folderName") or item.get("title") or item.get("label") or ""
        if fid is not None and str(fid).strip() != "":
            out.append({"id": str(fid).strip(), "name": str(name).strip() if name else str(fid)})
    return out


def _flatten_folder_tree(node: Dict[str, Any], prefix: str = "") -> List[Dict[str, Any]]:
    """Flacht einen Ordnerbaum (children) zu einer Liste mit id/name ab; name inkl. Pfad für Eindeutigkeit."""
    out: List[Dict[str, Any]] = []
    fid = node.get("id") or node.get("oId") or node.get("folderId") or node.get("folderID") or node.get("folder_id")
    name = (node.get("name") or node.get("foldername") or node.get("folderName") or node.get("title") or node.get("label") or str(fid) or "").strip()
    if fid is not None and str(fid).strip() != "":
        display_name = (prefix + " " + name).strip() if prefix else name
        out.append({"id": str(fid).strip(), "name": display_name or str(fid)})
    children = node.get("children") or node.get("subFolders") or node.get("childFolders") or []
    if not isinstance(children, list):
        children = []
    sub_prefix = (prefix + " / " + name).strip() if name else prefix
    for ch in children:
        if isinstance(ch, dict):
            out.extend(_flatten_folder_tree(ch, sub_prefix))
    return out


def get_openapi_spec(force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    Lädt die OpenAPI/Swagger-Spec von ecoDMS (zentral, gecacht).
    - Wenn ECODMS_OPENAPI_SPEC_URL gesetzt: diese URL (vollständig oder Pfad relativ zu BASE_URL).
    - Sonst: Discovery über bekannte Pfade und /swagger-resources.
    Rückgabe: Spec-Dict oder None. Cache 10 Minuten.
    """
    global _openapi_spec_cache, _openapi_spec_cache_time
    auth = _get_auth()
    base = BASE_URL.rstrip("/")
    now = datetime.now().timestamp()
    if not force_refresh and _openapi_spec_cache is not None and _openapi_spec_cache_time is not None:
        if (now - _openapi_spec_cache_time) < _OPENAPI_CACHE_SECONDS:
            return _openapi_spec_cache

    headers = {"accept": "application/json"}
    spec_url: Optional[str] = None

    if ECODMS_OPENAPI_SPEC_URL:
        raw = ECODMS_OPENAPI_SPEC_URL
        if raw.startswith("http://") or raw.startswith("https://"):
            spec_url = raw
        else:
            spec_url = base + ("/" if not raw.startswith("/") else "") + raw.lstrip("/")

    if spec_url:
        try:
            r = requests.get(spec_url, auth=auth, timeout=15, headers=headers)
            if r.status_code == 200:
                _openapi_spec_cache = r.json()
                _openapi_spec_cache_time = now
                return _openapi_spec_cache
        except Exception:
            pass
        _openapi_spec_cache = None
        _openapi_spec_cache_time = None
        return None

    for doc_path in _DISCOVERY_PATHS:
        try:
            r = requests.get(base + doc_path, auth=auth, timeout=10, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and (data.get("paths") or data.get("openapi") or data.get("swagger")):
                    _openapi_spec_cache = data
                    _openapi_spec_cache_time = now
                    return _openapi_spec_cache
        except Exception:
            continue

    try:
        r = requests.get(base + "/swagger-resources", auth=auth, timeout=10, headers=headers)
        if r.status_code == 200:
            resources = r.json()
            if isinstance(resources, list):
                for res in resources:
                    if not isinstance(res, dict):
                        continue
                    loc = res.get("location") or res.get("url")
                    if not loc:
                        continue
                    if loc.startswith("http"):
                        url = loc
                    else:
                        url = base + ("/" if not loc.startswith("/") else "") + loc.lstrip("/")
                    r2 = requests.get(url, auth=auth, timeout=10, headers=headers)
                    if r2.status_code == 200:
                        data = r2.json()
                        if isinstance(data, dict) and (data.get("paths") or data.get("openapi") or data.get("swagger")):
                            _openapi_spec_cache = data
                            _openapi_spec_cache_time = now
                            return _openapi_spec_cache
    except Exception:
        pass

    _openapi_spec_cache = None
    _openapi_spec_cache_time = None
    return None


def _get_openapi_spec(auth: tuple, base: str) -> Optional[Dict[str, Any]]:
    """Liefert die gecachte OpenAPI-Spec (für Abwärtskompatibilität)."""
    return get_openapi_spec()


def _folder_paths_from_spec(spec: Dict[str, Any]) -> List[str]:
    """Ermittelt aus der OpenAPI-Spec alle GET-Pfade, die Ordner listen (folder/archive)."""
    paths = spec.get("paths") or {}
    candidates: List[str] = []
    for path_key, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        get_spec = path_item.get("get")
        if not get_spec:
            continue
        pl = path_key.lower()
        if "folder" in pl or "ordner" in pl or ("archive" in pl and "folders" in pl):
            candidates.append(path_key)
    return sorted(candidates)


def _resolve_schema_ref(spec: Dict[str, Any], ref: str) -> Optional[Dict[str, Any]]:
    """Löst $ref in components/schemas auf."""
    if not ref or not ref.startswith("#/components/schemas/"):
        return None
    key = ref.replace("#/components/schemas/", "")
    return ((spec.get("components") or {}).get("schemas") or {}).get(key)


def _folders_from_response(data: Any, spec: Optional[Dict[str, Any]] = None, response_schema: Any = None) -> List[Dict[str, Any]]:
    """Extrahiert flache Ordnerliste aus API-Antwort; unterstützt auch Baum (children) und verschiedene Keys."""
    if isinstance(data, list):
        flat: List[Dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict) and (item.get("children") or item.get("subFolders") or item.get("childFolders")):
                flat.extend(_flatten_folder_tree(item))
            else:
                flat.extend(_normalize_folders_response([item]))
        return flat
    if isinstance(data, dict) and (data.get("children") or data.get("subFolders") or data.get("childFolders")):
        return _flatten_folder_tree(data)
    return _normalize_folders_response(data)


def get_folders() -> Dict[str, Any]:
    """
    Liest die Ordnerstruktur von ecoDMS per API.
    Zuerst wird die OpenAPI/Swagger-Spec (v3/api-docs) geladen; daraus werden alle GET-Pfade
    mit "folder" oder "archive" ermittelt und nacheinander aufgerufen. Antwort wird einheitlich
    in [{"id", "name"}, ...] gemappt (inkl. hierarchische Struktur → flach).
    Rückgabe: { "success": bool, "folders": [ {"id": str, "name": str}, ... ], "error": str | None }
    """
    global _folders_cache, _folders_cache_time
    auth = _get_auth()
    if not auth:
        return {"success": False, "folders": [], "error": "ecoDMS-Zugangsdaten nicht konfiguriert."}
    base = BASE_URL.rstrip("/")
    now = datetime.now().timestamp()
    if _folders_cache is not None and _folders_cache_time is not None and (now - _folders_cache_time) < _FOLDERS_CACHE_SECONDS:
        return {"success": True, "folders": _folders_cache, "error": None}

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    folders: List[Dict[str, Any]] = []

    # 1) Swagger/OpenAPI zuerst (wenn Spec geladen werden kann – konfigurierte URL oder Discovery)
    spec = get_openapi_spec()
    if spec:
        path_list = _folder_paths_from_spec(spec)
        # Gibt es einen Pfad, der Archive listet? (für /api/archive/{archiveId}/folders)
        archives_path = None
        for p in (spec.get("paths") or {}).keys():
            pk = p.lower()
            if ("archive" in pk and "folder" not in pk and "{" not in p) or pk in ("/api/archives", "/api/archive"):
                archives_path = p
                break
        archive_ids: List[str] = []
        if archives_path:
            try:
                ra = requests.get(base + archives_path, auth=auth, timeout=10, headers=headers)
                if ra.status_code == 200:
                    arch_data = ra.json()
                    if isinstance(arch_data, list):
                        for a in arch_data:
                            aid = a.get("id") or a.get("archiveId") or a.get("archiveID") if isinstance(a, dict) else None
                            if aid is not None:
                                archive_ids.append(str(aid))
                    elif isinstance(arch_data, dict):
                        for a in (arch_data.get("archives") or arch_data.get("data") or [arch_data]):
                            if isinstance(a, dict):
                                aid = a.get("id") or a.get("archiveId") or a.get("archiveID")
                                if aid is not None:
                                    archive_ids.append(str(aid))
            except Exception:
                pass
        if not archive_ids:
            archive_ids = ["0", "1"]

        for path_key in path_list:
            path_item = (spec.get("paths") or {}).get(path_key) or {}
            params_spec = path_item.get("get", {}).get("parameters") or []
            path_params = [p for p in params_spec if isinstance(p, dict) and p.get("in") == "path"]
            if not path_params:
                url_path = path_key
                try:
                    r = requests.get(base + url_path, auth=auth, timeout=15, headers=headers)
                    if r.status_code == 200:
                        folders = _folders_from_response(r.json(), spec)
                        if folders:
                            _folders_cache = folders
                            _folders_cache_time = now
                            return {"success": True, "folders": folders, "error": None}
                except Exception:
                    pass
                continue
            for aid in archive_ids:
                url_path = path_key
                for p in path_params:
                    name = p.get("name")
                    if name and "{" + name + "}" in url_path:
                        url_path = url_path.replace("{" + name + "}", aid)
                try:
                    r = requests.get(base + url_path, auth=auth, timeout=15, headers=headers)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    folders = _folders_from_response(data, spec)
                    if folders:
                        _folders_cache = folders
                        _folders_cache_time = now
                        return {"success": True, "folders": folders, "error": None}
                except Exception:
                    continue

    # 2) Fallback: bekannte ecoDMS-Pfade (funktioniert auch ohne Swagger, z. B. wenn Spec 404)
    for path in ("/api/folders", "/api/archive/folders", "/api/archives/folders", "/api/folder/tree"):
        try:
            r = requests.get(base + path, auth=auth, timeout=10, headers=headers)
            if r.status_code == 200:
                data = r.json()
                folders = _folders_from_response(data)
                if folders:
                    _folders_cache = folders
                    _folders_cache_time = now
                    return {"success": True, "folders": folders, "error": None}
        except Exception:
            continue

    return {"success": False, "folders": [], "error": "Kein Ordner-Endpunkt gefunden (OpenAPI-Spec oder api/folders)."}


def resolve_folder_id(folder_config: str) -> str:
    """
    Gibt die zu verwendende Ordner-ID zurück.
    Wenn folder_config wie eine ID aussieht (Ziffern/Punkte, z. B. 1.2 oder 5), wird sie unverändert genutzt.
    Sonst wird die Ordnerliste per API geholt und nach Namen (case-insensitive) gesucht.
    """
    cfg = (folder_config or "").strip()
    if not cfg:
        return FOLDER_BELEGE
    if re.match(r"^[\d.]+$", cfg):
        return cfg
    result = get_folders()
    if not result.get("success") or not result.get("folders"):
        return cfg
    cfg_lower = cfg.lower()
    for f in result["folders"]:
        if (f.get("name") or "").strip().lower() == cfg_lower:
            return str(f.get("id", cfg))
    return cfg


def check_connection() -> Dict[str, Any]:
    """
    Prüft die Verbindung zu ecoDMS (GET /api/test).
    Rückgabe: { "ok": bool, "message": str }
    """
    try:
        r = requests.get(f"{BASE_URL.rstrip('/')}/api/test", timeout=5)
        return {"ok": r.status_code == 200, "message": r.text[:200] if r.text else ""}
    except Exception as e:
        return {"ok": False, "message": str(e)}
