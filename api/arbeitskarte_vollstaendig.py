"""
Vollständige Garantieakte PDF-Generator
========================================
TAG 173: Generiert vollständige Akte mit Arbeitskarte, Terminblatt und Bildern
- Max. 20MB Gesamtgröße
- Bilder werden optimiert
- Terminblatt aus GUDAT
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
import requests
import os
import tempfile

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

MAX_TOTAL_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_IMAGE_WIDTH = 15 * cm  # Max. Breite für Bilder im PDF
MAX_IMAGE_HEIGHT = 10 * cm  # Max. Höhe für Bilder im PDF
JPEG_QUALITY = 85  # JPEG-Qualität (0-100)


def optimize_image(image_data: bytes, max_size_mb: float = 1.0) -> bytes:
    """
    Optimiert ein Bild auf max. Größe.
    
    Args:
        image_data: Original-Bild als Bytes
        max_size_mb: Maximale Größe in MB
        
    Returns:
        Optimiertes Bild als Bytes
    """
    if not PIL_AVAILABLE:
        # Fallback: Original zurückgeben
        return image_data
    
    try:
        # Lade Bild
        img = Image.open(BytesIO(image_data))
        
        # Konvertiere zu RGB falls nötig (für JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Prüfe aktuelle Größe
        output = BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        current_size = len(output.getvalue())
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        if current_size <= max_size_bytes:
            return output.getvalue()
        
        # Reduziere Größe schrittweise
        quality = JPEG_QUALITY
        width, height = img.size
        
        while current_size > max_size_bytes and quality > 30:
            quality -= 5
            
            # Reduziere auch Auflösung wenn nötig
            if quality < 50:
                width = int(width * 0.9)
                height = int(height * 0.9)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            current_size = len(output.getvalue())
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Fehler beim Optimieren des Bildes: {e}")
        return image_data


def download_document(document_id: int, session: requests.Session, base_url: str = None) -> bytes:
    """
    Lädt ein Dokument (Bild, PDF, etc.) von GUDAT herunter.
    
    Args:
        document_id: Dokument-ID aus GUDAT
        session: Requests-Session mit GUDAT-Cookies
        base_url: Base-URL für GUDAT (default: werkstattplanung.net)
    
    Returns:
        Dokument-Daten als Bytes
    """
    try:
        if base_url is None:
            base_url = "https://werkstattplanung.net/greiner/deggendorf/kic"
        
        # URL-Format: /view_document/local/{document_id}?{timestamp}
        import time
        timestamp = int(time.time())
        url = f"{base_url}/view_document/local/{document_id}?{timestamp}"
        
        response = session.get(url, timeout=30)  # Längeres Timeout für größere Dateien
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Fehler beim Herunterladen von Dokument {document_id}: {e}")
        return None


# Alias für Rückwärtskompatibilität
def download_image(document_id: int, session: requests.Session, base_url: str = None) -> bytes:
    """Alias für download_document (Rückwärtskompatibilität)"""
    return download_document(document_id, session, base_url)


def generate_vollstaendige_akte_pdf(
    data: dict,
    bilder: list = None,
    terminblatt: bytes = None,
    gudat_session: requests.Session = None
) -> bytes:
    """
    Generiert vollständige Garantieakte mit Arbeitskarte, Terminblatt und Bildern.
    
    Args:
        data: Dict mit Arbeitskarte-Daten (wie generate_arbeitskarte_pdf)
        bilder: Liste von Bild-Dicts mit 'name', 'url', 'mime_type', 'size'
        terminblatt: Terminblatt als PDF-Bytes (optional)
    
    Returns:
        bytes: PDF-Inhalt (max. 20MB)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    temp_files = []  # Für Cleanup von temporären Bild-Dateien
    
    # Styles (wie in generate_arbeitskarte_pdf)
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#0066cc')
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=10,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT
    )
    
    # ========================================================================
    # TERMINBLATT (falls vorhanden)
    # ========================================================================
    if terminblatt:
        elements.append(Paragraph("TERMINBLATT", title_style))
        elements.append(Spacer(1, 0.5*cm))
        # TODO: Terminblatt-PDF einbinden (falls möglich)
        # Für jetzt: Hinweis
        elements.append(Paragraph(
            "<i>Terminblatt aus GUDAT vorhanden (separates PDF)</i>",
            normal_style
        ))
        elements.append(PageBreak())
    
    # ========================================================================
    # ARBEITSKARTE (wie bisher)
    # ========================================================================
    from api.arbeitskarte_pdf import generate_arbeitskarte_pdf
    
    # Generiere Arbeitskarte-PDF
    arbeitskarte_pdf = generate_arbeitskarte_pdf(data)
    
    # Füge Arbeitskarte-Inhalt hinzu
    # (Für jetzt: Einfache Version, später könnte man PDFs kombinieren)
    auftrag = data.get('locosoft', {}).get('auftrag', {})
    kunde = data.get('locosoft', {}).get('kunde', {})
    fahrzeug = data.get('locosoft', {}).get('fahrzeug', {})
    
    elements.append(Paragraph("ARBEITSKARTE", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Kopf-Daten (vereinfacht)
    kopf_data = [
        ['Auftragsnummer:', str(auftrag.get('nummer', '')), 'Kunde:', kunde.get('name', '')],
        ['Fahrzeug:', fahrzeug.get('kennzeichen', ''), 'VIN:', fahrzeug.get('vin', '')],
    ]
    
    kopf_table = Table(kopf_data, colWidths=[4*cm, 6*cm, 4*cm, 3*cm])
    kopf_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(kopf_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # GUDAT-Anmerkungen
    gudat = data.get('gudat')
    gudat_tasks = gudat.get('tasks', []) if gudat else []
    if gudat_tasks:
        elements.append(Paragraph("Diagnose durch Arbeitsausführenden", heading_style))
        for task in gudat_tasks:
            desc = task.get('description', '')
            if desc:
                for line in desc.split('\n'):
                    if line.strip():
                        elements.append(Paragraph(line.strip(), normal_style))
                elements.append(Spacer(1, 0.3*cm))
    
    elements.append(PageBreak())
    
    # ========================================================================
    # BILDER (einzeln, optimiert)
    # ========================================================================
    if bilder:
        elements.append(Paragraph("BILDER", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        total_size = 0
        # Verwende übergebene Session oder erstelle neue
        if gudat_session:
            session = gudat_session
        else:
            session = requests.Session()
        
        for idx, bild in enumerate(bilder, 1):
            document_id = bild.get('id')
            name = bild.get('name', f'Bild_{idx}')
            original_size = bild.get('size', 0)  # Kann None sein
            
            if not document_id:
                elements.append(Paragraph(
                    f"<i>Bild {idx}: {name} (ID nicht verfügbar)</i>",
                    normal_style
                ))
                continue
            
            # Lade und optimiere Bild
            image_data = download_image(document_id, session)
            if not image_data:
                elements.append(Paragraph(
                    f"<i>Bild {idx}: {name} (Download fehlgeschlagen)</i>",
                    normal_style
                ))
                continue
            
            # Optimiere Bild (max. 1MB pro Bild, damit Gesamtgröße < 20MB)
            optimized_data = optimize_image(image_data, max_size_mb=1.0)
            total_size += len(optimized_data)
            
            # Prüfe Gesamtgröße
            if total_size > MAX_TOTAL_SIZE * 0.9:  # 90% von 20MB
                elements.append(Paragraph(
                    f"<i>Weitere Bilder wurden ausgelassen (Größenlimit erreicht)</i>",
                    normal_style
                ))
                break
            
            # Erstelle temporäre Datei für ReportLab
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            tmp_file.write(optimized_data)
            tmp_path = tmp_file.name
            tmp_file.close()
            temp_files.append(tmp_path)  # Für späteres Cleanup
            
            try:
                # Lade Bild für ReportLab
                img = RLImage(tmp_path, width=MAX_IMAGE_WIDTH, height=MAX_IMAGE_HEIGHT)
                
                elements.append(Paragraph(f"<b>Bild {idx}: {name}</b>", heading_style))
                elements.append(img)
                elements.append(Spacer(1, 0.3*cm))
                
            except Exception as e:
                print(f"Fehler beim Einbinden von Bild {name}: {e}")
                elements.append(Paragraph(
                    f"<i>Bild {idx}: {name} (Fehler beim Einbinden)</i>",
                    normal_style
                ))
            
            # Seitenumbruch nach jedem 2. Bild
            if idx % 2 == 0:
                elements.append(PageBreak())
        
        # Session nur schließen, wenn wir sie erstellt haben
        if not gudat_session:
            session.close()
    
    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"<i>Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr | Auftrag #{data.get('order_number', '')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # PDF generieren
    try:
        doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
    finally:
        # Cleanup: Lösche temporäre Dateien
        for tmp_path in temp_files:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception as e:
                print(f"Fehler beim Löschen von {tmp_path}: {e}")
    
    # Prüfe finale Größe
    if len(pdf_bytes) > MAX_TOTAL_SIZE:
        print(f"⚠️  Warnung: PDF ist {len(pdf_bytes) / 1024 / 1024:.2f} MB (max. 20 MB)")
    
    return pdf_bytes
