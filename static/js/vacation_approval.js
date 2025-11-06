/**
 * URLAUBSPLANER V2 - APPROVAL MANAGEMENT
 * Urlaubsanträge genehmigen und ablehnen
 */

// State
let pendingApprovals = [];
let selectedRequests = new Set();

// ====================================
// INITIALISIERUNG
// ====================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Approval Manager wird initialisiert...');
    
    // Event-Listener
    setupApprovalListeners();
    
    // Initial laden wenn Tab aktiv
    const approvalTab = document.getElementById('approval-tab');
    if (approvalTab) {
        approvalTab.addEventListener('shown.bs.tab', loadPendingApprovals);
    }
});

// ====================================
// EVENT LISTENERS
// ====================================

function setupApprovalListeners() {
    // Refresh Button
    const refreshBtn = document.getElementById('refreshApprovalsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadPendingApprovals);
    }
    
    // Batch-Buttons
    const batchApproveBtn = document.getElementById('batchApproveBtn');
    const batchRejectBtn = document.getElementById('batchRejectBtn');
    
    if (batchApproveBtn) {
        batchApproveBtn.addEventListener('click', handleBatchApprove);
    }
    
    if (batchRejectBtn) {
        batchRejectBtn.addEventListener('click', handleBatchReject);
    }
    
    // Filter
    const filterDept = document.getElementById('filterDepartment');
    if (filterDept) {
        filterDept.addEventListener('change', filterApprovals);
    }
    
    console.log('✅ Approval Listeners eingerichtet');
}

// ====================================
// DATEN LADEN
// ====================================

async function loadPendingApprovals() {
    console.log('📥 Lade offene Genehmigungen...');
    
    const container = document.getElementById('approvalsList');
    if (!container) return;
    
    // Loading
    container.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"></div><p class="mt-2">Lade Anträge...</p></div>';
    
    try {
        const response = await apiCall('/approvals/pending');
        
        if (response.status === 'success') {
            pendingApprovals = response.data;
            console.log('✅ Offene Genehmigungen geladen:', pendingApprovals.length);
            
            updatePendingBadge(pendingApprovals.length);
            renderApprovalsList(pendingApprovals);
        } else {
            throw new Error(response.error || 'Fehler beim Laden');
        }
        
    } catch (error) {
        console.error('❌ Fehler:', error);
        container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Fehler beim Laden: ' + error.message + '</div>';
    }
}

function renderApprovalsList(approvals) {
    const container = document.getElementById('approvalsList');
    if (!container) return;
    
    if (approvals.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>Keine offenen Genehmigungen</p></div>';
        return;
    }
    
    const byDepartment = groupByDepartment(approvals);
    let html = '';
    
    Object.keys(byDepartment).sort().forEach(dept => {
        const deptApprovals = byDepartment[dept];
        html += '<div class="mb-4"><h6 class="text-muted mb-3"><i class="fas fa-building"></i> ' + dept + ' <span class="badge bg-secondary ms-2">' + deptApprovals.length + '</span></h6>';
        deptApprovals.forEach(approval => {
            html += renderApprovalItem(approval);
        });
        html += '</div>';
    });
    
    container.innerHTML = html;
    setupCheckboxListeners();
}

function renderApprovalItem(approval) {
    return '<div class="approval-item" id="approval-' + approval.request_id + '">' +
        '<div class="row align-items-center">' +
        '<div class="col-auto"><input type="checkbox" class="approval-checkbox" data-request-id="' + approval.request_id + '" onchange="toggleRequestSelection(' + approval.request_id + ')"></div>' +
        '<div class="col">' +
        '<div class="employee-info">' + approval.employee_name + '</div>' +
        '<div class="vacation-dates"><i class="fas fa-calendar"></i> ' + formatDate(approval.start_date) + ' - ' + formatDate(approval.end_date) +
        ' <span class="vacation-days ms-2"><i class="fas fa-clock"></i> ' + approval.working_days + ' Arbeitstage</span></div>' +
        (approval.comment ? '<div class="comment-box mt-2"><i class="fas fa-comment"></i> ' + approval.comment + '</div>' : '') +
        '</div>' +
        '<div class="col-auto">' +
        '<button class="btn btn-success btn-sm me-2" onclick="approveRequest(' + approval.request_id + ', \'' + approval.employee_name + '\')"><i class="fas fa-check"></i> Genehmigen</button>' +
        '<button class="btn btn-danger btn-sm" onclick="rejectRequest(' + approval.request_id + ', \'' + approval.employee_name + '\')"><i class="fas fa-times"></i> Ablehnen</button>' +
        '</div></div></div>';
}

function groupByDepartment(approvals) {
    const groups = {};
    approvals.forEach(approval => {
        const dept = approval.department || 'Keine Abteilung';
        if (!groups[dept]) groups[dept] = [];
        groups[dept].push(approval);
    });
    return groups;
}

