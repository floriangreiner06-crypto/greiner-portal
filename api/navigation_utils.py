"""
Navigation Utilities - TAG 190
Zentrale Funktionen für DB-basierte Navigation
"""
from flask_login import current_user
from flask import has_request_context, g
from api.db_connection import get_db
from api.db_utils import rows_to_list


def get_navigation_for_user():
    """
    Lädt Navigation-Items für aktuellen User
    Gefiltert nach Feature-Zugriff und Rollen
    
    TAG 192: ROLLBACK - Zurück zur Python-Filterung (SQL-Filterung verursachte Performance-Probleme)
    TAG 192: CACHING - Per-Request-Cache in Flask g (verhindert mehrfaches Laden)
    """
    # TAG 192: Per-Request-Cache (verhindert mehrfaches Laden pro Request)
    if has_request_context():
        if hasattr(g, 'navigation_items'):
            return g.navigation_items
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Alle aktiven Items laden
        cursor.execute('''
            SELECT 
                id,
                parent_id,
                label,
                url,
                icon,
                order_index,
                requires_feature,
                role_restriction,
                is_dropdown,
                is_header,
                is_divider,
                active,
                category
            FROM navigation_items
            WHERE active = true
            ORDER BY order_index, label
        ''')
        
        all_items = rows_to_list(cursor.fetchall())
        conn.close()
        
        # Effektives requires_feature: Einträge ohne eigenes Feature erben vom Eltern-Menü
        # (damit alle Menüs rechtsbeschränkt sind; z.B. Werkstatt-Kinder nur bei Berechtigung)
        all_items_by_id = {item['id']: item for item in all_items}
        effective_feature_by_id = {}
        for item in all_items:
            effective_feature_by_id[item['id']] = (item.get('requires_feature') or '').strip() or None
        changed = True
        while changed:
            changed = False
            for item in all_items:
                if effective_feature_by_id.get(item['id']):
                    continue
                pid = item.get('parent_id')
                if pid and pid in effective_feature_by_id and effective_feature_by_id.get(pid):
                    effective_feature_by_id[item['id']] = effective_feature_by_id[pid]
                    changed = True
        
        # Filter: Nur Items auf die User Zugriff hat (Python-Filterung)
        filtered_items = []
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') if hasattr(current_user, 'portal_role') else 'mitarbeiter'
        
        for item in all_items:
            # Prüfe Feature-Zugriff (effektiv: eigenes oder geerbtes Feature)
            eff = effective_feature_by_id.get(item['id'])
            if eff:
                if not (hasattr(current_user, 'can_access_feature') and 
                        current_user.can_access_feature(eff)):
                    continue
            
            # Prüfe Rollen-Restriktion (einzelne Rolle oder kommasep. Liste)
            if item.get('role_restriction'):
                allowed_roles = [r.strip() for r in str(item['role_restriction']).split(',') if r.strip()]
                if user_role not in allowed_roles:
                    # Admin sieht alles
                    if not (hasattr(current_user, 'can_access_feature') and 
                            current_user.can_access_feature('admin')):
                        continue
            
            filtered_items.append(item)
        
        # Eltern von sichtbaren Items nachziehen (damit z.B. "Werkstatt" erscheint,
        # wenn User nur Feature "fahrzeuganlage" hat, nicht "aftersales")
        all_items_by_id = {item['id']: item for item in all_items}
        filtered_ids = {item['id'] for item in filtered_items}
        while True:
            to_add = []
            for item in filtered_items:
                pid = item.get('parent_id')
                if pid and pid not in filtered_ids and pid in all_items_by_id:
                    to_add.append(all_items_by_id[pid])
                    filtered_ids.add(pid)
            if not to_add:
                break
            filtered_items.extend(to_add)
        
        # Struktur als Baum aufbauen
        items_by_id = {item['id']: item for item in filtered_items}
        root_items = []
        
        for item in filtered_items:
            if item['parent_id']:
                parent = items_by_id.get(item['parent_id'])
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(item)
            else:
                root_items.append(item)
        
        # Rekursiv: Dropdowns ohne sichtbare Kinder ausblenden (auf allen Ebenen)
        def remove_empty_dropdowns(items):
            result = []
            for item in list(items):
                if item.get('is_dropdown') and item.get('children'):
                    item['children'] = remove_empty_dropdowns(item['children'])
                if item.get('is_dropdown') and len(item.get('children', [])) == 0:
                    continue  # Leeres Dropdown weglassen
                result.append(item)
            return result
        
        root_items = remove_empty_dropdowns(root_items)
        
        # TAG 192: In Flask g speichern (Per-Request-Cache)
        if has_request_context():
            g.navigation_items = root_items
        
        return root_items
        
    except Exception as e:
        import traceback
        print(f"⚠️ Fehler beim Laden der Navigation: {e}")
        traceback.print_exc()
        return []  # Fallback: Leere Liste


