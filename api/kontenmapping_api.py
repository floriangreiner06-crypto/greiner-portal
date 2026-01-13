"""
Kontenmapping API - Lesbares Mapping für Buchhaltung
=====================================================
TAG 181: Export und Bearbeitung von Kontenmappings

Features:
- Lesbares Kontenmapping ausgeben (CSV/Excel/JSON)
- Editierbares Mapping (später)
- Export mit gewünschten Änderungen als TODO-Liste
"""

from flask import Blueprint, jsonify, request, Response
from api.db_utils import db_session, row_to_dict, rows_to_list, locosoft_session
from api.db_connection import convert_placeholders
import csv
import io
from datetime import datetime

kontenmapping_api = Blueprint('kontenmapping_api', __name__)

# =============================================================================
# KONTENMAPPING EXPORT
# =============================================================================

@kontenmapping_api.route('/api/kontenmapping/export', methods=['GET'])
def export_kontenmapping():
    """
    GET /api/kontenmapping/export
    
    Exportiert alle Konten mit Bezeichnungen als lesbares Mapping.
    
    Query-Parameter:
    - format: 'csv' (Standard), 'excel', 'json'
    - firma: 1=Stellantis, 2=Hyundai, 0=Alle (Standard: 0)
    - konto_von: Filter ab Kontonummer (optional)
    - konto_bis: Filter bis Kontonummer (optional)
    - nur_verwendet: true/false - nur Konten mit Buchungen (Standard: false)
    - mit_kst: true/false - KST-Information hinzufügen (Standard: false)
    
    Returns:
    - CSV: text/csv mit Download-Header
    - Excel: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    - JSON: application/json
    """
    try:
        export_format = request.args.get('format', 'csv').lower()
        firma = request.args.get('firma', '0')
        konto_von = request.args.get('konto_von', type=int)
        konto_bis = request.args.get('konto_bis', type=int)
        nur_verwendet = request.args.get('nur_verwendet', 'false').lower() == 'true'
        mit_kst = request.args.get('mit_kst', 'false').lower() == 'true'
        
        with locosoft_session() as conn:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Basis-Query: Alle Konten mit Bezeichnungen
            where_clauses = []
            params = []
            
            # Firma-Filter
            if firma != '0':
                where_clauses.append("n.subsidiary_to_company_ref = %s")
                params.append(int(firma))
            
            # Kontonummer-Filter
            if konto_von:
                where_clauses.append("n.nominal_account_number >= %s")
                params.append(konto_von)
            if konto_bis:
                where_clauses.append("n.nominal_account_number <= %s")
                params.append(konto_bis)
            
            # Nur verwendete Konten (mit Buchungen)
            if nur_verwendet:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM journal_accountings j
                        WHERE j.nominal_account_number = n.nominal_account_number
                        LIMIT 1
                    )
                """)
            
            where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Query mit KST-Information
            if mit_kst:
                query = convert_placeholders(f"""
                    SELECT DISTINCT
                        n.nominal_account_number as konto,
                        n.subsidiary_to_company_ref as firma,
                        CASE n.subsidiary_to_company_ref
                            WHEN 1 THEN 'Stellantis'
                            WHEN 2 THEN 'Hyundai'
                            ELSE 'Unbekannt'
                        END as firma_name,
                        n.account_description as bezeichnung_locosoft,
                        -- TAG 181: KST-Stelle korrekt ermitteln (KORRIGIERT nach Buchhaltung)
                        -- Für Kosten (4xxxxx): 5. Ziffer
                        -- Für Umsatz/Einsatz (7xxxxx/8xxxxx): 2. Ziffer (Kostenstelle), 6. Ziffer (Filiale)
                        -- Beispiel: 810001 → KST = 1 (2. Ziffer), Filiale = 1 (6. Ziffer)
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN
                                -- Kosten: 5. Ziffer
                                CASE WHEN LENGTH(CAST(n.nominal_account_number AS TEXT)) >= 5 
                                    THEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER)
                                    ELSE NULL
                                END
                            WHEN n.nominal_account_number BETWEEN 700000 AND 899999 THEN
                                -- Umsatz/Einsatz: 2. Ziffer = Kostenstelle
                                CASE WHEN LENGTH(CAST(n.nominal_account_number AS TEXT)) >= 2 
                                    THEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER)
                                    ELSE NULL
                                END
                            ELSE NULL
                        END as kst_stelle,
                        -- TAG 181: KST-Name korrekt zuordnen (KORRIGIERT nach Buchhaltung)
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN
                                -- Kosten: 5. Ziffer
                                CASE 
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 0 THEN 'Gemeinkosten'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 1 THEN 'Neuwagen'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 2 THEN 'Gebrauchtwagen'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 3 THEN 'Service/Werkstatt'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 6 THEN 'Teile & Zubehör'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 5, 1) AS INTEGER) = 7 THEN 'Mietwagen'
                                    ELSE NULL
                                END
                            WHEN n.nominal_account_number BETWEEN 700000 AND 899999 THEN
                                -- Umsatz/Einsatz: 2. Ziffer = Kostenstelle
                                -- KST-Mapping: 1=NW, 2=GW, 3=T+Z, 4=Service, 6=Mietwagen
                                CASE 
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) = 1 THEN 'Neuwagen'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) = 2 THEN 'Gebrauchtwagen'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) = 3 THEN 'Teile & Zubehör'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) = 4 THEN 'Service/Werkstatt'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) = 6 THEN 'Mietwagen'
                                    ELSE NULL
                                END
                            ELSE NULL
                        END as kst_name,
                        -- TAG 181: Filiale (6. Ziffer) zusätzlich anzeigen
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 700000 AND 899999 THEN
                                -- Umsatz/Einsatz: 6. Ziffer = Filiale
                                CASE WHEN LENGTH(CAST(n.nominal_account_number AS TEXT)) >= 6 
                                    THEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 6, 1) AS INTEGER)
                                    ELSE NULL
                                END
                            ELSE NULL
                        END as filiale,
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 700000 AND 899999 THEN
                                -- Filiale-Mapping: 1=DEG (Opel), 2=Landau (Opel), 1=Hyundai (nur eine Filiale)
                                CASE 
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 6, 1) AS INTEGER) = 1 THEN 'Deggendorf'
                                    WHEN CAST(substr(CAST(n.nominal_account_number AS TEXT), 6, 1) AS INTEGER) = 2 THEN 'Landau'
                                    ELSE NULL
                                END
                            ELSE NULL
                        END as filiale_name,
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 800000 AND 889999 THEN 'Umsatz'
                            WHEN n.nominal_account_number BETWEEN 893200 AND 893299 THEN 'Umsatz (Sonder)'
                            WHEN n.nominal_account_number BETWEEN 700000 AND 799999 THEN 'Einsatz'
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN 'Kosten'
                            WHEN n.nominal_account_number BETWEEN 200000 AND 299999 THEN 'Neutrales Ergebnis'
                            ELSE 'Sonstiges'
                        END as konto_typ,
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 800000 AND 889999 THEN 'HABEN - SOLL'
                            WHEN n.nominal_account_number BETWEEN 893200 AND 893299 THEN 'HABEN - SOLL'
                            WHEN n.nominal_account_number BETWEEN 700000 AND 799999 THEN 'SOLL - HABEN'
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN 'SOLL - HABEN'
                            WHEN n.nominal_account_number BETWEEN 200000 AND 299999 THEN 'HABEN - SOLL'
                            ELSE ''
                        END as berechnung,
                        n.is_profit_loss_account as guv_konto,
                        n.vat_key as mwst_schluessel
                    FROM nominal_accounts n
                    WHERE 1=1 {where_sql}
                    ORDER BY n.nominal_account_number, n.subsidiary_to_company_ref
                """)
            else:
                query = convert_placeholders(f"""
                    SELECT DISTINCT
                        n.nominal_account_number as konto,
                        n.subsidiary_to_company_ref as firma,
                        CASE n.subsidiary_to_company_ref
                            WHEN 1 THEN 'Stellantis'
                            WHEN 2 THEN 'Hyundai'
                            ELSE 'Unbekannt'
                        END as firma_name,
                        n.account_description as bezeichnung_locosoft,
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 800000 AND 889999 THEN 'Umsatz'
                            WHEN n.nominal_account_number BETWEEN 893200 AND 893299 THEN 'Umsatz (Sonder)'
                            WHEN n.nominal_account_number BETWEEN 700000 AND 799999 THEN 'Einsatz'
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN 'Kosten'
                            WHEN n.nominal_account_number BETWEEN 200000 AND 299999 THEN 'Neutrales Ergebnis'
                            ELSE 'Sonstiges'
                        END as konto_typ,
                        CASE 
                            WHEN n.nominal_account_number BETWEEN 800000 AND 889999 THEN 'HABEN - SOLL'
                            WHEN n.nominal_account_number BETWEEN 893200 AND 893299 THEN 'HABEN - SOLL'
                            WHEN n.nominal_account_number BETWEEN 700000 AND 799999 THEN 'SOLL - HABEN'
                            WHEN n.nominal_account_number BETWEEN 400000 AND 499999 THEN 'SOLL - HABEN'
                            WHEN n.nominal_account_number BETWEEN 200000 AND 299999 THEN 'HABEN - SOLL'
                            ELSE ''
                        END as berechnung,
                        n.is_profit_loss_account as guv_konto,
                        n.vat_key as mwst_schluessel
                    FROM nominal_accounts n
                    WHERE 1=1 {where_sql}
                    ORDER BY n.nominal_account_number, n.subsidiary_to_company_ref
                """)
            
            cursor.execute(query, params if params else None)
            rows = cursor.fetchall()
            
            if not rows:
                return jsonify({'error': 'Keine Konten gefunden'}), 404
            
            # Daten konvertieren (RealDictCursor gibt bereits Dict zurück)
            konten = [dict(row) for row in rows]
            
            # Export-Format
            if export_format == 'json':
                return jsonify({
                    'status': 'ok',
                    'anzahl': len(konten),
                    'export_datum': datetime.now().isoformat(),
                    'konten': konten
                })
            
            elif export_format == 'csv':
                # CSV erstellen
                output = io.StringIO()
                writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                
                # Header
                if mit_kst:
                    writer.writerow([
                        'Kontonummer', 'Firma', 'Firma Name', 'Bezeichnung (Locosoft)',
                        'KST-Stelle', 'KST-Name', 'Konto-Typ', 'Berechnung', 'G&V-Konto', 'MwSt-Schlüssel'
                    ])
                else:
                    writer.writerow([
                        'Kontonummer', 'Firma', 'Firma Name', 'Bezeichnung (Locosoft)',
                        'Konto-Typ', 'Berechnung', 'G&V-Konto', 'MwSt-Schlüssel'
                    ])
                
                # Daten
                for konto in konten:
                    if mit_kst:
                        writer.writerow([
                            konto.get('konto', ''),
                            konto.get('firma', ''),
                            konto.get('firma_name', ''),
                            konto.get('bezeichnung_locosoft', ''),
                            konto.get('kst_stelle', ''),
                            konto.get('kst_name', ''),
                            konto.get('konto_typ', ''),
                            konto.get('berechnung', ''),
                            konto.get('guv_konto', ''),
                            konto.get('mwst_schluessel', '')
                        ])
                    else:
                        writer.writerow([
                            konto.get('konto', ''),
                            konto.get('firma', ''),
                            konto.get('firma_name', ''),
                            konto.get('bezeichnung_locosoft', ''),
                            konto.get('konto_typ', ''),
                            konto.get('berechnung', ''),
                            konto.get('guv_konto', ''),
                            konto.get('mwst_schluessel', '')
                        ])
                
                # Response
                filename = f"kontenmapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                return Response(
                    output.getvalue(),
                    mimetype='text/csv; charset=utf-8',
                    headers={
                        'Content-Disposition': f'attachment; filename="{filename}"'
                    }
                )
            
            elif export_format == 'excel':
                # Excel-Export (später mit openpyxl)
                return jsonify({'error': 'Excel-Export noch nicht implementiert. Bitte CSV verwenden.'}), 501
            
            else:
                return jsonify({'error': f'Unbekanntes Format: {export_format}'}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@kontenmapping_api.route('/api/kontenmapping/todo', methods=['POST'])
def create_kontenmapping_todo():
    """
    POST /api/kontenmapping/todo
    
    Erstellt eine TODO-Liste mit gewünschten Änderungen am Kontenmapping.
    
    Request Body (JSON):
    {
        "aenderungen": [
            {
                "konto": 810111,
                "firma": 1,
                "bezeichnung_alt": "NW VE Privatkunde bar/überw.",
                "bezeichnung_neu": "NW VE Privatkunde bar/überw. (korrigiert)",
                "grund": "Bezeichnung unklar"
            },
            ...
        ]
    }
    
    Returns:
    - Markdown-Formatierte TODO-Liste für Claude
    """
    try:
        data = request.get_json()
        if not data or 'aenderungen' not in data:
            return jsonify({'error': 'Keine Änderungen übergeben'}), 400
        
        aenderungen = data['aenderungen']
        if not aenderungen:
            return jsonify({'error': 'Leere Änderungsliste'}), 400
        
        # TODO-Liste im Markdown-Format erstellen
        todo_lines = [
            "# Kontenmapping-Änderungen (TODO für Claude)",
            "",
            f"**Erstellt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Anzahl Änderungen:** {len(aenderungen)}",
            "",
            "## Änderungen",
            ""
        ]
        
        for idx, aenderung in enumerate(aenderungen, 1):
            todo_lines.append(f"### {idx}. Konto {aenderung.get('konto', 'N/A')}")
            todo_lines.append("")
            todo_lines.append(f"- **Firma:** {aenderung.get('firma', 'N/A')}")
            todo_lines.append(f"- **Bezeichnung (alt):** {aenderung.get('bezeichnung_alt', 'N/A')}")
            todo_lines.append(f"- **Bezeichnung (neu):** {aenderung.get('bezeichnung_neu', 'N/A')}")
            if aenderung.get('grund'):
                todo_lines.append(f"- **Grund:** {aenderung.get('grund')}")
            todo_lines.append("")
            todo_lines.append("```python")
            todo_lines.append(f"# TODO: Kontobezeichnung für Konto {aenderung.get('konto')} ändern")
            todo_lines.append(f"# Alt: {aenderung.get('bezeichnung_alt', 'N/A')}")
            todo_lines.append(f"# Neu: {aenderung.get('bezeichnung_neu', 'N/A')}")
            todo_lines.append("```")
            todo_lines.append("")
        
        todo_lines.append("---")
        todo_lines.append("")
        todo_lines.append("## Implementierung")
        todo_lines.append("")
        todo_lines.append("Diese Änderungen können in einer späteren Session umgesetzt werden.")
        todo_lines.append("")
        
        todo_content = "\n".join(todo_lines)
        
        # Als Download zurückgeben
        filename = f"kontenmapping_todo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        return Response(
            todo_content,
            mimetype='text/markdown; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
