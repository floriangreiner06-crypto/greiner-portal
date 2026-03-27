# DRIVE - Data-driven Real-time Intelligence for Vehicle Excellence

**Projekt:** Autohaus Greiner GmbH
**Initiator:** Florian Greiner
**Start:** TAG 119 (Dezember 2025)
**Status:** Produktiv

---

## Vision

DRIVE ist ein datengetriebenes Projekt zur Optimierung der Werkstatt-Prozesse bei Autohaus Greiner. Ziel ist es, durch Machine Learning und echte Betriebsdaten bessere Entscheidungen zu ermöglichen - für Mitarbeiter, Werkstattleiter und Management.

**Kernidee:** Die Herstellervorgaben (AW-Zeiten) sind oft unrealistisch. DRIVE lernt aus echten Stempeluhr-Daten, wie lange Arbeiten tatsächlich dauern.

---

## Komponenten

### 1. ML-Modell (XGBoost V5.1)
- **Algorithmus:** XGBoost (Gradient Boosting)
- **Training:** 5.721 qualitätsgeprüfte Aufträge (2023-2025)
- **Features:** 20 (Fahrzeug, Auftrag, Zeit, Mechaniker)
- **Performance:** R² = 0.68, MAE = 45 min

### 2. Datenquellen
| Quelle | Daten | Verwendung |
|--------|-------|------------|
| **Locosoft times** | Echte Stempeluhr-Zeiten | IST-Dauer (Gold!) |
| **Locosoft labours** | Herstellervorgabe (AW) | SOLL-Dauer |
| **Locosoft vehicles** | Fahrzeugdaten | Features |
| **Locosoft employees** | Mechaniker-Daten | Features |

### 3. Qualitätsfilter (V5)
- Mindestens 2 Stempel pro Auftrag
- Effizienz-Ratio 0.3x - 8.0x
- Mindestens 0.5 Stempel pro Position
- Konfidenz-Score (0-100) pro Datensatz

---

## Benefits für das Team

### Werkstattleiter
| Vorher | Nachher |
|--------|---------|
| Überraschungen bei Zeitüberschreitungen | Frühwarnung "unterbewertet" |
| Manuelle Kapazitätsplanung | ML-basierte Auslastungsprognose |
| Reaktives Eingreifen | Proaktive Planung |

### Serviceberater
| Vorher | Nachher |
|--------|---------|
| Unrealistische Kundenzusagen | Realistische Zeitschätzung |
| Herstellervorgabe = Wahrheit | ML-Korrektur der Vorgabe |
| Beschwerden bei Verzögerung | Bessere Erwartungshaltung |

### Mechaniker
| Vorher | Nachher |
|--------|---------|
| Druck durch unrealistische AW | Faire Bewertung |
| "Warum brauchst du so lange?" | Daten zeigen: Normal! |
| Gefühlte Ineffizienz | Objektive Effizienz-Messung |

### Controlling
| Vorher | Nachher |
|--------|---------|
| Hohe "Leerlauf"-Quote (fake) | Echte Auslastung |
| AW-basierte Produktivität | Stempeluhr-basierte Realität |
| Äpfel-Birnen-Vergleich | Faire Mechaniker-Bewertung |

---

## Technische Details

### Feature-Vektor (21 Features)
```
1. soll_dauer_min      - Herstellervorgabe in Minuten
2. soll_aw             - Herstellervorgabe in AW
3. betrieb             - Standort (1=DEG, 2=Hyundai, 3=Landau)
4. anzahl_positionen   - Arbeitspositionen pro Auftrag
5. anzahl_teile        - Ersatzteile pro Auftrag
6. charge_type         - Lohnart/Kostenträger
7. urgency             - Dringlichkeit (0-3)
8. wochentag           - 0=Montag, 6=Sonntag
9. monat               - 1-12
10. start_stunde       - Arbeitsbeginn (Stunde)
11. kalenderwoche      - KW 1-52
12. power_kw           - Motorleistung
13. cubic_capacity     - Hubraum
14. km_stand           - Kilometerstand
15. fahrzeug_alter_jahre - Fahrzeugalter
16. productivity_factor - Mechaniker-Produktivität
17. years_experience   - Berufserfahrung
18. meister            - Meisterqualifikation (0/1)
19. marke_encoded      - Fahrzeugmarke (encoded)
20. auftragstyp_encoded - Auftragstyp (encoded)
21. labour_type_encoded - Arbeitstyp (encoded)
```

### Dateien
```
scripts/ml/
├── extract_features_v5.py     # Feature-Extraktion mit Qualitätsfilter
├── train_auftragsdauer_model_v2.py  # Training (XGBoost, LightGBM, RF, GB)

data/ml/
├── auftraege_features_v5.csv  # Trainingsdaten (14k Aufträge)
├── models/
│   ├── auftragsdauer_model.pkl → v2_tag119.pkl  # Symlink
│   ├── label_encoders_v2_tag119.pkl
│   └── model_metadata_v2_tag119.pkl

api/
├── werkstatt_live_api.py      # DRIVE V5 Integration (Zeile 3086ff)
├── ml_api.py                  # ML REST API
```

### Scheduler-Jobs
```
03:00 - ml_extract_features    # V5 Feature-Extraktion
03:15 - ml_retrain             # LightGBM Training
```

---

## Performance-Vergleich

### ML vs Herstellervorgabe (Woche 09.-12.12.2025)
| Metrik | Herstellervorgabe | DRIVE ML | Verbesserung |
|--------|-------------------|----------|--------------|
| MAE | 228 min | 115 min | **-49%** |
| Besser bei | 24% Aufträge | 76% Aufträge | **+52pp** |

### Modell-Evolution
| Version | Datenquelle | R² | MAE | Datensätze |
|---------|-------------|-----|-----|------------|
| V2 | labours (fake IST) | 1.0 | - | - |
| V3 | Durchlaufzeit | 0.41 | - | 5k |
| V4 | Stempeluhr (roh) | 0.46 | 86 min | 18k |
| V5 | Stempeluhr (gefiltert) | 0.55 | 77 min | 14k |
| **V5.1** | **Stempeluhr (DISTINCT fix)** | **0.68** | **45 min** | **5.7k** |

---

## Frontend-Integration

### Kapazitätsplanung
- Spalte "ML-Prognose" neben Herstellervorgabe
- Farbcodierung: Rot = unterbewertet, Grün = überbewertet

### Werkstatt-Aufträge
- ML-Status pro Auftrag
- Potenzial in AW angezeigt

### Stempeluhr
- ML-Indikator bei laufenden Aufträgen
- Warnung wenn SOLL überschritten

---

## Roadmap

### Erledigt (TAG 119)
- [x] V5 Feature-Extraktion mit Qualitätsfilter
- [x] LightGBM Training (R² = 0.55)
- [x] API-Integration (werkstatt_live_api.py)
- [x] Scheduler-Jobs (03:00, 03:15)

### Geplant
- [ ] Mechaniker-spezifische Produktivitätsfaktoren aus Stempeluhr
- [ ] Gudat-Integration: ML-Vorhersage bei Terminbuchung
- [ ] Dashboard-Widget: Tagesauslastung ML-basiert
- [ ] Historische Genauigkeits-Analyse

---

## Kontakt

**Projekt-Owner:** Florian Greiner
**Technische Umsetzung:** Claude (Anthropic)
**Dokumentation:** TAG 119 (2025-12-12)

---

*DRIVE - Weil echte Daten besser sind als Herstellervorgaben.*
