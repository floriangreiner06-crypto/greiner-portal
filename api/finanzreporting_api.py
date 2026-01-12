"""
Finanzreporting API - Cube-Funktionalität für BWA
==================================================
Erstellt: TAG 178 (2026-01-10)

Zweck: 
- Dynamische Cube-Abfragen auf Basis von Materialized Views
- Aggregation nach Dimensionen (Zeit, Standort, KST, Konto)
- Schnelle BWA-Analysen

Architektur:
- Dimensionstabellen: dim_zeit, dim_standort, dim_kostenstelle, dim_konto
- Fact-Table: fact_bwa
- API-Endpunkte: /api/finanzreporting/cube
"""

from flask import Blueprint, jsonify, request, Response
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import io
import csv
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import convert_placeholders

finanzreporting_api = Blueprint('finanzreporting_api', __name__)

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def validate_dimension(dim: str) -> bool:
    """Validiert, ob eine Dimension gültig ist"""
    valid_dimensions = ['zeit', 'standort', 'kst', 'konto']
    return dim.lower() in valid_dimensions

def validate_measure(measure: str) -> bool:
    """Validiert, ob ein Measure gültig ist"""
    valid_measures = ['betrag', 'menge']
    return measure.lower() in valid_measures

def build_dimension_select(dimensions: List[str]) -> tuple:
    """Baut SELECT-Klausel für Dimensionen"""
    selects = []
    joins_dict = {}  # Dict um Duplikate zu vermeiden
    
    if 'zeit' in dimensions:
        selects.append("dz.jahr_monat as zeit")
        joins_dict['zeit'] = "LEFT JOIN dim_zeit dz ON f.zeit_id = dz.datum"
    
    if 'standort' in dimensions:
        selects.append("ds.standort_code as standort")
        joins_dict['standort'] = "LEFT JOIN dim_standort ds ON f.standort_id = ds.standort_id"
    
    if 'kst' in dimensions:
        selects.append("dk.kst_id as kst")
        joins_dict['kst'] = "LEFT JOIN dim_kostenstelle dk ON f.kst_id = dk.kst_id"
    
    if 'konto' in dimensions:
        selects.append("dkonto.konto_id as konto")
        selects.append("dkonto.ebene3 as konto_ebene3")
        joins_dict['konto'] = "LEFT JOIN dim_konto dkonto ON f.konto_id = dkonto.konto_id"
    
    joins_str = " ".join(joins_dict.values()) if joins_dict else ""
    return ", ".join(selects), joins_str

def build_measure_select(measures: List[str]) -> str:
    """Baut SELECT-Klausel für Measures"""
    selects = []
    
    if 'betrag' in measures:
        selects.append("SUM(f.betrag) as betrag")
    
    if 'menge' in measures:
        selects.append("SUM(f.menge) as menge")
    
    return ", ".join(selects)

def build_group_by(dimensions: List[str]) -> str:
    """Baut GROUP BY-Klausel"""
    groups = []
    
    if 'zeit' in dimensions:
        groups.append("dz.jahr_monat")
    
    if 'standort' in dimensions:
        groups.append("ds.standort_code")
    
    if 'kst' in dimensions:
        groups.append("dk.kst_id")
    
    if 'konto' in dimensions:
        groups.append("dkonto.konto_id")
        groups.append("dkonto.ebene3")
    
    return ", ".join(groups) if groups else ""

