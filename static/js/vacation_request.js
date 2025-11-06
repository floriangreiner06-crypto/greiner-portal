/**
 * URLAUBSPLANER V2 - REQUEST MANAGEMENT
 * Urlaubsanträge erstellen und verwalten
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('📝 Request Manager wird initialisiert...');
    setupRequestForm();
});

function setupRequestForm() {
    const form = document.getElementById('vacationRequestForm');
    if (!form) return;
    
    const employeeSelect = document.getElementById('employeeSelect');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    startDateInput.addEventListener('change', calculateWorkingDays);
    endDateInput.addEventListener('change', calculateWorkingDays);
    employeeSelect.addEventListener('change', calculateWorkingDays);
    
    form.addEventListener('submit', handleRequestSubmit);
    form.addEventListener('reset', handleFormReset);
    
    console.log('✅ Request Form eingerichtet');
}

async function calculateWorkingDays() {
    const employeeId = document.getElementById('employeeSelect').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    const calculationResult = document.getElementById('calculationResult');
    const calculationDetails = document.getElementById('calculationDetails');
    
    if (!startDate || !endDate) {
        calculationResult.style.display = 'none';
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        calculationDetails.innerHTML = '<span class="text-danger">❌ Enddatum muss nach Startdatum liegen!</span>';
        calculationResult.style.display = 'block';
        return;
    }
    
    calculationResult.style.display = 'block';
    calculationDetails.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Berechne...';
    
    try {
        const workingDays = calculateWorkingDaysSimple(startDate, endDate);
        
        let balanceInfo = '';
        if (employeeId) {
            const employee = employees.find(e => e.employee_id == employeeId);
            if (employee) {
                const remainingAfter = (employee.resturlaub || 0) - workingDays;
                balanceInfo = `
                    <div class="mt-2">
                        <small class="text-muted">
                            Aktueller Resturlaub: <strong>${employee.resturlaub || 0} Tage</strong><br>
                            Nach diesem Antrag: <strong class="${remainingAfter >= 0 ? 'text-success' : 'text-danger'}">${remainingAfter} Tage</strong>
                        </small>
                    </div>
                `;
                
                if (remainingAfter < 0) {
                    balanceInfo += '<div class="alert alert-danger mt-2 mb-0"><small>⚠️ Nicht genügend Resturlaub!</small></div>';
                }
            }
        }
        
        calculationDetails.innerHTML = `
            <div>
                <strong>Zeitraum:</strong> ${formatDate(startDate)} - ${formatDate(endDate)}<br>
                <strong>Arbeitstage:</strong> <span class="text-primary fs-5">${workingDays} Tage</span>
            </div>
            ${balanceInfo}
        `;
        
        if (employeeId) {
            await checkOverlaps(employeeId, startDate, endDate);
        }
        
    } catch (error) {
        console.error('Fehler bei Berechnung:', error);
        calculationDetails.innerHTML = '<span class="text-danger">❌ Fehler bei Berechnung</span>';
    }
}

function calculateWorkingDaysSimple(startDate, endDate) {
    let count = 0;
    let current = new Date(startDate);
    const end = new Date(endDate);
    
    while (current <= end) {
        const dayOfWeek = current.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            count++;
        }
        current.setDate(current.getDate() + 1);
    }
    
    return count;
}

async function checkOverlaps(employeeId, startDate, endDate) {
    const overlapWarning = document.getElementById('overlapWarning');
    const overlapMessage = document.getElementById('overlapMessage');
    
    try {
        const response = await apiCall(`/requests?employee_id=${employeeId}`);
        
        if (response.requests && response.requests.length > 0) {
            const overlaps = response.requests.filter(req => {
                if (req.status === 'rejected') return false;
                
                const reqDate = new Date(req.booking_date);
                const start = new Date(startDate);
                const end = new Date(endDate);
                
                return reqDate >= start && reqDate <= end;
            });
            
            if (overlaps.length > 0) {
                overlapWarning.style.display = 'block';
                overlapMessage.innerHTML = `
                    Es existieren bereits ${overlaps.length} Buchung(en) in diesem Zeitraum!
                `;
            } else {
                overlapWarning.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Fehler bei Overlap-Check:', error);
    }
}

async function handleRequestSubmit(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('submitRequestBtn');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Wird eingereicht...';
    
    try {
        const employeeId = parseInt(document.getElementById('employeeSelect').value);
        const vacationTypeId = parseInt(document.getElementById('vacationTypeSelect').value);
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const comment = document.getElementById('requestComment').value || null;
        
        if (!employeeId || !vacationTypeId || !startDate || !endDate) {
            throw new Error('Bitte alle Pflichtfelder ausfüllen!');
        }
        
        // Alle Tage zwischen Start und Ende als einzelne Buchungen erstellen
        const current = new Date(startDate);
        const end = new Date(endDate);
        const requests = [];
        
        while (current <= end) {
            const dayOfWeek = current.getDay();
            // Nur Werktage (Mo-Fr)
            if (dayOfWeek !== 0 && dayOfWeek !== 6) {
                const dateStr = current.toISOString().split('T')[0];
                requests.push({
                    employee_id: employeeId,
                    vacation_type_id: vacationTypeId,
                    start_date: dateStr,
                    end_date: dateStr,
                    comment: comment
                });
            }
            current.setDate(current.getDate() + 1);
        }
        
        console.log(`📤 Sende ${requests.length} Urlaubsbuchungen...`);
        
        // Alle Requests senden
        const results = [];
        for (const req of requests) {
            try {
                const response = await apiCall('/request', 'POST', req);
                results.push(response);
            } catch (error) {
                console.error('Fehler bei Buchung:', error);
            }
        }
        
        console.log(`✅ ${results.length} Buchungen erstellt`);
        
        showToast(`${results.length} Urlaubstage erfolgreich beantragt!`, 'success');
        
        document.getElementById('vacationRequestForm').reset();
        document.getElementById('calculationResult').style.display = 'none';
        document.getElementById('overlapWarning').style.display = 'none';
        
        await loadMyBalance();
        await loadMyRequests();
        
        setTimeout(() => {
            document.getElementById('dashboard-tab').click();
        }, 1500);
        
    } catch (error) {
        console.error('❌ Fehler beim Einreichen:', error);
        showToast(`Fehler: ${error.message}`, 'danger');
        
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function handleFormReset() {
    console.log('🔄 Formular wird zurückgesetzt');
    document.getElementById('calculationResult').style.display = 'none';
    document.getElementById('overlapWarning').style.display = 'none';
}

console.log('📦 vacation_request.js geladen');
