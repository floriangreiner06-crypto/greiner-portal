"""
Gudat DA REST API – OAuth-Client mit Token-Cache.

Nutzt api.werkstattplanung.net/da/v1 mit OAuth2 (Password Grant).
Credentials aus config/credentials.json unter external_systems.gudat.centers[center].
Token wird pro Center gecacht (TTL 50 Min), bei 401 einmalig Refresh/Neuanforderung.

Verwendung:
    from api.gudat_da_client import gudat_da_request, get_gudat_da_token

    token, err = get_gudat_da_token("deggendorf")
    data, err = gudat_da_request("GET", "/resources", "deggendorf")
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
TOKEN_CACHE_TTL_SECONDS = 50 * 60  # 50 Minuten
_token_cache: Dict[str, Dict] = {}  # center -> { "token", "expires_at" }


def _load_da_config() -> Optional[Dict]:
    """Lädt gudat.api_base_url, group, centers aus credentials.json."""
    if not os.path.isfile(CREDENTIALS_PATH):
        return None
    try:
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.warning("Gudat DA Config nicht lesbar: %s", e)
        return None
    gudat = data.get('external_systems', {}).get('gudat', {})
    base_url = (gudat.get('api_base_url') or '').rstrip('/')
    group = gudat.get('group') or 'greiner'
    centers = gudat.get('centers') or {}
    if not base_url or not centers:
        return None
    return {'base_url': base_url, 'group': group, 'centers': centers}


def get_gudat_da_token(center: str) -> Tuple[Optional[str], Optional[str]]:
    """
    OAuth-Token für das angegebene Center (deggendorf, landau).
    Nutzt Cache; bei Ablauf oder 401 wird neu angefordert.

    Returns:
        (token, None) bei Erfolg
        (None, error_message) bei Fehler
    """
    global _token_cache
    now = time.time()
    entry = _token_cache.get(center)
    if entry and entry.get('expires_at', 0) > now + 60:
        return entry.get('token'), None

    cfg = _load_da_config()
    if not cfg:
        return None, "Gudat DA Config nicht gefunden (api_base_url, centers)"
    if center not in cfg['centers']:
        return None, f"Center '{center}' nicht in gudat.centers konfiguriert"
    c = cfg['centers'][center]
    client_id = (c.get('client_id') or '').strip()
    client_secret = (c.get('client_secret') or '').strip()
    username = (c.get('username') or '').strip()
    password = (c.get('password') or '').strip()
    if not all([client_id, client_secret, username, password]) or 'PLACEHOLDER' in (client_id + client_secret):
        return None, f"Gudat DA Credentials für Center '{center}' unvollständig oder Platzhalter"

    try:
        import requests
    except ImportError:
        return None, "requests nicht installiert"

    url = f"{cfg['base_url']}/oauth/token"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'group': cfg['group'],
        'center': center,
    }
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    try:
        r = requests.post(url, headers=headers, data=data, timeout=15)
    except requests.RequestException as e:
        return None, str(e)
    if r.status_code != 200:
        return None, f"Token fehlgeschlagen: {r.status_code} {r.text[:300]}"
    body = r.json()
    token = body.get('access_token') or body.get('token')
    if not token:
        return None, "Kein access_token in Response"
    expires_in = body.get('expires_in', 3600)
    _token_cache[center] = {
        'token': token,
        'expires_at': now + min(expires_in, TOKEN_CACHE_TTL_SECONDS),
    }
    logger.debug("Gudat DA Token für %s gecacht", center)
    return token, None


def invalidate_token(center: str) -> None:
    """Token für Center aus Cache entfernen (z.B. nach 401)."""
    global _token_cache
    _token_cache.pop(center, None)


def gudat_da_request(
    method: str,
    path: str,
    center: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict] = None,
    retry_on_401: bool = True,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Führt einen Request an die DA REST API aus (group/center/Authorization gesetzt).

    path: z.B. "/resources", "/service_events"
    params: Query-Parameter (z.B. filter[inRange]=date,date)
    json_data: Body für POST/PATCH

    Returns:
        (response_json, None) bei Erfolg (bei 2xx)
        (None, error_message) bei Fehler
    """
    token, err = get_gudat_da_token(center)
    if err:
        return None, err
    cfg = _load_da_config()
    if not cfg:
        return None, "Gudat DA Config nicht gefunden"
    url = cfg['base_url'].rstrip('/') + path
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'group': cfg['group'],
        'center': center,
        'Authorization': f'Bearer {token}',
    }
    try:
        import requests
    except ImportError:
        return None, "requests nicht installiert"
    try:
        r = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=30,
        )
    except requests.RequestException as e:
        return None, str(e)

    if r.status_code == 401 and retry_on_401:
        invalidate_token(center)
        token2, err2 = get_gudat_da_token(center)
        if not err2 and token2 != token:
            return gudat_da_request(method, path, center, params=params, json_data=json_data, retry_on_401=False)
    if r.status_code >= 400:
        return None, f"API {r.status_code}: {r.text[:400]}"
    if not r.content:
        return {}, None
    try:
        return r.json(), None
    except Exception as e:
        return None, f"Response kein JSON: {e}"
