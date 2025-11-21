/**
 * URLAUBSPLANER V2 - MAIN MANAGER
 * Zentrale Koordination & API-Kommunikation
 */

const API_BASE = '/api/vacation';

let employees = [];
let vacationTypes = [];
let departments = [];
let currentUserId = null;

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Urlaubsplaner V2 wird initialisiert...');
    
    try {
        await loadEmployees();
        await loadVacationTypes();
        await loadDepartments();
        
        // currentUserId wird automatisch aus Session geholt (via /my-balance)
        await loadCurrentUserInfo();
        await initDashboard();
        
        setupEventListeners();
        
        console.log('✅ Urlaubsplaner V2 erfolgreich initialisiert!');
        showToast('Willkommen im Urlaubsplaner V2!', 'success');
        
    } catch (error) {
        console.error('❌ Fehler bei Initialisierung:', error);
        showToast('Fehler beim Laden der Daten', 'danger');
    }
});

async function apiCall(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE}${endpoint}`;
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

async function loadEmployees() {
    console.log('📥 Lade Mitarbeiter...');
    
    try {
        const response = await apiCall('/balance');
        
        if (response.balances) {
            employees = response.balances;
            console.log(`✅ ${employees.length} Mitarbeiter geladen`);
            fillEmployeeDropdown();
            return employees;
        }
    } catch (error) {
        console.error('❌ Fehler beim Laden der Mitarbeiter:', error);
        throw error;
    }
}

async function loadVacationTypes() {
    console.log('📥 Lade Urlaubsarten...');
    
    vacationTypes = [
        { id: 1, name: 'Urlaub', color: '#28a745' },
        { id: 2, name: 'Sonderurlaub', color: '#17a2b8' },
        { id: 3, name: 'Krankheit', color: '#dc3545' },
        { id: 4, name: 'Unbezahlter Urlaub', color: '#6c757d' }
    ];
    
    console.log(`✅ ${vacationTypes.length} Urlaubsarten geladen`);
    fillVacationTypeDropdown();
    return vacationTypes;
}

function loadDepartments() {
    console.log('📥 Extrahiere Abteilungen...');
    
    const deptSet = new Set();
    employees.forEach(emp => {
        if (emp.department_name) {
            deptSet.add(emp.department_name);
        }
    });
    
    departments = Array.from(deptSet).sort();
    console.log(`✅ ${departments.length} Abteilungen gefunden`);
    fillDepartmentDropdowns();
    return departments;
}

async function loadCurrentUserInfo() {
    console.log('📥 Lade Info für aktuellen User...');
    
    try {
        // Verwende /my-balance - holt automatisch den eingeloggten User
        const response = await apiCall('/my-balance');
        
        if (response.success && response.balance) {
            const balance = response.balance;
            
            // Setze currentUserId aus Response
            currentUserId = balance.employee_id;
            
            // Zeige User-Info an
            document.getElementById('userName').textContent = balance.name || 'Unbekannt';
            document.getElementById('remainingDays').textContent = balance.resturlaub || 0;
            
            console.log(`✅ User-Info geladen: ${balance.name} (ID: ${currentUserId})`);
        }
    } catch (error) {
        console.error('❌ Fehler beim Laden der User-Info:', error);
        showToast('Fehler beim Laden der Benutzerdaten', 'danger');
    }
}

function fillEmployeeDropdown() {
    const select = document.getElementById('employeeSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">Bitte wählen...</option>';
    
    const sortedEmployees = [...employees].sort((a, b) => 
        (a.name || '').localeCompare(b.name || '')
    );
    
    sortedEmployees.forEach(emp => {
        const option = document.createElement('option');
        option.value = emp.employee_id;
        option.textContent = `${emp.name} (${emp.department_name || 'Keine Abt.'})`;
        select.appendChild(option);
    });
    
    console.log(`✅ ${sortedEmployees.length} Mitarbeiter in Dropdown`);
}

function fillVacationTypeDropdown() {
    const select = document.getElementById('vacationTypeSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">Bitte wählen...</option>';
    
    vacationTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type.id;
        option.textContent = type.name;
        select.appendChild(option);
    });
    
    console.log(`✅ ${vacationTypes.length} Urlaubsarten in Dropdown`);
}

function fillDepartmentDropdowns() {
    const selects = [
        document.getElementById('filterDepartment'),
        document.getElementById('calendarDepartment')
    ];
    
    selects.forEach(select => {
        if (!select) return;
        
        select.innerHTML = '<option value="">Alle Abteilungen</option>';
        
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            select.appendChild(option);
        });
    });
    
    console.log(`✅ ${departments.length} Abteilungen in Dropdowns`);
}

async function initDashboard() {
    console.log('📊 Initialisiere Dashboard...');
    
    try {
        await loadMyBalance();
        await loadMyRequests();
        await loadTeamAbsenceToday();
        
        console.log('✅ Dashboard initialisiert');
    } catch (error) {
        console.error('❌ Fehler beim Dashboard-Init:', error);
    }
}

async function loadMyBalance() {
    const container = document.getElementById('myBalanceDetails');
    if (!container) return;
    
    try {
        // Verwende /my-balance
        const response = await apiCall('/my-balance');
        
        if (response.success && response.balance) {
            const balance = response.balance;
            
            container.innerHTML = `
                <div class="balance-item">
                    <span class="balance-label">Jahresanspruch:</span>
                    <span class="balance-value">${balance.anspruch || 0} Tage</span>
                </div>
                <div class="balance-item">
                    <span class="balance-label">Bereits genommen:</span>
                    <span class="balance-value">${balance.verbraucht || 0} Tage</span>
                </div>
                <div class="balance-item">
                    <span class="balance-label">Resturlaub:</span>
                    <span class="balance-value text-success">${balance.resturlaub || 0} Tage</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Fehler beim Laden des Saldos:', error);
        container.innerHTML = '<p class="text-danger">Fehler beim Laden</p>';
    }
}