def get_navigation_for_role(role: str, allowed_features: set):
    """
    Lädt Navigation-Items gefiltert für eine gegebene Rolle und Feature-Menge.
    Für Admin-Anzeige „Rechte & Navi für User“ – ohne current_user.
    """
    if allowed_features is None:
        allowed_features = set()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, parent_id, label, url, icon, order_index,
                   requires_feature, role_restriction, is_dropdown, is_header, is_divider, active, category
            FROM navigation_items
            WHERE active = true
            ORDER BY order_index, label
        ''')
        all_items = rows_to_list(cursor.fetchall())
        conn.close()

        all_items_by_id = {item['id']: item for item in all_items}
        effective_feature_by_id = {}
        for item in all_items:
            effective_feature_by_id[item['id']] = (item.get('requires_feature') or '').strip() or None
        changed = True
        while changed:
            changed = False
            for item in all_items:
                if effective_feature_by_id.get(item['id']):
                    continue
                pid = item.get('parent_id')
                if pid and pid in effective_feature_by_id and effective_feature_by_id.get(pid):
                    effective_feature_by_id[item['id']] = effective_feature_by_id[pid]
                    changed = True

        filtered_items = []
        is_admin = role == 'admin'
        for item in all_items:
            eff = effective_feature_by_id.get(item['id'])
            if eff:
                if not is_admin and eff not in allowed_features:
                    continue
            if item.get('role_restriction'):
                allowed_roles = [r.strip() for r in str(item['role_restriction']).split(',') if r.strip()]
                if role not in allowed_roles and not is_admin:
                    continue
            filtered_items.append(item)

        filtered_ids = {item['id'] for item in filtered_items}
        while True:
            to_add = []
            for item in filtered_items:
                pid = item.get('parent_id')
                if pid and pid not in filtered_ids and pid in all_items_by_id:
                    to_add.append(all_items_by_id[pid])
                    filtered_ids.add(pid)
            if not to_add:
                break
            filtered_items.extend(to_add)

        items_by_id = {item['id']: item for item in filtered_items}
        root_items = []
        for item in filtered_items:
            if item['parent_id']:
                parent = items_by_id.get(item['parent_id'])
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(item)
            else:
                root_items.append(item)

        def remove_empty_dropdowns(items):
            result = []
            for item in list(items):
                if item.get('is_dropdown') and item.get('children'):
                    item['children'] = remove_empty_dropdowns(item['children'])
                if item.get('is_dropdown') and len(item.get('children', [])) == 0:
                    continue
                result.append(item)
            return result

        root_items = remove_empty_dropdowns(root_items)
        return root_items
    except Exception as e:
        import traceback
        print(f"⚠️ get_navigation_for_role: {e}")
        traceback.print_exc()
        return []


def render_navigation_html(items):
    """
    Rendert Navigation-Items als HTML
    """
    if not items:
        return ""
    
    html = ""
    
    for item in items:
        if item.get('is_divider'):
            html += '<li><hr class="dropdown-divider"></li>\n'
        elif item.get('is_header'):
            html += f'<li><h6 class="dropdown-header text-muted">{item["label"]}</h6></li>\n'
        elif item.get('is_dropdown'):
            # Dropdown-Item
            dropdown_id = item['label'].lower().replace(' ', '') + 'Dropdown'
            html += f'''<li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="{dropdown_id}" role="button" data-bs-toggle="dropdown">
                    <i class="bi {item.get('icon', '')}"></i> {item['label']}
                </a>
                <ul class="dropdown-menu">\n'''
            
            # Children rendern
            if 'children' in item:
                html += render_navigation_html(item['children'])
            
            html += '</ul>\n</li>\n'
        else:
            # Normales Link-Item
            url = item.get('url', '#')
            icon = item.get('icon', '')
            label = item['label']
            
            if item.get('parent_id'):
                # Dropdown-Child
                html += f'<li><a class="dropdown-item" href="{url}">\n'
                if icon:
                    html += f'    <i class="bi {icon}"></i> {label}\n'
                else:
                    html += f'    {label}\n'
                html += '</a></li>\n'
            else:
                # Top-Level Item
                html += f'''<li class="nav-item">
                    <a class="nav-link" href="{url}">
                        <i class="bi {icon}"></i> {label}
                    </a>
                </li>\n'''
    
    return html
