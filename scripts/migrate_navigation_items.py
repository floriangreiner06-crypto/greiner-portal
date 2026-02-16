#!/usr/bin/env python3
"""
Migration Script: Navigation-Items aus base.html migrieren
TAG 190: Erstellt Initial-Daten für navigation_items Tabelle
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db_connection import get_db
from api.db_utils import row_to_dict

def migrate_navigation_items():
    """Migriert Navigation-Items aus base.html in DB"""
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Navigation-Items definieren (aus base.html extrahiert)
    items = [
        # Top-Level Items
        {'label': 'Dashboard', 'url': '/', 'icon': 'bi-house-door', 'order_index': 1, 'category': 'main'},
        
        # Controlling Dropdown
        {'label': 'Controlling', 'url': None, 'icon': 'bi-graph-up-arrow', 'order_index': 2, 'is_dropdown': True, 'category': 'main'},
        
        # Verkauf Dropdown
        {'label': 'Verkauf', 'url': None, 'icon': 'bi-cart3', 'order_index': 3, 'requires_feature': 'auftragseingang', 'is_dropdown': True, 'category': 'main'},
        
        # Urlaubsplaner
        {'label': 'Urlaubsplaner', 'url': None, 'icon': 'bi-calendar-check', 'order_index': 4, 'is_dropdown': True, 'category': 'main'},
        
        # After Sales
        {'label': 'After Sales', 'url': None, 'icon': 'bi-tools', 'order_index': 5, 'requires_feature': 'teilebestellungen', 'is_dropdown': True, 'category': 'main'},
        
        # Admin
        {'label': 'Admin', 'url': None, 'icon': 'bi-shield-lock', 'order_index': 6, 'role_restriction': 'admin', 'is_dropdown': True, 'category': 'main'},
    ]
    
    # Top-Level Items einfügen
    top_level_ids = {}
    for item in items:
        cursor.execute('''
            INSERT INTO navigation_items 
                (label, url, icon, order_index, requires_feature, role_restriction, is_dropdown, category, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT DO NOTHING
            RETURNING id
        ''', (
            item['label'],
            item.get('url'),
            item.get('icon'),
            item['order_index'],
            item.get('requires_feature'),
            item.get('role_restriction'),
            item.get('is_dropdown', False),
            item.get('category', 'main')
        ))
        
        result = cursor.fetchone()
        if result:
            top_level_ids[item['label']] = result[0]
        else:
            # Item existiert bereits, ID holen
            cursor.execute('SELECT id FROM navigation_items WHERE label = %s', (item['label'],))
            row = cursor.fetchone()
            if row:
                top_level_ids[item['label']] = row[0]
    
    # Controlling Dropdown-Items
    controlling_id = top_level_ids.get('Controlling')
    if controlling_id:
        controlling_items = [
            {'label': 'Übersichten', 'is_header': True, 'requires_feature': 'bankenspiegel', 'order_index': 1},
            {'label': 'Dashboard', 'url': '/controlling/dashboard', 'icon': 'bi-speedometer2', 'requires_feature': 'bankenspiegel', 'order_index': 2},
            {'label': 'BWA', 'url': '/controlling/bwa', 'icon': 'bi-graph-up', 'requires_feature': 'bankenspiegel', 'order_index': 3},
            {'label': 'TEK (Tägliche Erfolgskontrolle)', 'url': '/controlling/tek', 'icon': 'bi-bar-chart-line', 'requires_feature': 'bankenspiegel', 'order_index': 4},
            {'label': 'Kontenmapping', 'url': '/controlling/kontenmapping', 'icon': 'bi-table', 'requires_feature': 'bankenspiegel', 'order_index': 5},
            {'label': 'Auswertung Zeiterfassung', 'url': '/controlling/auswertung-zeiterfassung', 'icon': 'bi-clock-history', 'requires_feature': 'bankenspiegel', 'order_index': 6},
            {'label': '', 'is_divider': True, 'order_index': 7},
            {'label': 'Zielplanung', 'is_header': True, 'requires_feature': 'bankenspiegel', 'order_index': 8},
            {'label': '1%-Ziel (Unternehmensplan)', 'url': '/controlling/unternehmensplan', 'icon': 'bi-bullseye', 'requires_feature': 'bankenspiegel', 'order_index': 9},
            {'label': 'KST-Ziele (Tagesstatus)', 'url': '/controlling/kst-ziele', 'icon': 'bi-bar-chart', 'requires_feature': 'bankenspiegel', 'order_index': 10},
            {'label': '', 'is_divider': True, 'order_index': 11},
            {'label': 'Abteilungsleiter-Planung', 'url': '/planung/abteilungsleiter', 'icon': 'bi-clipboard-check', 'requires_feature': 'controlling', 'order_index': 12},
            {'label': 'Analysen', 'is_header': True, 'order_index': 13},
            {'label': 'Zinsen-Analyse', 'url': '/bankenspiegel/zinsen-analyse', 'icon': 'bi-percent', 'requires_feature': 'zinsen', 'order_index': 14},
            {'label': 'Einkaufsfinanzierung', 'url': '/bankenspiegel/einkaufsfinanzierung', 'icon': 'bi-truck', 'requires_feature': 'einkaufsfinanzierung', 'order_index': 15},
            {'label': 'Jahresprämie', 'url': '/jahrespraemie/', 'icon': 'bi-gift', 'requires_feature': 'bankenspiegel', 'order_index': 16},
            {'label': '', 'is_divider': True, 'order_index': 17},
            {'label': 'Bankenspiegel', 'is_header': True, 'requires_feature': 'bankenspiegel', 'order_index': 18},
            {'label': 'Dashboard', 'url': '/bankenspiegel/dashboard', 'icon': 'bi-bank2', 'requires_feature': 'bankenspiegel', 'order_index': 19},
            {'label': 'Kontenübersicht', 'url': '/bankenspiegel/konten', 'icon': 'bi-wallet2', 'requires_feature': 'bankenspiegel', 'order_index': 20},
            {'label': 'Transaktionen', 'url': '/bankenspiegel/transaktionen', 'icon': 'bi-receipt', 'requires_feature': 'bankenspiegel', 'order_index': 21},
            {'label': 'Fahrzeugfinanzierungen', 'url': '/bankenspiegel/fahrzeugfinanzierungen', 'icon': 'bi-car-front', 'requires_feature': 'bankenspiegel', 'order_index': 22},
            {'label': '', 'is_divider': True, 'order_index': 23},
            {'label': 'Archiv', 'is_header': True, 'requires_feature': 'bankenspiegel', 'order_index': 24},
            {'label': 'TEK v1', 'url': '/controlling/tek/archiv', 'icon': 'bi-archive', 'requires_feature': 'bankenspiegel', 'order_index': 25},
        ]
        
        for item in controlling_items:
            cursor.execute('''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, requires_feature, is_header, is_divider, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'dropdown', true)
                ON CONFLICT DO NOTHING
            ''', (
                controlling_id,
                item['label'],
                item.get('url'),
                item.get('icon'),
                item['order_index'],
                item.get('requires_feature'),
                item.get('is_header', False),
                item.get('is_divider', False)
            ))
    
    # Verkauf Dropdown-Items
    verkauf_id = top_level_ids.get('Verkauf')
    if verkauf_id:
        verkauf_items = [
            {'label': 'Auftragseingang', 'url': '/verkauf/auftragseingang', 'icon': 'bi-clipboard-data', 'requires_feature': 'auftragseingang', 'order_index': 1},
            {'label': 'Auslieferungen', 'url': '/verkauf/auslieferung/detail', 'icon': 'bi-truck', 'requires_feature': 'auslieferungen', 'order_index': 2},
            {'label': 'eAutoseller Bestand', 'url': '/verkauf/eautoseller-bestand', 'icon': 'bi-car-front', 'requires_feature': 'auftragseingang', 'order_index': 3},
            {'label': 'GW-Standzeit', 'url': '/verkauf/gw-bestand', 'icon': 'bi-clock-history', 'requires_feature': 'auftragseingang', 'order_index': 4},
            {'label': '', 'is_divider': True, 'order_index': 5},
            {'label': 'Planung', 'is_header': True, 'role_restriction': 'admin', 'order_index': 6},
            {'label': 'Budget-Planung', 'url': '/verkauf/budget', 'icon': 'bi-bullseye', 'role_restriction': 'admin', 'order_index': 7},
            {'label': 'Lieferforecast', 'url': '/verkauf/lieferforecast', 'icon': 'bi-calendar-week', 'role_restriction': 'admin', 'order_index': 8},
            {'label': '', 'is_divider': True, 'order_index': 9},
            {'label': 'Tools', 'is_header': True, 'requires_feature': 'auftragseingang', 'order_index': 10},
            {'label': 'Leasys Programmfinder', 'url': '/verkauf/leasys-programmfinder', 'icon': 'bi-search-heart', 'requires_feature': 'auftragseingang', 'order_index': 11},
            {'label': 'Leasys Kalkulator', 'url': '/verkauf/leasys-kalkulator', 'icon': 'bi-calculator', 'requires_feature': 'auftragseingang', 'order_index': 12},
        ]
        
        for item in verkauf_items:
            cursor.execute('''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, requires_feature, role_restriction, is_header, is_divider, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'dropdown', true)
                ON CONFLICT DO NOTHING
            ''', (
                verkauf_id,
                item['label'],
                item.get('url'),
                item.get('icon'),
                item['order_index'],
                item.get('requires_feature'),
                item.get('role_restriction'),
                item.get('is_header', False),
                item.get('is_divider', False)
            ))
    
    # Urlaubsplaner Items
    urlaub_id = top_level_ids.get('Urlaubsplaner')
    if urlaub_id:
        urlaub_items = [
            {'label': 'Mein Urlaub', 'url': '/urlaubsplaner/v2', 'icon': 'bi-calendar-plus', 'order_index': 1},
            {'label': '', 'is_divider': True, 'order_index': 2},
            {'label': 'Team-Übersicht', 'url': '/urlaubsplaner/chef', 'icon': 'bi-diagram-3', 'requires_feature': 'urlaub_genehmigen', 'order_index': 3},
        ]
        
        for item in urlaub_items:
            cursor.execute('''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, requires_feature, is_divider, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'dropdown', true)
                ON CONFLICT DO NOTHING
            ''', (
                urlaub_id,
                item['label'],
                item.get('url'),
                item.get('icon'),
                item['order_index'],
                item.get('requires_feature'),
                item.get('is_divider', False)
            ))
    
    # After Sales Items (vereinfacht - wichtigste)
    aftersales_id = top_level_ids.get('After Sales')
    if aftersales_id:
        aftersales_items = [
            {'label': 'Controlling', 'is_header': True, 'requires_feature': 'teilebestellungen', 'order_index': 1},
            {'label': 'Serviceberater Übersicht', 'url': '/aftersales/serviceberater/uebersicht', 'icon': 'bi-people', 'requires_feature': 'teilebestellungen', 'order_index': 2},
            {'label': 'Serviceberater Controlling', 'url': '/aftersales/serviceberater/', 'icon': 'bi-person-badge', 'requires_feature': 'teilebestellungen', 'order_index': 3},
            {'label': '', 'is_divider': True, 'order_index': 4},
            {'label': 'Garantie', 'is_header': True, 'requires_feature': 'aftersales', 'order_index': 5},
            {'label': 'Garantieaufträge', 'url': '/aftersales/garantie/auftraege', 'icon': 'bi-shield-check', 'requires_feature': 'aftersales', 'order_index': 6},
            {'label': 'Handbücher & Richtlinien', 'url': '/aftersales/garantie/handbuecher', 'icon': 'bi-journal-bookmark', 'requires_feature': 'aftersales', 'order_index': 7},
        ]
        
        for item in aftersales_items:
            cursor.execute('''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, requires_feature, is_header, is_divider, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'dropdown', true)
                ON CONFLICT DO NOTHING
            ''', (
                aftersales_id,
                item['label'],
                item.get('url'),
                item.get('icon'),
                item['order_index'],
                item.get('requires_feature'),
                item.get('is_header', False),
                item.get('is_divider', False)
            ))
    
    # Admin Items
    admin_id = top_level_ids.get('Admin')
    if admin_id:
        admin_items = [
            {'label': 'System', 'is_header': True, 'role_restriction': 'admin', 'order_index': 1},
            {'label': 'Task Manager', 'url': '/admin/celery/', 'icon': 'bi-list-task', 'role_restriction': 'admin', 'order_index': 2},
            {'label': 'Flower Dashboard', 'url': 'http://10.80.80.20:5555', 'icon': 'bi-flower1', 'role_restriction': 'admin', 'order_index': 3},
            {'label': 'Rechteverwaltung', 'url': '/admin/rechte', 'icon': 'bi-person-lock', 'role_restriction': 'admin', 'order_index': 4},
        ]
        
        for item in admin_items:
            cursor.execute('''
                INSERT INTO navigation_items 
                    (parent_id, label, url, icon, order_index, role_restriction, is_header, category, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'dropdown', true)
                ON CONFLICT DO NOTHING
            ''', (
                admin_id,
                item['label'],
                item.get('url'),
                item.get('icon'),
                item['order_index'],
                item.get('role_restriction'),
                item.get('is_header', False)
            ))
    
    conn.commit()
    conn.close()
    
    print("✅ Navigation-Items erfolgreich migriert!")


if __name__ == '__main__':
    migrate_navigation_items()