def build_filters(filters: Dict[str, Any]) -> tuple:
    """Baut WHERE-Klausel aus Filtern"""
    conditions = []
    params = []
    
    # Zeit-Filter
    if 'von' in filters:
        conditions.append("f.zeit_id >= %s")
        params.append(filters['von'])
    
    if 'bis' in filters:
        conditions.append("f.zeit_id <= %s")
        params.append(filters['bis'])
    
    # Standort-Filter
    if 'standort' in filters:
        standort = filters['standort']
        if isinstance(standort, list):
            placeholders = ", ".join(["%s"] * len(standort))
            conditions.append(f"ds.standort_code IN ({placeholders})")
            params.extend(standort)
        else:
            conditions.append("ds.standort_code = %s")
            params.append(standort)
    
    # KST-Filter
    if 'kst' in filters:
        kst = filters['kst']
        if isinstance(kst, list):
            placeholders = ", ".join(["%s"] * len(kst))
            conditions.append(f"dk.kst_id IN ({placeholders})")
            params.extend(kst)
        else:
            conditions.append("dk.kst_id = %s")
            params.append(kst)
    
    # Konto-Filter
    if 'konto' in filters:
        konto = filters['konto']
        if isinstance(konto, list):
            placeholders = ", ".join(["%s"] * len(konto))
            conditions.append(f"dkonto.konto_id IN ({placeholders})")
            params.extend(konto)
        else:
            conditions.append("dkonto.konto_id = %s")
            params.append(konto)
    
    # Konto-Ebene-Filter
    if 'konto_ebene3' in filters:
        ebene3 = filters['konto_ebene3']
        if isinstance(ebene3, list):
            placeholders = ", ".join(["%s"] * len(ebene3))
            conditions.append(f"dkonto.ebene3 IN ({placeholders})")
            params.extend(ebene3)
        else:
            conditions.append("dkonto.ebene3 = %s")
            params.append(ebene3)
    
    where_clause = " AND ".join(conditions) if conditions else ""
    return where_clause, params

# ============================================================================
# API-ENDPUNKTE
# ============================================================================

