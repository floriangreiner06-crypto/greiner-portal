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
        
        # Filter: Nur Items auf die User Zugriff hat (Python-Filterung)
        filtered_items = []
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') if hasattr(current_user, 'portal_role') else 'mitarbeiter'
        
        for item in all_items:
            # Prüfe Feature-Zugriff
            if item.get('requires_feature'):
                if not (hasattr(current_user, 'can_access_feature') and 
                        current_user.can_access_feature(item['requires_feature'])):
                    continue
            
            # Prüfe Rollen-Restriktion
            if item.get('role_restriction'):
                if user_role != item['role_restriction']:
                    # Prüfe auch ob User admin ist (admin sieht alles)
                    if not (hasattr(current_user, 'can_access_feature') and 
                            current_user.can_access_feature('admin')):
                        continue
            
            filtered_items.append(item)
        
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
        
        # TAG 192: In Flask g speichern (Per-Request-Cache)
        if has_request_context():
            g.navigation_items = root_items
        
        return root_items
        
    except Exception as e:
        import traceback
        print(f"⚠️ Fehler beim Laden der Navigation: {e}")
        traceback.print_exc()
        return []  # Fallback: Leere Liste


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