async function approveRequest(requestId, employeeName) {
    const comment = prompt('Kommentar zur Genehmigung für ' + employeeName + ' (optional):');
    if (comment === null) return;
    
    try {
        const response = await apiCall('/request/' + requestId + '/approve', 'POST', {comment: comment || null});
        if (response.status === 'success') {
            showToast('Antrag für ' + employeeName + ' wurde genehmigt!', 'success');
            removeApprovalFromUI(requestId);
            await loadPendingApprovals();
        } else {
            throw new Error(response.error || 'Fehler bei Genehmigung');
        }
    } catch (error) {
        showToast('Fehler: ' + error.message, 'danger');
    }
}

async function rejectRequest(requestId, employeeName) {
    const comment = prompt('Ablehnungsgrund für ' + employeeName + ' (PFLICHT):');
    if (!comment || comment.trim() === '') {
        alert('Bitte geben Sie einen Ablehnungsgrund an!');
        return;
    }
    
    try {
        const response = await apiCall('/request/' + requestId + '/reject', 'POST', {comment: comment});
        if (response.status === 'success') {
            showToast('Antrag für ' + employeeName + ' wurde abgelehnt', 'warning');
            removeApprovalFromUI(requestId);
            await loadPendingApprovals();
        } else {
            throw new Error(response.error || 'Fehler bei Ablehnung');
        }
    } catch (error) {
        showToast('Fehler: ' + error.message, 'danger');
    }
}

function setupCheckboxListeners() {
    document.querySelectorAll('.approval-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateBatchButtons);
    });
}

function toggleRequestSelection(requestId) {
    const checkbox = document.querySelector('input[data-request-id="' + requestId + '"]');
    const item = document.getElementById('approval-' + requestId);
    
    if (checkbox && checkbox.checked) {
        selectedRequests.add(requestId);
        if (item) item.classList.add('selected');
    } else {
        selectedRequests.delete(requestId);
        if (item) item.classList.remove('selected');
    }
    updateBatchButtons();
}

function updateBatchButtons() {
    const batchApproveBtn = document.getElementById('batchApproveBtn');
    const batchRejectBtn = document.getElementById('batchRejectBtn');
    const count = selectedRequests.size;
    
    if (count > 0) {
        batchApproveBtn.disabled = false;
        batchRejectBtn.disabled = false;
        batchApproveBtn.innerHTML = '<i class="fas fa-check"></i> ' + count + ' genehmigen';
        batchRejectBtn.innerHTML = '<i class="fas fa-times"></i> ' + count + ' ablehnen';
    } else {
        batchApproveBtn.disabled = true;
        batchRejectBtn.disabled = true;
        batchApproveBtn.innerHTML = '<i class="fas fa-check"></i> Ausgewählte genehmigen';
        batchRejectBtn.innerHTML = '<i class="fas fa-times"></i> Ausgewählte ablehnen';
    }
}

async function handleBatchApprove() {
    if (selectedRequests.size === 0) return;
    const comment = prompt('Kommentar für ' + selectedRequests.size + ' Genehmigungen (optional):');
    if (comment === null) return;
    
    try {
        const response = await apiCall('/approvals/batch', 'POST', {
            request_ids: Array.from(selectedRequests),
            action: 'approve',
            comment: comment || null
        });
        
        if (response.status === 'success') {
            showToast(response.data.approved + ' Anträge genehmigt!', 'success');
            selectedRequests.clear();
            await loadPendingApprovals();
        }
    } catch (error) {
        showToast('Fehler: ' + error.message, 'danger');
    }
}

async function handleBatchReject() {
    if (selectedRequests.size === 0) return;
    const comment = prompt('Ablehnungsgrund für ' + selectedRequests.size + ' Anträge (PFLICHT):');
    
    if (!comment || comment.trim() === '') {
        alert('Bitte geben Sie einen Ablehnungsgrund an!');
        return;
    }
    
    try {
        const response = await apiCall('/approvals/batch', 'POST', {
            request_ids: Array.from(selectedRequests),
            action: 'reject',
            comment: comment
        });
        
        if (response.status === 'success') {
            showToast(response.data.rejected + ' Anträge abgelehnt', 'warning');
            selectedRequests.clear();
            await loadPendingApprovals();
        }
    } catch (error) {
        showToast('Fehler: ' + error.message, 'danger');
    }
}

function filterApprovals() {
    const selectedDept = document.getElementById('filterDepartment').value;
    if (!selectedDept) {
        renderApprovalsList(pendingApprovals);
    } else {
        const filtered = pendingApprovals.filter(a => a.department === selectedDept);
        renderApprovalsList(filtered);
    }
}

function updatePendingBadge(count) {
    const badge = document.getElementById('pendingBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

function removeApprovalFromUI(requestId) {
    const item = document.getElementById('approval-' + requestId);
    if (item) {
        item.style.opacity = '0.5';
        setTimeout(() => item.remove(), 500);
    }
    selectedRequests.delete(requestId);
    updateBatchButtons();
}

console.log('📦 vacation_approval.js geladen');