@finanzreporting_api.route('/api/finanzreporting/cube', methods=['GET'])
def get_cube_data():
    """
    GET /api/finanzreporting/cube
    
    Cube-Abfrage für BWA-Daten
    
    Query-Parameter:
    - dimensionen: Komma-getrennte Liste (zeit,standort,kst,konto)
    - measures: Komma-getrennte Liste (betrag,menge)
    - von: Startdatum (YYYY-MM-DD)
    - bis: Enddatum (YYYY-MM-DD)
    - standort: Standort-Code (DEG,HYU,LAN) oder Liste
    - kst: KST-ID oder Liste
    - konto: Konto-ID oder Liste
    - konto_ebene3: Konto-Ebene 3 (z.B. 400, 700, 800) oder Liste
    
    Returns:
    {
        "dimensionen": ["zeit", "standort"],
        "measures": ["betrag"],
        "data": [
            {
                "zeit": "2024-09",
                "standort": "DEG",
                "betrag": 123456.78
            }
        ],
        "total": {
            "betrag": 123456.78
        }
    }
    """
    try:
        # Parameter parsen
        dimensionen_str = request.args.get('dimensionen', 'zeit')
        measures_str = request.args.get('measures', 'betrag')
        
        dimensionen = [d.strip() for d in dimensionen_str.split(',')]
        measures = [m.strip() for m in measures_str.split(',')]
        
        # Validierung
        for dim in dimensionen:
            if not validate_dimension(dim):
                return jsonify({'error': f'Ungültige Dimension: {dim}'}), 400
        
        for measure in measures:
            if not validate_measure(measure):
                return jsonify({'error': f'Ungültiges Measure: {measure}'}), 400
        
        # Filter parsen
        filters = {}
        if 'von' in request.args:
            filters['von'] = request.args.get('von')
        if 'bis' in request.args:
            filters['bis'] = request.args.get('bis')
        if 'standort' in request.args:
            standort = request.args.get('standort')
            filters['standort'] = standort.split(',') if ',' in standort else standort
        if 'kst' in request.args:
            kst = request.args.get('kst')
            filters['kst'] = [int(k) for k in kst.split(',')] if ',' in kst else int(kst)
        if 'konto' in request.args:
            konto = request.args.get('konto')
            filters['konto'] = [int(k) for k in konto.split(',')] if ',' in konto else int(konto)
        if 'konto_ebene3' in request.args:
            ebene3 = request.args.get('konto_ebene3')
            filters['konto_ebene3'] = [int(e) for e in ebene3.split(',')] if ',' in ebene3 else int(ebene3)
        
        # SQL bauen
        dim_select, dim_joins = build_dimension_select(dimensionen)
        measure_select = build_measure_select(measures)
        group_by = build_group_by(dimensionen)
        where_clause, params = build_filters(filters)
        
        # Prüfe ob JOINs nötig sind (auch für Filter)
        needs_zeit_join = 'zeit' in dimensionen or 'von' in filters or 'bis' in filters
        needs_standort_join = 'standort' in dimensionen or 'standort' in filters
        needs_kst_join = 'kst' in dimensionen or 'kst' in filters
        needs_konto_join = 'konto' in dimensionen or 'konto' in filters or 'konto_ebene3' in filters
        
        # JOINs sammeln (ohne Duplikate)
        joins_set = set()
        
        # JOINs aus Dimensionen
        if dim_joins:
            # Parse bestehende JOINs
            if 'dim_zeit' in dim_joins:
                joins_set.add("LEFT JOIN dim_zeit dz ON f.zeit_id = dz.datum")
            if 'dim_standort' in dim_joins:
                joins_set.add("LEFT JOIN dim_standort ds ON f.standort_id = ds.standort_id")
            if 'dim_kostenstelle' in dim_joins:
                joins_set.add("LEFT JOIN dim_kostenstelle dk ON f.kst_id = dk.kst_id")
            if 'dim_konto' in dim_joins:
                joins_set.add("LEFT JOIN dim_konto dkonto ON f.konto_id = dkonto.konto_id")
        
        # JOINs für Filter hinzufügen (falls nicht bereits vorhanden)
        if needs_zeit_join:
            joins_set.add("LEFT JOIN dim_zeit dz ON f.zeit_id = dz.datum")
        if needs_standort_join:
            joins_set.add("LEFT JOIN dim_standort ds ON f.standort_id = ds.standort_id")
        if needs_kst_join:
            joins_set.add("LEFT JOIN dim_kostenstelle dk ON f.kst_id = dk.kst_id")
        if needs_konto_join:
            joins_set.add("LEFT JOIN dim_konto dkonto ON f.konto_id = dkonto.konto_id")
        
        all_joins = " ".join(sorted(joins_set)) if joins_set else ""
        
        # SQL-Query zusammenbauen
        sql = f"""
            SELECT 
                {dim_select if dim_select else "1 as dummy"},
                {measure_select}
            FROM fact_bwa f
            {all_joins}
        """
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if group_by:
            sql += f" GROUP BY {group_by}"
        elif dim_select:
            # Wenn Dimensionen aber kein GROUP BY, dann GROUP BY Dimensionen
            sql += f" GROUP BY {dim_select}"
        
        # ORDER BY
        order_parts = []
        if 'zeit' in dimensionen:
            order_parts.append("dz.jahr_monat")
        if 'standort' in dimensionen:
            order_parts.append("ds.standort_code")
        if 'kst' in dimensionen:
            order_parts.append("dk.kst_id")
        if 'konto' in dimensionen:
            order_parts.append("dkonto.konto_id")
        
        if order_parts:
            sql += f" ORDER BY {', '.join(order_parts)}"
        else:
            sql += " ORDER BY 1"
        
        # Query ausführen
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(sql), params)
            rows = cursor.fetchall()
            
            # Daten formatieren
            data = []
            total = {measure: 0.0 for measure in measures}
            
            for row in rows:
                row_dict = row_to_dict(row, cursor)
                data.append(row_dict)
                
                # Total berechnen
                for measure in measures:
                    if measure in row_dict and row_dict[measure]:
                        total[measure] += float(row_dict[measure] or 0)
            
            return jsonify({
                'dimensionen': dimensionen,
                'measures': measures,
                'data': data,
                'total': total,
                'count': len(data)
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@finanzreporting_api.route('/api/finanzreporting/refresh', methods=['POST'])
def refresh_cube():
    """
    POST /api/finanzreporting/refresh
    
    Aktualisiert alle Materialized Views des Finanzreporting Cubes
    
    Returns:
    {
        "success": true,
        "message": "Cube erfolgreich aktualisiert"
    }
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT refresh_finanzreporting_cube()")
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cube erfolgreich aktualisiert'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@finanzreporting_api.route('/api/finanzreporting/cube/export', methods=['GET'])
def export_cube_data():
    """
    GET /api/finanzreporting/cube/export
    
    Exportiert Cube-Daten als CSV oder Excel
    
    Query-Parameter:
    - format: 'csv' (Standard) oder 'excel'
    - Alle Parameter von /api/finanzreporting/cube werden unterstützt
    
    Returns:
    - CSV: text/csv mit Download-Header
    - Excel: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    try:
        # Format bestimmen
        export_format = request.args.get('format', 'csv').lower()
        
        # Cube-Daten holen (nutzt gleiche Logik wie get_cube_data)
        dimensionen_str = request.args.get('dimensionen', 'zeit')
        measures_str = request.args.get('measures', 'betrag')
        
        dimensionen = [d.strip() for d in dimensionen_str.split(',')]
        measures = [m.strip() for m in measures_str.split(',')]
        
        # Validierung
        for dim in dimensionen:
            if not validate_dimension(dim):
                return jsonify({'error': f'Ungültige Dimension: {dim}'}), 400
        
        for measure in measures:
            if not validate_measure(measure):
                return jsonify({'error': f'Ungültiges Measure: {measure}'}), 400
        
        # Filter parsen (gleiche Logik wie get_cube_data)
        filters = {}
        if 'von' in request.args:
            filters['von'] = request.args.get('von')
        if 'bis' in request.args:
            filters['bis'] = request.args.get('bis')
        if 'standort' in request.args:
            standort = request.args.get('standort')
            filters['standort'] = standort.split(',') if ',' in standort else standort
        if 'kst' in request.args:
            kst = request.args.get('kst')
            filters['kst'] = [int(k) for k in kst.split(',')] if ',' in kst else int(kst)
        if 'konto' in request.args:
            konto = request.args.get('konto')
            filters['konto'] = [int(k) for k in konto.split(',')] if ',' in konto else int(konto)
        if 'konto_ebene3' in request.args:
            ebene3 = request.args.get('konto_ebene3')
            filters['konto_ebene3'] = [int(e) for e in ebene3.split(',')] if ',' in ebene3 else int(ebene3)
        
        # SQL bauen (gleiche Logik wie get_cube_data)
        dim_select, dim_joins = build_dimension_select(dimensionen)
        measure_select = build_measure_select(measures)
        group_by = build_group_by(dimensionen)
        where_clause, params = build_filters(filters)
        
        # JOINs sammeln
        joins_set = set()
        needs_zeit_join = 'zeit' in dimensionen or 'von' in filters or 'bis' in filters
        needs_standort_join = 'standort' in dimensionen or 'standort' in filters
        needs_kst_join = 'kst' in dimensionen or 'kst' in filters
        needs_konto_join = 'konto' in dimensionen or 'konto' in filters or 'konto_ebene3' in filters
        
        if dim_joins:
            if 'dim_zeit' in dim_joins:
                joins_set.add("LEFT JOIN dim_zeit dz ON f.zeit_id = dz.datum")
            if 'dim_standort' in dim_joins:
                joins_set.add("LEFT JOIN dim_standort ds ON f.standort_id = ds.standort_id")
            if 'dim_kostenstelle' in dim_joins:
                joins_set.add("LEFT JOIN dim_kostenstelle dk ON f.kst_id = dk.kst_id")
            if 'dim_konto' in dim_joins:
                joins_set.add("LEFT JOIN dim_konto dkonto ON f.konto_id = dkonto.konto_id")
        
        if needs_zeit_join:
            joins_set.add("LEFT JOIN dim_zeit dz ON f.zeit_id = dz.datum")
        if needs_standort_join:
            joins_set.add("LEFT JOIN dim_standort ds ON f.standort_id = ds.standort_id")
        if needs_kst_join:
            joins_set.add("LEFT JOIN dim_kostenstelle dk ON f.kst_id = dk.kst_id")
        if needs_konto_join:
            joins_set.add("LEFT JOIN dim_konto dkonto ON f.konto_id = dkonto.konto_id")
        
        all_joins = " ".join(sorted(joins_set)) if joins_set else ""
        
        # SQL-Query
        sql = f"""
            SELECT 
                {dim_select if dim_select else "1 as dummy"},
                {measure_select}
            FROM fact_bwa f
            {all_joins}
        """
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if group_by:
            sql += f" GROUP BY {group_by}"
        elif dim_select:
            sql += f" GROUP BY {dim_select}"
        
        # ORDER BY
        order_parts = []
        if 'zeit' in dimensionen:
            order_parts.append("dz.jahr_monat")
        if 'standort' in dimensionen:
            order_parts.append("ds.standort_code")
        if 'kst' in dimensionen:
            order_parts.append("dk.kst_id")
        if 'konto' in dimensionen:
            order_parts.append("dkonto.konto_id")
        
        if order_parts:
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        # Daten abfragen
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_placeholders(sql), params)
            rows = cursor.fetchall()
        
        if not rows:
            return jsonify({'error': 'Keine Daten gefunden'}), 404
        
        # Spalten-Namen bestimmen
        column_names = []
        if dim_select:
            for dim in dimensionen:
                if dim == 'zeit':
                    column_names.append('Zeit')
                elif dim == 'standort':
                    column_names.append('Standort')
                elif dim == 'kst':
                    column_names.append('Kostenstelle')
                elif dim == 'konto':
                    column_names.append('Konto')
        
        for measure in measures:
            if measure == 'betrag':
                column_names.append('Betrag (€)')
            elif measure == 'menge':
                column_names.append('Menge')
        
        # CSV-Export
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            # Header
            writer.writerow(column_names)
            
            # Daten
            for row in rows:
                row_dict = row_to_dict(row, cursor)
                row_data = []
                
                # Dimensionen
                for dim in dimensionen:
                    if dim == 'zeit':
                        row_data.append(row_dict.get('zeit', ''))
                    elif dim == 'standort':
                        row_data.append(row_dict.get('standort', ''))
                    elif dim == 'kst':
                        row_data.append(row_dict.get('kst', ''))
                    elif dim == 'konto':
                        row_data.append(row_dict.get('konto', ''))
                
                # Measures
                for measure in measures:
                    value = row_dict.get(measure, 0)
                    if measure == 'betrag':
                        row_data.append(str(float(value or 0)).replace('.', ','))
                    else:
                        row_data.append(str(value or 0).replace('.', ','))
                
                writer.writerow(row_data)
            
            output.seek(0)
            filename = f"finanzreporting_cube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename={filename}',
                    'Content-Type': 'text/csv; charset=utf-8-sig'
                }
            )
        
        # Excel-Export (via pandas, falls verfügbar)
        elif export_format == 'excel':
            try:
                import pandas as pd
                
                # Daten in DataFrame konvertieren
                data_list = []
                for row in rows:
                    row_dict = row_to_dict(row, cursor)
                    data_list.append(row_dict)
                
                df = pd.DataFrame(data_list)
                
                # Spalten umbenennen
                column_mapping = {}
                if 'zeit' in dimensionen:
                    column_mapping['zeit'] = 'Zeit'
                if 'standort' in dimensionen:
                    column_mapping['standort'] = 'Standort'
                if 'kst' in dimensionen:
                    column_mapping['kst'] = 'Kostenstelle'
                if 'konto' in dimensionen:
                    column_mapping['konto'] = 'Konto'
                if 'betrag' in measures:
                    column_mapping['betrag'] = 'Betrag (€)'
                if 'menge' in measures:
                    column_mapping['menge'] = 'Menge'
                
                df = df.rename(columns=column_mapping)
                
                # Excel erstellen
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Finanzreporting')
                
                output.seek(0)
                filename = f"finanzreporting_cube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return Response(
                    output.getvalue(),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={
                        'Content-Disposition': f'attachment; filename={filename}'
                    }
                )
            except ImportError:
                return jsonify({'error': 'Excel-Export erfordert pandas und openpyxl'}), 500
        
        else:
            return jsonify({'error': f'Unbekanntes Format: {export_format}'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@finanzreporting_api.route('/api/finanzreporting/cube/metadata', methods=['GET'])
def get_cube_metadata():
    """
    GET /api/finanzreporting/cube/metadata
    
    Gibt Metadaten über verfügbare Dimensionen, Measures und Filter zurück.
    Nützlich für Frontend-Dropdowns und Validierung.
    
    Returns:
    {
        "dimensionen": [...],
        "measures": [...],
        "standorte": [...],
        "kostenstellen": [...],
        "konto_ebenen": [...]
    }
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Dimensionen
            dimensionen = [
                {
                    "id": "zeit",
                    "name": "Zeit",
                    "description": "Zeit-Dimension (Jahr-Monat)",
                    "type": "date"
                },
                {
                    "id": "standort",
                    "name": "Standort",
                    "description": "Standort-Dimension (DEG, HYU, LAN)",
                    "type": "string"
                },
                {
                    "id": "kst",
                    "name": "Kostenstelle",
                    "description": "Kostenstellen-Dimension (0-7)",
                    "type": "integer"
                },
                {
                    "id": "konto",
                    "name": "Konto",
                    "description": "Konten-Dimension (Kontonummer)",
                    "type": "integer"
                }
            ]
            
            # Measures
            measures = [
                {
                    "id": "betrag",
                    "name": "Betrag",
                    "description": "Betrag in Euro",
                    "format": "currency",
                    "unit": "€"
                },
                {
                    "id": "menge",
                    "name": "Menge",
                    "description": "Menge (Anzahl)",
                    "format": "number",
                    "unit": ""
                }
            ]
            
            # Standorte
            cursor.execute("""
                SELECT standort_id, standort_code, standort_name
                FROM dim_standort
                ORDER BY standort_id
            """)
            standorte = []
            for row in cursor.fetchall():
                row_dict = row_to_dict(row, cursor)
                standorte.append({
                    "id": row_dict['standort_id'],
                    "code": row_dict['standort_code'],
                    "name": row_dict['standort_name']
                })
            
            # Kostenstellen
            cursor.execute("""
                SELECT DISTINCT kst_id
                FROM dim_kostenstelle
                ORDER BY kst_id
            """)
            kostenstellen = []
            for row in cursor.fetchall():
                row_dict = row_to_dict(row, cursor)
                kostenstellen.append({
                    "id": row_dict['kst_id'],
                    "name": f"KST {row_dict['kst_id']}"
                })
            
            # Konto-Ebenen (Ebene 3)
            cursor.execute("""
                SELECT DISTINCT ebene3 as id
                FROM dim_konto
                WHERE ebene3 IS NOT NULL
                  AND ebene3 IN (400, 700, 800, 830, 840)
                ORDER BY ebene3
            """)
            konto_ebenen = []
            ebene_names = {
                400: "Kosten",
                700: "Einsatz",
                800: "Umsatz",
                830: "Umsatz Service",
                840: "Umsatz Service"
            }
            for row in cursor.fetchall():
                row_dict = row_to_dict(row, cursor)
                ebene_id = row_dict['id']
                konto_ebenen.append({
                    "id": ebene_id,
                    "name": ebene_names.get(ebene_id, f"Ebene {ebene_id}")
                })
            
            # Zeit-Werte (letzte 12 Monate)
            cursor.execute("""
                SELECT DISTINCT jahr_monat
                FROM dim_zeit
                ORDER BY jahr_monat DESC
                LIMIT 12
            """)
            zeit_values = [row_to_dict(row, cursor)['jahr_monat'] for row in cursor.fetchall()]
            
            # Zeit-Dimension mit Werten erweitern
            for dim in dimensionen:
                if dim['id'] == 'zeit':
                    dim['values'] = zeit_values
                    dim['min'] = min(zeit_values) if zeit_values else None
                    dim['max'] = max(zeit_values) if zeit_values else None
            
            return jsonify({
                'dimensionen': dimensionen,
                'measures': measures,
                'standorte': standorte,
                'kostenstellen': kostenstellen,
                'konto_ebenen': konto_ebenen
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
