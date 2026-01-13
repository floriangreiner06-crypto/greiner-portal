/**
 * KPI Help System - Zentrale Hilfe für alle KPIs
 * ===============================================
 * 
 * Bietet einheitliche Hilfe-Funktionalität für alle Features.
 * 
 * Verwendung:
 * 1. Help-Icon neben KPI anzeigen: <i class="bi bi-info-circle kpi-help-icon" data-kpi="leistungsgrad"></i>
 * 2. Help-System initialisieren: KPIHelp.init()
 * 
 * KPI-Definitionen werden zentral verwaltet und können pro Feature erweitert werden.
 * 
 * TAG 181 - Erstellt für Werkstatt-Dashboard, erweiterbar für alle Features
 */

class KPIHelp {
    constructor() {
        this.kpiDefinitions = {
            // Werkstatt-KPIs
            'leistungsgrad': {
                name: 'Leistungsgrad',
                formel: 'AW × 6 / Stempelzeit × 100',
                ziel: '≥ 100%',
                beschreibung: 'Wie schnell arbeitet der Mechaniker im Vergleich zur Kalkulation?',
                datengrundlage: 'Vorgabe-AW aus Rechnungen (labours) vs. gestempelte Zeit (times type=2)',
                beispiel: '10 AW Vorgabe, 8 AW gestempelt → 125% (schneller als kalkuliert)',
                schwellenwerte: {
                    gut: '≥ 85%',
                    warnung: '≥ 70%',
                    kritisch: '< 70%'
                },
                berechnung: 'Die Vorgabe-AW werden mit 6 multipliziert (1 AW = 6 Min), dann durch die gestempelte Zeit geteilt.'
            },
            'produktivitaet': {
                name: 'Produktivität',
                formel: 'Stempelzeit / Anwesenheit × 100',
                ziel: '≥ 90%',
                beschreibung: 'Wie viel der Anwesenheit wird produktiv auf Aufträge gestempelt?',
                datengrundlage: 'Gestempelte Zeit (times type=2) vs. Anwesenheit (times type=1)',
                beispiel: '8h anwesend, 7.2h gestempelt → 90% Produktivität',
                schwellenwerte: {
                    gut: '≥ 85%',
                    warnung: '≥ 75%',
                    kritisch: '< 75%'
                },
                berechnung: '10% "Verlust" ist normal für: Arbeitsplatz aufräumen, Werkzeug holen, Leerlauf morgens.'
            },
            'effizienz': {
                name: 'Effizienz',
                formel: 'Leistungsgrad × Produktivität / 100',
                ziel: '≥ 85%',
                beschreibung: 'Gesamtproduktivität - was kommt am Ende wirklich raus?',
                datengrundlage: 'Kombination aus Leistungsgrad und Produktivität',
                beispiel: '100% Leistung × 90% Produktivität = 90% Effizienz',
                schwellenwerte: {
                    gut: '≥ 65%',
                    warnung: '≥ 55%',
                    kritisch: '< 55%'
                },
                berechnung: 'Multiplikation von Leistungsgrad und Produktivität. Zeigt die Gesamtleistung.'
            },
            'anwesenheitsgrad': {
                name: 'Anwesenheitsgrad',
                formel: 'Anwesende Stunden / Bezahlte Stunden × 100',
                ziel: '≥ 79%',
                beschreibung: 'Wie viel der bezahlten Zeit ist der Mitarbeiter tatsächlich anwesend?',
                datengrundlage: 'Anwesenheit (times type=1) vs. bezahlte Zeit (Arbeitstage × 8h)',
                beispiel: '6.5h anwesend von 8h bezahlt → 81.3% Anwesenheitsgrad',
                schwellenwerte: {
                    gut: '≥ 75%',
                    warnung: '≥ 65%',
                    kritisch: '< 65%'
                },
                berechnung: 'Bezahlte Zeit = Anzahl Arbeitstage × 8 Stunden. Abzüge für Urlaub, Krankheit, Schulung, Feiertage sind normal.',
                hinweis: 'Bei 40h/Woche: 220 Arbeitstage × 8h = 1.760h bezahlt, abzüglich ~370h (Urlaub, Krank, etc.) = ~1.390h anwesend → 79%',
                ueber_100_prozent: 'Ein Anwesenheitsgrad über 100% bedeutet, dass der Mechaniker mehr Stunden anwesend war als bezahlt (z.B. Überstunden, Samstagsarbeit, Mehrarbeit). Das ist möglich und zeigt, dass der Mitarbeiter mehr arbeitet als vertraglich vereinbart.'
            },
            'entgangener_umsatz': {
                name: 'Entgangener Umsatz',
                formel: '(Gestempelte-AW - Vorgabe-AW) × AW-Preis',
                ziel: '0 €',
                beschreibung: 'Umsatzverlust bei Überzeiten (wenn langsamer als kalkuliert)',
                datengrundlage: 'Differenz zwischen gestempelter und vorgabe AW, multipliziert mit AW-Preis (Standard: 119 €/Std)',
                beispiel: '10 AW Vorgabe, 12 AW gestempelt, 11.90€/AW → 23.80€ entgangener Umsatz',
                schwellenwerte: {
                    gut: '= 0 €',
                    warnung: '< 5.000 €',
                    kritisch: '≥ 5.000 €'
                },
                berechnung: 'Nur bei Überzeiten! Schneller arbeiten = 0€ (kein "Gewinn", aber auch kein Verlust).'
            }
        };
    }

