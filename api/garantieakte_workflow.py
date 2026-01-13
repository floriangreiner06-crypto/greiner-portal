"""
Garantieakte Workflow
=====================
TAG 173: Speichert vollständige Garantieakte in Ordnerstruktur
- Ordner: {kunde}_{Auftragsnummer}
- Dateien: Arbeitskarte-PDF, Bilder (einzeln), Terminblatt
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

# Windows-Pfad: \\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie
# Separater Mount-Punkt für Hyundai Garantie (TAG 173)
BASE_PATH_OPTIONS = [
    "/mnt/hyundai-garantie",  # Separater Mount (\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie)
    "/mnt/buchhaltung/DigitalesAutohaus/Hyundai_Garantie",  # Über buchhaltung Mount (Fallback)
    "/mnt/DigitalesAutohaus/Hyundai_Garantie",  # Direkt gemountet (Fallback)
    "/mnt/greiner-portal-sync/../DigitalesAutohaus/Hyundai_Garantie",  # Relativ zu Sync (Fallback)
]
# Fallback: Falls Mount nicht verfügbar, verwende Sync-Ordner
FALLBACK_PATH = "/mnt/greiner-portal-sync/Hyundai_Garantie"


def sanitize_filename(name: str) -> str:
    """Bereinigt Dateinamen für Windows"""
    # Ersetze ungültige Zeichen
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Entferne führende/abschließende Punkte und Leerzeichen
    name = name.strip('. ')
    return name


def create_garantieakte_ordner(
    kunde_name: str,
    auftragsnummer: int,
    base_path: str = None
) -> str:
    """
    Erstellt Ordner für Garantieakte.
    
    Args:
        kunde_name: Name des Kunden (z.B. "Kopra-Schäfer, Dr. Monika")
        auftragsnummer: Auftragsnummer
        base_path: Basis-Pfad (default: BASE_PATH)
    
    Returns:
        Pfad zum erstellten Ordner
    """
    import subprocess
    
    if base_path is None:
        # Prüfe verschiedene Pfade
        base_path = None
        for path_option in BASE_PATH_OPTIONS:
            # Prüfe ob Basis-Verzeichnis existiert
            base_dir = os.path.dirname(path_option)
            if os.path.exists(base_dir):
                base_path = path_option
                break
        
        if not base_path:
            base_path = FALLBACK_PATH
            logger.warning(f"DigitalesAutohaus nicht gemountet, verwende FALLBACK_PATH: {base_path}")
            logger.info(f"Bitte mounte: \\\\srvrdb01\\Allgemein\\DigitalesAutohaus nach /mnt/DigitalesAutohaus")
    
    # Erstelle Basis-Ordner falls nicht vorhanden
    try:
        os.makedirs(base_path, exist_ok=True)
    except PermissionError as e:
        logger.warning(f"Konnte Basis-Ordner nicht erstellen: {e}")
        raise
    
    # Bereinige Kundenname für Ordner
    kunde_clean = sanitize_filename(kunde_name)
    ordner_name = f"{kunde_clean}_{auftragsnummer}"
    ordner_path = os.path.join(base_path, ordner_name)
    
    # Erstelle Ordner
    try:
        os.makedirs(ordner_path, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Konnte Ordner nicht erstellen: {e}")
        logger.error(f"Bitte prüfe Windows-Berechtigungen für: {base_path}")
        raise
    
    logger.info(f"Ordner erstellt: {ordner_path}")
    return ordner_path


def save_arbeitskarte_pdf(
    ordner_path: str,
    pdf_bytes: bytes,
    auftragsnummer: int
) -> str:
    """
    Speichert Arbeitskarte-PDF.
    
    Returns:
        Pfad zur gespeicherten Datei
    """
    filename = f"Arbeitskarte_{auftragsnummer}.pdf"
    file_path = os.path.join(ordner_path, filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    logger.info(f"Arbeitskarte-PDF gespeichert: {file_path}")
    return file_path


def save_anhang(
    ordner_path: str,
    anhang_data: Dict,
    file_bytes: bytes,
    index: int = None
) -> str:
    """
    Speichert einen Anhang (Bild, PDF, etc.) einzeln.
    
    Args:
        ordner_path: Pfad zum Ordner
        anhang_data: Dict mit 'name', 'id', 'file_type'
        file_bytes: Datei-Daten als Bytes
        index: Optionaler Index für Dateinamen
    
    Returns:
        Pfad zur gespeicherten Datei
    """
    original_name = anhang_data.get('name', f'Anhang_{anhang_data.get("id", "unknown")}')
    file_type = anhang_data.get('file_type', '')
    
    # Bestimme Dateiendung aus file_type oder original_name
    if file_type == 'application/pdf':
        ext = '.pdf'
    elif 'jpeg' in file_type or 'jpg' in file_type.lower():
        ext = '.jpg'
    elif 'png' in file_type.lower():
        ext = '.png'
    elif 'gif' in file_type.lower():
        ext = '.gif'
    elif 'word' in file_type.lower() or 'msword' in file_type.lower():
        ext = '.doc'
    elif 'excel' in file_type.lower() or 'spreadsheet' in file_type.lower():
        ext = '.xls'
    else:
        # Versuche aus original_name
        if '.' in original_name:
            ext = os.path.splitext(original_name)[1]
        else:
            ext = ''  # Keine Endung
    
    # Bereinige Dateiname
    name_clean = sanitize_filename(original_name)
    if ext and not name_clean.endswith(ext):
        # Entferne alte Endung falls vorhanden
        name_without_ext = os.path.splitext(name_clean)[0]
        name_clean = name_without_ext + ext
    
    # Optional: Index voranstellen für Sortierung
    if index is not None:
        filename = f"{index:02d}_{name_clean}"
    else:
        filename = name_clean
    
    file_path = os.path.join(ordner_path, filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    file_type_label = 'PDF' if ext == '.pdf' else 'Bild' if file_type.startswith('image/') else 'Dokument'
    logger.info(f"{file_type_label} gespeichert: {file_path} ({len(file_bytes) / 1024:.1f} KB)")
    return file_path


# Alias für Rückwärtskompatibilität
def save_bild(ordner_path: str, bild_data: Dict, image_bytes: bytes, index: int = None) -> str:
    """Alias für save_anhang (Rückwärtskompatibilität)"""
    return save_anhang(ordner_path, bild_data, image_bytes, index)


def save_terminblatt(
    ordner_path: str,
    terminblatt_data: Dict,
    pdf_bytes: bytes,
    auftragsnummer: int
) -> Optional[str]:
    """
    Speichert Terminblatt-PDF.
    
    Returns:
        Pfad zur gespeicherten Datei oder None
    """
    if not terminblatt_data or not pdf_bytes:
        return None
    
    name = terminblatt_data.get('name', f'Terminblatt_{auftragsnummer}')
    name_clean = sanitize_filename(name)
    
    if not name_clean.endswith('.pdf'):
        name_clean = os.path.splitext(name_clean)[0] + '.pdf'
    
    filename = f"Terminblatt_{name_clean}"
    file_path = os.path.join(ordner_path, filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    logger.info(f"Terminblatt gespeichert: {file_path}")
    return file_path


def create_garantieakte_vollstaendig(
    order_number: int,
    kunde_name: str,
    arbeitskarte_pdf: bytes,
    anhaenge: List[Dict] = None,
    terminblatt_data: Dict = None,
    terminblatt_pdf: bytes = None,
    gudat_session: requests.Session = None,
    base_path: str = None
) -> Dict:
    """
    Erstellt vollständige Garantieakte in Ordnerstruktur.
    
    Args:
        order_number: Auftragsnummer
        kunde_name: Name des Kunden
        arbeitskarte_pdf: Arbeitskarte als PDF-Bytes
        anhaenge: Liste von Anhang-Dicts mit 'id', 'name', 'file_type' (Bilder, PDFs, etc.)
        terminblatt_data: Terminblatt-Dict (optional)
        terminblatt_pdf: Terminblatt als PDF-Bytes (optional)
        gudat_session: GUDAT-Session für Anhang-Downloads
        base_path: Basis-Pfad (optional)
    
    Returns:
        Dict mit 'success', 'ordner_path', 'dateien'
    """
    try:
        # 1. Erstelle Ordner
        ordner_path = create_garantieakte_ordner(
            kunde_name,
            order_number,
            base_path
        )
        
        dateien = []
        
        # 2. Speichere Arbeitskarte-PDF
        arbeitskarte_path = save_arbeitskarte_pdf(
            ordner_path,
            arbeitskarte_pdf,
            order_number
        )
        dateien.append({
            'typ': 'Arbeitskarte',
            'pfad': arbeitskarte_path,
            'groesse_kb': len(arbeitskarte_pdf) / 1024
        })
        
        # 3. Lade und speichere ALLE Anhänge einzeln (Bilder, PDFs, etc.)
        if anhaenge and gudat_session:
            from api.arbeitskarte_vollstaendig import download_document
            
            # Sortiere Anhänge: Bilder zuerst, dann PDFs, dann andere
            def sort_key(anhang):
                file_type = anhang.get('file_type', '')
                if file_type.startswith('image/'):
                    return (0, anhang.get('name', ''))
                elif file_type == 'application/pdf':
                    return (1, anhang.get('name', ''))
                else:
                    return (2, anhang.get('name', ''))
            
            sorted_anhaenge = sorted(anhaenge, key=sort_key)
            
            for idx, anhang in enumerate(sorted_anhaenge, 1):
                document_id = anhang.get('id')
                if not document_id:
                    continue
                
                # Lade Anhang
                file_bytes = download_document(document_id, gudat_session)
                if not file_bytes:
                    logger.warning(f"Anhang {anhang.get('name')} konnte nicht geladen werden")
                    continue
                
                # Bestimme Typ für Rückgabe
                file_type = anhang.get('file_type', '')
                if file_type == 'application/pdf':
                    typ_label = 'PDF'
                elif file_type.startswith('image/'):
                    typ_label = 'Bild'
                else:
                    typ_label = 'Dokument'
                
                # Speichere Anhang
                anhang_path = save_anhang(
                    ordner_path,
                    anhang,
                    file_bytes,
                    index=idx
                )
                dateien.append({
                    'typ': typ_label,
                    'pfad': anhang_path,
                    'groesse_kb': len(file_bytes) / 1024,
                    'name': anhang.get('name')
                })
        
        # 4. Speichere Terminblatt (falls vorhanden)
        if terminblatt_data and terminblatt_pdf:
            terminblatt_path = save_terminblatt(
                ordner_path,
                terminblatt_data,
                terminblatt_pdf,
                order_number
            )
            if terminblatt_path:
                dateien.append({
                    'typ': 'Terminblatt',
                    'pfad': terminblatt_path,
                    'groesse_kb': len(terminblatt_pdf) / 1024
                })
        
        # 5. Speichere Metadaten (Ersteller, Datum)
        try:
            from flask_login import current_user
            ersteller = None
            if current_user and hasattr(current_user, 'username'):
                ersteller = current_user.username
            elif current_user and hasattr(current_user, 'id'):
                ersteller = str(current_user.id)
            
            if ersteller:
                from api.garantie_auftraege_api import save_garantieakte_metadata
                save_garantieakte_metadata(order_number, ordner_path, ersteller)
        except Exception as e:
            logger.warning(f"Fehler beim Speichern der Metadaten: {e}")
        
        # Windows-Pfad für Rückgabe
        if '/hyundai-garantie' in ordner_path:
            # \\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\{kunde}_{nummer}
            windows_path = ordner_path.replace('/mnt/hyundai-garantie', r'\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie')
            windows_path = windows_path.replace('/', '\\')
        elif '/buchhaltung/DigitalesAutohaus' in ordner_path:
            # \\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\{kunde}_{nummer}
            windows_path = ordner_path.replace('/mnt/buchhaltung/DigitalesAutohaus', '\\\\srvrdb01\\Allgemein\\DigitalesAutohaus')
            windows_path = windows_path.replace('/', '\\')
        elif '/DigitalesAutohaus' in ordner_path:
            # \\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie\{kunde}_{nummer}
            windows_path = ordner_path.replace('/mnt/DigitalesAutohaus', '\\\\srvrdb01\\Allgemein\\DigitalesAutohaus')
            windows_path = windows_path.replace('/', '\\')
        elif '/greiner-portal-sync' in ordner_path:
            # Fallback: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\Hyundai_Garantie\{kunde}_{nummer}
            windows_path = ordner_path.replace('/mnt/greiner-portal-sync', '\\\\Srvrdb01\\Allgemein\\Greiner Portal\\Greiner_Portal_NEU\\Server')
            windows_path = windows_path.replace('/', '\\')
        else:
            windows_path = ordner_path.replace('/', '\\')
        
        return {
            'success': True,
            'ordner_path': ordner_path,
            'windows_path': windows_path,
            'dateien': dateien,
            'anzahl_dateien': len(dateien)
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Garantieakte: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
