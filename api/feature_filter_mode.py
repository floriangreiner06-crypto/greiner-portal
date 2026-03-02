"""
Filter-Modus für Seiten mit Verkäufer-Filter (Auftragseingang, Auslieferungen, OPOS).
Pro Feature + Rolle: own_only | own_default | all_filterable.
"""
from api.db_utils import db_session

FEATURE_FILTER_FEATURES = ('auftragseingang', 'auslieferungen', 'opos', 'werkstatt_leistungsuebersicht')


def get_filter_mode(role_name: str, feature_name: str) -> str:
    """
    Liefert den konfigurierten Filter-Modus für (Rolle, Feature).
    Return: 'own_only' | 'own_default' | 'all_filterable'
    """
    if feature_name not in FEATURE_FILTER_FEATURES:
        return 'all_filterable'
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT filter_mode FROM feature_filter_mode WHERE feature_name = %s AND role_name = %s',
                (feature_name, role_name)
            )
            row = cursor.fetchone()
        if row:
            return row[0] if hasattr(row, '__getitem__') else row.filter_mode
        if role_name == 'verkauf' and feature_name in FEATURE_FILTER_FEATURES:
            return 'own_only'
        return 'all_filterable'
    except Exception:
        return 'all_filterable'
