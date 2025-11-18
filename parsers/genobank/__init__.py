"""
Genobank Parser Module
======================
Spezialisierte Parser für verschiedene Genobank-PDF-Formate

Parser:
- GenobankTagesauszugParser: Für tägliche Auszüge (alle Monate/Jahre)
- GenobankKontoauszugParser: Für monatliche Kontoauszüge (alle Monate/Jahre)
"""

from .genobank_base import GenobankBaseParser
from .genobank_tagesauszug_parser import GenobankTagesauszugParser
from .genobank_kontoauszug_parser import GenobankKontoauszugParser

__all__ = [
    'GenobankBaseParser',
    'GenobankTagesauszugParser',
    'GenobankKontoauszugParser'
]
