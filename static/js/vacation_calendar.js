/**
 * URLAUBSPLANER V2 - CALENDAR VIEW
 * Team-Kalender mit allen Abwesenheiten
 */

let calendarData = [];

// ====================================
// INITIALISIERUNG
// ====================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📅 Calendar Manager wird initialisiert...');
    
    // Initial laden wenn Tab aktiv
    const calendarTab = document.getElementById('calendar-tab');
    if (calendarTab) {
        calendarTab.addEventListener('shown.bs.tab', loadCalendar);
    }
    
    // Filter
    const deptFilter = document.getElementById('calendarDepartment');
    const typeFilter = document.getElementById('calendarVacationType');
    
    if (deptFilter) {
        deptFilter.addEventListener('change', filterCalendar);
    }
    
    if (typeFilter) {
        typeFilter.addEventListener('change', filterCalendar);
    }
});

// ====================================
// KALENDER LADEN
// ====================================

async function loadCalendar() {
    console.log('📅 Lade Team-Kalender...');
    
    const container = document.getElementById('teamCalendar');
    if (!container) return;
    
    // Loading
    container.innerHTML = '<div class="text-center py-5"><div class="spinner-border"></div><p class="mt-3">Kalender wird geladen...</p></div>';
    
    try {
        // Aktuelles Jahr/Monat
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
        
        // API-Call
        const response = await apiCall('/calendar?year=' + year + '&month=' + month);
        
        if (response.status === 'success') {
            calendarData = response.data;
            console.log('✅ Kalender geladen:', calendarData.length, 'Einträge');
            
            // Kalender rendern
            renderCalendar(calendarData);
            
        } else {
            throw new Error(response.error || 'Fehler beim Laden');
        }
        
    } catch (error) {
        console.error('❌ Fehler beim Laden des Kalenders:', error);
        container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Fehler beim Laden: ' + error.message + '</div>';
    }
}

// ====================================
// KALENDER RENDERN
// ====================================

function renderCalendar(data) {
    const container = document.getElementById('teamCalendar');
    if (!container) return;
    
    if (data.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-calendar"></i><p>Keine Abwesenheiten im aktuellen Monat</p></div>';
        return;
    }
    
    // Gruppierung nach Datum
    const byDate = groupByDate(data);
    const dates = Object.keys(byDate).sort();
    
    let html = '<div class="calendar-view">';
    
    // Nach Datum durchgehen
    dates.forEach(date => {
        const entries = byDate[date];
        const dateObj = new Date(date);
        
        html += '<div class="calendar-day-section mb-4">';
        html += '<h6 class="date-header">';
        html += '<i class="fas fa-calendar-day"></i> ';
        html += formatDateLong(date);
        html += ' <span class="badge bg-secondary ms-2">' + entries.length + '</span>';
        html += '</h6>';
        
        // Einträge für dieses Datum
        html += '<div class="row">';
        entries.forEach(entry => {
            html += renderCalendarEntry(entry);
        });
        html += '</div>';
        
        html += '</div>';
    });
    
    html += '</div>';
    
    container.innerHTML = html;
}

function renderCalendarEntry(entry) {
    const typeClass = getVacationTypeClass(entry.vacation_type);
    
    return '<div class="col-md-6 col-lg-4 mb-3">' +
        '<div class="card calendar-event ' + typeClass + '">' +
        '<div class="card-body">' +
        '<h6 class="card-title mb-2">' + entry.employee_name + '</h6>' +
        '<p class="card-text small mb-1">' +
        '<i class="fas fa-building"></i> ' + (entry.department || 'Keine Abt.') +
        '</p>' +
        '<p class="card-text small mb-1">' +
        '<i class="fas fa-calendar"></i> ' + formatDate(entry.start_date) + ' - ' + formatDate(entry.end_date) +
        '</p>' +
        '<p class="card-text small">' +
        '<i class="fas fa-clock"></i> ' + entry.working_days + ' Arbeitstage' +
        '</p>' +
        '</div>' +
        '</div>' +
        '</div>';
}

// ====================================
// HELPER FUNKTIONEN
// ====================================

function groupByDate(data) {
    const groups = {};
    
    data.forEach(entry => {
        // Alle Tage zwischen Start und Ende
        const start = new Date(entry.start_date);
        const end = new Date(entry.end_date);
        
        let current = new Date(start);
        while (current <= end) {
            const dateKey = current.toISOString().split('T')[0];
            
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            
            // Entry für diesen Tag hinzufügen
            groups[dateKey].push(entry);
            
            current.setDate(current.getDate() + 1);
        }
    });
    
    return groups;
}

function getVacationTypeClass(vacationType) {
    if (!vacationType) return '';
    
    const type = vacationType.toLowerCase();
    if (type.includes('urlaub') && !type.includes('sonder') && !type.includes('unbezahlt')) {
        return 'vtype-urlaub';
    } else if (type.includes('sonder')) {
        return 'vtype-sonderurlaub';
    } else if (type.includes('krank')) {
        return 'vtype-krank';
    } else if (type.includes('unbezahlt')) {
        return 'vtype-unbezahlt';
    }
    return '';
}

function formatDateLong(dateString) {
    const date = new Date(dateString);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('de-DE', options);
}

// ====================================
// FILTER
// ====================================

function filterCalendar() {
    const selectedDept = document.getElementById('calendarDepartment').value;
    const selectedType = document.getElementById('calendarVacationType').value;
    
    let filtered = calendarData;
    
    // Nach Abteilung filtern
    if (selectedDept) {
        filtered = filtered.filter(entry => entry.department === selectedDept);
    }
    
    // Nach Urlaubsart filtern
    if (selectedType) {
        filtered = filtered.filter(entry => {
            if (!entry.vacation_type) return false;
            return entry.vacation_type.toLowerCase().includes(selectedType.toLowerCase());
        });
    }
    
    console.log('🔍 Gefiltert:', filtered.length, 'von', calendarData.length);
    renderCalendar(filtered);
}

console.log('📦 vacation_calendar.js geladen');
