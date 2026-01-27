# Motocost API-Keys anfragen - Vorlage

**TAG:** 212  
**Datum:** 2026-01-26

---

## 📧 EMAIL-VORLAGE

**An:** [Kontakt von motocost/freund]  
**Betreff:** API-Zugriff für auto1.com Angebote - Integration in DRIVE Portal

**Text:**

Hallo [Name],

vielen Dank für die Bereitstellung des motocost-Dashboards! Die Daten sind sehr hilfreich für unsere Zukäufer Rolf und Anton.

Wir möchten die Daten gerne in unser internes DRIVE Portal integrieren, damit Rolf und Anton direkt dort arbeiten können, ohne zwischen Systemen wechseln zu müssen.

**Frage:** Gibt es die Möglichkeit, einen **API-Key** oder **Service-Account** für programmatischen Zugriff auf die Grafana-Daten zu erhalten?

**Anforderungen:**
- Zugriff auf die MongoDB-Datenquelle (`de3b0tgjwgm4gb`)
- Abfrage der Fahrzeugdaten via `/api/ds/query`
- Automatischer Import in unser System (1x täglich)

**Alternativ:**
- Gibt es eine Export-Funktion (CSV/JSON)?
- Oder einen anderen Weg für den Datenzugriff?

Vielen Dank für deine Unterstützung!

---

## ✅ VORTEILE VON API-KEYS

1. **Stabil:** Keine Abhängigkeit von Browser/UI-Änderungen
2. **Schnell:** Direkter API-Zugriff ohne Browser-Overhead
3. **Zuverlässig:** Keine Timeouts oder Session-Probleme
4. **Wartungsarm:** Einmal eingerichtet, läuft stabil
5. **Skalierbar:** Kann für mehrere Anwendungen genutzt werden

---

## 📝 ALTERNATIVEN (falls keine API-Keys)

### Option A: Manueller Export + Import ⭐⭐⭐

**Vorgehen:**
1. Rolf/Anton exportieren täglich Daten aus Dashboard (CSV/Excel)
2. Upload in DRIVE Portal
3. Automatische Verarbeitung

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Stabil (keine Browser-Automation)
- ✅ Keine API-Abhängigkeit

**Nachteile:**
- ⚠️ Manueller Schritt nötig (1x täglich)
- ⚠️ Nicht vollautomatisch

**Aufwand:** 2-3 Stunden (Upload-Funktion + Import-Logik)

---

### Option B: Hybrid (Export + Browser-Automation als Fallback) ⭐

**Vorgehen:**
1. Primär: Manueller Export
2. Fallback: Browser-Automation (nur wenn Export fehlt)

**Vorteile:**
- ✅ Automatisch, wenn möglich
- ✅ Fallback vorhanden

**Nachteile:**
- ❌ Komplexer
- ❌ Browser-Automation bleibt instabil

**Aufwand:** 1-2 Wochen (Browser-Automation + Fallback-Logik)

---

## 🎯 EMPFEHLUNG

**1. PRIO: API-Keys anfragen** ⭐⭐⭐
- Beste Lösung
- Stabil und wartungsarm
- Aufwand: 1-2 Tage (nach Erhalt der Keys)

**2. FALLBACK: Manueller Export** ⭐⭐
- Falls keine API-Keys verfügbar
- Einfach und stabil
- Aufwand: 2-3 Stunden

**3. NICHT EMPFOHLEN: Browser-Automation ohne API-Keys** ❌
- Zu instabil für produktiven Betrieb
- Hoher Wartungsaufwand
- Nicht zuverlässig

---

**Status:** ⏳ Warte auf Antwort bezüglich API-Keys
