#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parsers Package für Bankenspiegel 3.0
=====================================
Bank-spezifische PDF-Parser

Unterstützte Banken:
- Sparkasse
- VR-Bank / Genobank / Volksbank
- HypoVereinsbank

Author: Claude AI
Version: 3.0
Date: 2025-11-06
"""

from .base_parser import BaseParser, Transaction
from .sparkasse_parser import SparkasseParser
from .vrbank_parser import VRBankParser
from .hypovereinsbank_parser import HypovereinsbankParser
from .parser_factory import ParserFactory

__all__ = [
    'BaseParser',
    'Transaction',
    'SparkasseParser',
    'VRBankParser',
    'HypovereinsbankParser',
    'ParserFactory'
]

__version__ = '3.0'
