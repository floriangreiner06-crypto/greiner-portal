#!/usr/bin/env python3
"""
LDAP-Locosoft Matching Report - TAG 107
=======================================
Vergleicht Mitarbeiter zwischen AD und Locosoft.
Sendet Email-Report über Microsoft Graph API.

Konfiguration:
- LDAP: config/ldap_credentials.env
- Graph API: config/.env (GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET)
"""

import sqlite3, json, sys, os
from datetime import datetime
from pathlib import Path

# Pfade
BASE_PATH = '/opt/greiner-portal'
DB_PATH = f'{BASE_PATH}/data/greiner_controlling.db'
LDAP_CONFIG_PATH = f'{BASE_PATH}/config/ldap_credentials.env'
REPORT_EMAIL = 'florian.greiner@auto-greiner.de'
FROM_EMAIL = 'drive@auto-greiner.de'

# Graph Mail Connector importieren
sys.path.insert(0, f'{BASE_PATH}/api')
from graph_mail_connector import GraphMailConnector


def load_ldap_config():
    """Lädt LDAP-Config aus ldap_credentials.env"""
    config = {}
    with open(LDAP_CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config


def parse_subsidiary(company):
    """Parse Standort aus AD company-Attribut"""
    if not company: 
        return None, 'Nicht gepflegt'
    if 'deggendorf' in company.lower(): 
        return 1, 'Deggendorf'
    if 'landau' in company.lower(): 
        return 3, 'Landau'
    return None, f'Unbekannt ({company})'


def sub_name(s): 
    return {1: 'Deggendorf', 3: 'Landau'}.get(s, f'?({s})')


try:
    import ldap3
    LDAP_OK = True
except ImportError:
    LDAP_OK = False
    print("⚠️  ldap3 nicht installiert: pip install ldap3")


def get_loco(conn):
    """Hole aktive Locosoft-Mitarbeiter"""
    cur = conn.execute("""
        SELECT le.employee_number, le.name, le.subsidiary, gm.grp_code 
        FROM loco_employees le 
        LEFT JOIN loco_employees_group_mapping gm ON le.employee_number = gm.employee_number
        WHERE le.is_latest_record = 1 
          AND (le.leave_date IS NULL OR le.leave_date > date('now'))
          AND (le.termination_date IS NULL OR le.termination_date > date('now'))
    """)
    e = {}
    for r in cur.fetchall():
        if r[0] not in e:
            e[r[0]] = {'id': r[0], 'name': r[1], 'sub': r[2], 'standort': sub_name(r[2]), 'grp': set()}
        if r[3]:
            e[r[0]]['grp'].add(r[3])
    return e


def get_ldap_map(conn):
    """Hole LDAP-Employee-Mappings"""
    cur = conn.execute("""
        SELECT lem.ldap_username, lem.locosoft_id, e.first_name || ' ' || e.last_name 
        FROM ldap_employee_mapping lem 
        LEFT JOIN employees e ON lem.employee_id = e.id
    """)
    return {r[1]: {'user': r[0], 'loco_id': r[1], 'name': r[2]} for r in cur.fetchall()}


def get_ad(ldap_config):
    """Hole AD-User mit manager, department, company, proxyAddresses"""
    if not LDAP_OK:
        print("❌ ldap3 nicht verfügbar")
        return {}
    
    server_addr = ldap_config.get('LDAP_SERVER', 'srvdc01.auto-greiner.de')
    port = int(ldap_config.get('LDAP_PORT', '389'))
    use_ssl = ldap_config.get('LDAP_USE_SSL', 'False').lower() == 'true'
    bind_dn = ldap_config.get('LDAP_BIND_DN')
    bind_pw = ldap_config.get('LDAP_BIND_PASSWORD')
    base_dn = ldap_config.get('LDAP_BASE_DN', 'DC=auto-greiner,DC=de')
    
    print(f"   Server: {server_addr}:{port} (SSL: {use_ssl})")
    
    try:
        server = ldap3.Server(server_addr, port=port, use_ssl=use_ssl, get_info=ldap3.ALL)
        conn = ldap3.Connection(server, user=bind_dn, password=bind_pw, auto_bind=True)
        
        conn.search(
            search_base=f'OU=AUTO-GREINER,{base_dn}',
            search_filter='(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
            attributes=['sAMAccountName', 'displayName', 'department', 'manager', 'company', 'proxyAddresses', 'mail']
        )
        
        users = {}
        for entry in conn.entries:
            username = str(entry.sAMAccountName).lower()
            
            # Manager parsen
            mgr = str(entry.manager) if entry.manager else None
            mgr_name = None
            if mgr and 'CN=' in mgr and mgr != '[]':
                mgr_name = mgr.split('CN=')[1].split(',')[0]
            
            # Company/Standort
            company = str(entry.company) if entry.company and str(entry.company) != '[]' else None
            ad_sub, ad_standort = parse_subsidiary(company)
            
            # Department
            dept = str(entry.department) if entry.department and str(entry.department) != '[]' else None
            
            # proxyAddresses
            proxy_raw = entry.proxyAddresses if entry.proxyAddresses else []
            proxy_addresses = list(proxy_raw) if proxy_raw else []
            
            # mail
            mail = str(entry.mail) if entry.mail and str(entry.mail) != '[]' else None
            
            users[username] = {
                'user': username,
                'name': str(entry.displayName) if entry.displayName else None,
                'dept': dept,
                'mgr': mgr_name,
                'company': company,
                'ad_sub': ad_sub,
                'ad_st': ad_standort,
                'mail': mail,
                'proxyAddresses': proxy_addresses
            }
        
        conn.unbind()
        return users
        
    except Exception as ex:
        print(f"❌ LDAP-Fehler: {ex}")
        return {}


def generate_report(loco, ldap_map, ad):
    """Generiere Matching-Report"""
    r = {
        'ts': datetime.now().isoformat(),
        'sum': {'loco': len(loco), 'ldap': len(ldap_map), 'ad': len(ad)},
        'issues': {
            'no_ldap': [],
            'no_ad': [],
            'no_mgr': [],
            'no_dept': [],
            'no_company': [],
            'sub_mismatch': []
        },
        'proxy_addresses': {}  # Alle proxyAddresses für Debug
    }
    
    for eid, e in loco.items():
        if eid not in ldap_map:
            r['issues']['no_ldap'].append({
                'id': eid, 'name': e['name'], 
                'standort': e['standort'], 'grp': list(e['grp'])
            })
    
    for lid, m in ldap_map.items():
        a = ad.get(m['user'])
        lo = loco.get(lid)
        
        if not a:
            r['issues']['no_ad'].append({'user': m['user'], 'id': lid, 'name': m['name']})
            continue
        
        # proxyAddresses sammeln
        if a.get('proxyAddresses'):
            r['proxy_addresses'][m['user']] = {
                'name': a.get('name'),
                'mail': a.get('mail'),
                'proxyAddresses': a.get('proxyAddresses')
            }
        
        if not a.get('mgr'):
            r['issues']['no_mgr'].append({'user': m['user'], 'name': a.get('name'), 'id': lid})
        
        if not a.get('dept'):
            r['issues']['no_dept'].append({'user': m['user'], 'name': a.get('name')})
        
        if not a.get('company'):
            r['issues']['no_company'].append({
                'user': m['user'], 'name': a.get('name'),
                'loco_st': lo['standort'] if lo else '-'
            })
        elif lo and a.get('ad_sub') and a['ad_sub'] != lo['sub']:
            r['issues']['sub_mismatch'].append({
                'user': m['user'], 'name': a.get('name'),
                'ad_co': a['company'], 'ad_st': a['ad_st'], 'loco_st': lo['standort']
            })
    
    return r


def format_html(r):
    """Formatiere Report als HTML"""
    total = sum(len(v) for v in r['issues'].values())
    col = '#27ae60' if total == 0 else '#e74c3c' if total > 10 else '#f39c12'
    
    html = f"""<html><head><style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #c0392b; margin-top: 25px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .ok {{ color: #27ae60; background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; background: {col}; font-weight: bold; }}
        .proxy {{ font-size: 11px; color: #666; }}
    </style></head><body>
    <h1>🔄 LDAP ↔ Locosoft Matching Report</h1>
    <p>Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    <p><span class="badge">{total} Probleme gefunden</span></p>
    <p><strong>Übersicht:</strong> Locosoft: {r['sum']['loco']} | LDAP-Mappings: {r['sum']['ldap']} | AD-User: {r['sum']['ad']}</p>
    """
    
    titles = {
        'no_ldap': '❌ In Locosoft ohne LDAP-Mapping (kann sich nicht einloggen!)',
        'no_ad': '⚠️ LDAP-Mapping ohne AD-User (deaktiviert?)',
        'no_mgr': '⚠️ Kein Vorgesetzter in AD gepflegt',
        'no_dept': '⚠️ Keine Abteilung in AD gepflegt',
        'no_company': '⚠️ Keine Firma (Standort) in AD gepflegt',
        'sub_mismatch': '🔴 Standort-Mismatch (AD ≠ Locosoft)'
    }
    
    for k, items in r['issues'].items():
        if items:
            html += f"<h2>{titles[k]} ({len(items)})</h2>"
            html += "<table><tr><th>User/ID</th><th>Name</th><th>Details</th></tr>"
            
            for i in sorted(items, key=lambda x: x.get('name') or '')[:25]:
                if k == 'no_ldap':
                    det = f"{i['standort']} | {', '.join(i['grp'])}"
                elif k == 'sub_mismatch':
                    det = f"AD: {i['ad_st']} ({i['ad_co']}) vs Loco: {i['loco_st']}"
                elif k == 'no_company':
                    det = f"Locosoft: {i.get('loco_st', '-')}"
                else:
                    det = ''
                
                html += f"<tr><td>{i.get('user', i.get('id'))}</td><td>{i.get('name', '-')}</td><td>{det}</td></tr>"
            
            if len(items) > 25:
                html += f"<tr><td colspan='3'><em>... und {len(items) - 25} weitere</em></td></tr>"
            html += "</table>"
        else:
            html += f"<p class='ok'>✅ {titles[k].split('(')[0].strip()} - OK</p>"
    
    # proxyAddresses Sektion
    if r.get('proxy_addresses'):
        html += "<h2>📧 proxyAddresses (Debug-Info)</h2>"
        html += "<table><tr><th>User</th><th>Name</th><th>mail</th><th>proxyAddresses</th></tr>"
        for user, data in sorted(r['proxy_addresses'].items())[:30]:
            proxies = '<br>'.join(data.get('proxyAddresses', []))
            html += f"<tr><td>{user}</td><td>{data.get('name', '-')}</td><td>{data.get('mail', '-')}</td><td class='proxy'>{proxies}</td></tr>"
        if len(r['proxy_addresses']) > 30:
            html += f"<tr><td colspan='4'><em>... und {len(r['proxy_addresses']) - 30} weitere</em></td></tr>"
        html += "</table>"
    
    html += """
    <hr>
    <p style="color: #999; font-size: 11px;">
        GREINER PORTAL DRIVE - Automatischer Report<br>
        Script: /opt/greiner-portal/scripts/ldap_locosoft_matching_report.py
    </p>
    </body></html>
    """
    return html


def send_email(html, to):
    """Sende Email über Microsoft Graph API"""
    try:
        mail = GraphMailConnector()
        mail.send_mail(
            sender_email=FROM_EMAIL,
            to_emails=[to],
            subject=f"LDAP-Locosoft Report {datetime.now().strftime('%d.%m.%Y')}",
            body_html=html
        )
        print(f"✅ Email gesendet an {to}")
        return True
    except Exception as ex:
        print(f"❌ Email-Fehler: {ex}")
        return False


def main():
    print("=" * 50)
    print("LDAP ↔ Locosoft Matching Report")
    print("=" * 50)
    
    print("\n📥 Lade LDAP-Config...")
    ldap_config = load_ldap_config()
    print(f"   Server: {ldap_config.get('LDAP_SERVER')}")
    
    conn = sqlite3.connect(DB_PATH)
    
    print("📥 Lade Locosoft-Mitarbeiter...")
    loco = get_loco(conn)
    print(f"   {len(loco)} aktive Mitarbeiter")
    
    print("📥 Lade LDAP-Mappings...")
    ldap_map = get_ldap_map(conn)
    print(f"   {len(ldap_map)} Mappings")
    
    print("📥 Frage AD ab (inkl. proxyAddresses)...")
    ad = get_ad(ldap_config)
    print(f"   {len(ad)} AD-User")
    
    conn.close()
    
    print("\n📊 Generiere Report...")
    r = generate_report(loco, ldap_map, ad)
    
    print("\n" + "=" * 50)
    print("ZUSAMMENFASSUNG")
    print("=" * 50)
    for k, v in r['issues'].items():
        icon = "✅" if not v else "❌" if len(v) > 5 else "⚠️"
        print(f"{icon} {k}: {len(v)}")
    
    print(f"\n📧 proxyAddresses gefunden: {len(r.get('proxy_addresses', {}))}")
    
    html = format_html(r)
    
    if '--no-email' in sys.argv:
        f = f"/tmp/ldap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        open(f, 'w').write(html)
        print(f"\n📄 Report gespeichert: {f}")
    else:
        to = sys.argv[1] if len(sys.argv) > 1 and '@' in sys.argv[1] else REPORT_EMAIL
        send_email(html, to)
    
    Path(f'{BASE_PATH}/logs').mkdir(exist_ok=True)
    json_path = f"{BASE_PATH}/logs/ldap_matching_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_path, 'w') as f:
        json.dump(r, f, indent=2, default=list)
    print(f"📄 JSON: {json_path}")
    
    print("\n✅ Fertig!")


if __name__ == '__main__':
    main()