    /**
     * Initialisiert das Help-System
     */
    init() {
        // Event-Listener für alle Help-Icons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('kpi-help-icon') || e.target.closest('.kpi-help-icon')) {
                const icon = e.target.classList.contains('kpi-help-icon') ? e.target : e.target.closest('.kpi-help-icon');
                const kpiName = icon.getAttribute('data-kpi');
                if (kpiName) {
                    this.showHelp(kpiName);
                }
            }
        });
    }

    /**
     * Zeigt Help-Modal für einen KPI
     */
    showHelp(kpiName) {
        const kpi = this.kpiDefinitions[kpiName];
        if (!kpi) {
            console.warn(`KPI "${kpiName}" nicht gefunden`);
            return;
        }

        // Modal erstellen oder verwenden
        let modal = document.getElementById('kpiHelpModal');
        if (!modal) {
            modal = this.createModal();
            document.body.appendChild(modal);
        }

        // Inhalt füllen
        const modalBody = modal.querySelector('#kpiHelpModalBody');
        modalBody.innerHTML = this.renderKPIHelp(kpi);

        // Modal anzeigen
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    /**
     * Erstellt das Help-Modal (einmalig)
     */
    createModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'kpiHelpModal';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-info-circle"></i> KPI-Erklärung
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="kpiHelpModalBody">
                        <!-- Wird dynamisch gefüllt -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Schließen</button>
                    </div>
                </div>
            </div>
        `;
        return modal;
    }

    /**
     * Rendert den Help-Inhalt für einen KPI
     */
    renderKPIHelp(kpi) {
        return `
            <div class="kpi-help-content">
                <!-- Header -->
                <div class="mb-4">
                    <h4 class="mb-2">${kpi.name}</h4>
                    <p class="text-muted mb-0">${kpi.beschreibung}</p>
                </div>

                <!-- Formel -->
                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong><i class="bi bi-calculator"></i> Berechnung</strong>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <span class="text-muted">Formel:</span>
                            <code class="ms-2">${kpi.formel}</code>
                        </div>
                        ${kpi.berechnung ? `<p class="mb-0 small text-muted">${kpi.berechnung}</p>` : ''}
                    </div>
                </div>

                <!-- Ziel & Schwellenwerte -->
                <div class="row mb-3">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header bg-success text-white">
                                <strong><i class="bi bi-bullseye"></i> Zielwert</strong>
                            </div>
                            <div class="card-body">
                                <h5 class="mb-0 text-success">${kpi.ziel}</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header bg-light">
                                <strong><i class="bi bi-speedometer"></i> Schwellenwerte</strong>
                            </div>
                            <div class="card-body">
                                <div class="mb-1">
                                    <span class="badge bg-success">Gut</span>
                                    <span class="ms-2">${kpi.schwellenwerte.gut}</span>
                                </div>
                                <div class="mb-1">
                                    <span class="badge bg-warning text-dark">Warnung</span>
                                    <span class="ms-2">${kpi.schwellenwerte.warnung}</span>
                                </div>
                                <div>
                                    <span class="badge bg-danger">Kritisch</span>
                                    <span class="ms-2">${kpi.schwellenwerte.kritisch}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Datengrundlage -->
                <div class="card mb-3">
                    <div class="card-header bg-info text-white">
                        <strong><i class="bi bi-database"></i> Datengrundlage</strong>
                    </div>
                    <div class="card-body">
                        <p class="mb-0">${kpi.datengrundlage}</p>
                    </div>
                </div>

                <!-- Beispiel -->
                ${kpi.beispiel ? `
                <div class="card mb-3">
                    <div class="card-header bg-light">
                        <strong><i class="bi bi-lightbulb"></i> Beispiel</strong>
                    </div>
                    <div class="card-body">
                        <p class="mb-0"><code>${kpi.beispiel}</code></p>
                    </div>
                </div>
                ` : ''}

                <!-- Hinweis -->
                ${kpi.hinweis ? `
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle"></i> <strong>Hinweis:</strong> ${kpi.hinweis}
                </div>
                ` : ''}

                <!-- Über 100% Erklärung -->
                ${kpi.ueber_100_prozent ? `
                <div class="alert alert-warning mb-0 mt-3">
                    <i class="bi bi-exclamation-triangle"></i> <strong>Über 100%?</strong> ${kpi.ueber_100_prozent}
                </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Fügt eine KPI-Definition hinzu (für Feature-spezifische KPIs)
     */
    addKPI(kpiName, definition) {
        this.kpiDefinitions[kpiName] = definition;
    }
}

// Globale Instanz
const kpiHelp = new KPIHelp();

// Auto-Init beim DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => kpiHelp.init());
} else {
    kpiHelp.init();
}