async function loadMyRequests() {
    const container = document.getElementById('myRequestsList');
    if (!container) return;
    
    try {
        // Verwende /my-bookings statt /requests mit employee_id
        const response = await apiCall('/my-bookings');
        
        if (response.success && response.bookings && response.bookings.length > 0) {
            // Nur die letzten 5 Buchungen
            const bookings = response.bookings.slice(0, 5);
            
            container.innerHTML = bookings.map(booking => `
                <div class="request-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${formatDate(booking.date)}</strong>
                            <div class="small text-muted">
                                ${booking.type_name || 'Urlaub'}
                            </div>
                        </div>
                        <span class="request-status status-${booking.status}">
                            ${booking.status === 'pending' ? 'Offen' : 
                              booking.status === 'approved' ? 'Genehmigt' : 'Abgelehnt'}
                        </span>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">Keine Anträge vorhanden</p>';
        }
    } catch (error) {
        console.error('❌ Fehler beim Laden der Anträge:', error);
        container.innerHTML = '<p class="text-danger">Fehler beim Laden</p>';
    }
}

async function loadTeamAbsenceToday() {
    const container = document.getElementById('teamAbsenceToday');
    if (!container) return;
    
    container.innerHTML = '<p class="text-muted small">Keine Abwesenheiten heute</p>';
}

function setupEventListeners() {
    console.log('🎯 Richte Event-Listener ein...');
    
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', handleTabChange);
    });
}

function handleTabChange(event) {
    const targetId = event.target.getAttribute('data-bs-target');
    console.log(`🔀 Tab gewechselt zu: ${targetId}`);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const [year, month, day] = dateString.split('-');
    return `${day}.${month}.${year}`;
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} message-toast`;
    toast.innerHTML = `
        <strong>${type === 'success' ? '✅' : type === 'danger' ? '❌' : 'ℹ️'}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

console.log('📦 vacation_manager.js geladen');
