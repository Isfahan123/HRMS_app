/**
 * Leave Configuration Management
 * Handles leave types and entitlements configuration
 */

// Global state
let currentLeaveTypes = [];
let currentEntitlements = [];
let currentLeaveTypeId = null;
let currentEntitlementId = null;

// Global functions for leave type management
function showAddLeaveTypeModal() {
    document.getElementById('leaveTypeModalTitle').textContent = 'Add Leave Type';
    document.getElementById('leaveTypeForm').reset();
    document.getElementById('leaveTypeId').value = '';
    currentLeaveTypeId = null;
    
    // Set defaults
    document.getElementById('leaveTypeIsActive').checked = true;
    document.getElementById('leaveTypeDefaultDuration').value = '1.0';
    document.getElementById('leaveTypeMaxDuration').value = '14.0';
    
    document.getElementById('leaveTypeModal').style.display = 'block';
}

function closeLeaveTypeModal() {
    document.getElementById('leaveTypeModal').style.display = 'none';
}

function showAddEntitlementModal() {
    document.getElementById('entitlementModalTitle').textContent = 'Add Entitlement';
    document.getElementById('entitlementForm').reset();
    document.getElementById('entitlementId').value = '';
    currentEntitlementId = null;
    
    // Populate leave type dropdown and tier dropdown
    populateLeaveTypeDropdown();
    populateTierDropdown();
    
    document.getElementById('entitlementModal').style.display = 'block';
}

function closeEntitlementModal() {
    document.getElementById('entitlementModal').style.display = 'none';
}

// Initialize leave configuration
function initLeaveConfiguration() {
    // Setup leave configuration if tab exists
    const leaveConfigTab = document.getElementById('leaveConfigSubtab');
    if (!leaveConfigTab) {
        console.warn('Leave config tab not found, scheduling retry...');
        setTimeout(initLeaveConfiguration, 100);
        return;
    }
    
    // Add Leave Type button
    const addLeaveTypeBtn = document.getElementById('addLeaveTypeBtn');
    if (addLeaveTypeBtn) {
        addLeaveTypeBtn.addEventListener('click', showAddLeaveTypeModal);
    }
    
    // Add Entitlement button
    const addEntitlementBtn = document.getElementById('addEntitlementBtn');
    if (addEntitlementBtn) {
        addEntitlementBtn.addEventListener('click', showAddEntitlementModal);
    }
    
    // Leave Type Form submission
    const leaveTypeForm = document.getElementById('leaveTypeForm');
    if (leaveTypeForm) {
        leaveTypeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveLeaveType();
        });
    }
    
    // Entitlement Form submission
    const entitlementForm = document.getElementById('entitlementForm');
    if (entitlementForm) {
        entitlementForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveEntitlement();
        });
    }
    
    // Load initial data
    console.log('Loading leave types and entitlements...');
    loadLeaveTypes();
    loadEntitlements();
}

// Call initialization immediately since script is loaded at bottom of page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLeaveConfiguration);
} else {
    // DOM already loaded
    initLeaveConfiguration();
}

/**
 * Load leave types from database
 */
async function loadLeaveTypes() {
    const tbody = document.getElementById('leaveTypesTableBody');
    if (!tbody) return;
    
    try {
        // Fetch leave types from API
        const response = await fetch('/api/admin/leave-types');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            currentLeaveTypes = data.data;
        } else {
            // Fall back to default leave types
            currentLeaveTypes = [
                {
                    id: 1,
                    name: 'Annual Leave',
                    code: 'annual',
                    color: '#3498db',
                    description: 'Regular annual leave entitlement',
                    requires_approval: true,
                    is_paid: true,
                    requires_document: false,
                    default_duration: 1.0,
                    max_duration: 14.0,
                    deduct_from: 'annual',
                    is_active: true
                },
                {
                    id: 2,
                    name: 'Sick Leave',
                    code: 'sick',
                    color: '#e74c3c',
                    description: 'Medical leave with certificate',
                    requires_approval: true,
                    is_paid: true,
                    requires_document: true,
                    default_duration: 1.0,
                    max_duration: 14.0,
                    deduct_from: 'sick',
                    is_active: true
                },
                {
                    id: 3,
                    name: 'Emergency Leave',
                    code: 'emergency',
                    color: '#f39c12',
                    description: 'Urgent personal matters',
                    requires_approval: true,
                    is_paid: true,
                    requires_document: false,
                    default_duration: 1.0,
                    max_duration: 3.0,
                    deduct_from: 'annual',
                    is_active: true
                },
                {
                    id: 4,
                    name: 'Unpaid Leave',
                    code: 'unpaid',
                    color: '#95a5a6',
                    description: 'Leave without pay',
                    requires_approval: true,
                    is_paid: false,
                    requires_document: false,
                    default_duration: 1.0,
                    max_duration: 30.0,
                    deduct_from: 'unpaid',
                    is_active: true
                },
                {
                    id: 5,
                    name: 'Maternity Leave',
                    code: 'maternity',
                    color: '#e91e63',
                    description: 'Maternity leave (as per law)',
                    requires_approval: false,
                    is_paid: true,
                    requires_document: true,
                    default_duration: 60.0,
                    max_duration: 98.0,
                    deduct_from: 'none',
                    is_active: true
                }
            ];
        }
        
        renderLeaveTypesTable();
        
    } catch (error) {
        console.error('Error loading leave types:', error);
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: red;">Error loading leave types</td></tr>';
    }
}

/**
 * Render leave types table
 */
function renderLeaveTypesTable() {
    const tbody = document.getElementById('leaveTypesTableBody');
    if (!tbody) return;
    
    if (currentLeaveTypes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">No leave types found. Click "Add Leave Type" to create one.</td></tr>';
        return;
    }
    
    let html = '';
    currentLeaveTypes.forEach(type => {
        const statusBadge = type.is_active ? '<span style="color: green;">✓ Active</span>' : '<span style="color: gray;">○ Inactive</span>';
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px;">${statusBadge}</td>
                <td style="padding: 8px;"><strong>${type.code || '-'}</strong></td>
                <td style="padding: 8px;">${type.name}</td>
                <td style="padding: 8px; text-align: center;">${type.deduct_from || 'none'}</td>
                <td style="padding: 8px; text-align: center;">${type.requires_document ? '✓' : '○'}</td>
                <td style="padding: 8px; text-align: center;">${type.default_duration || 1.0}</td>
                <td style="padding: 8px; text-align: center;">${type.max_duration || '-'}</td>
                <td style="padding: 8px; font-size: 0.9em;">${type.description || '-'}</td>
                <td style="padding: 8px; text-align: center;">
                    <button class="btn-sm" style="background: #3498db; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; margin-right: 4px;" onclick="editLeaveType(${type.id})">✏️ Edit</button>
                    <button class="btn-sm" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;" onclick="deleteLeaveType(${type.id})">🗑️ Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Load entitlements configuration
 */
async function loadEntitlements() {
    const tbody = document.getElementById('entitlementsTableBody');
    if (!tbody) return;
    
    try {
        // Fetch entitlements from API
        const response = await fetch('/api/admin/leave-entitlements');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            currentEntitlements = data.data;
        } else {
            // Fall back to default entitlements
            currentEntitlements = [
                {
                    id: 1,
                    leave_type_code: 'annual',
                    leave_type_name: 'Annual Leave',
                    employee_tier: 'junior',
                    days_entitlement: 14,
                    max_accumulation: 42
                },
                {
                    id: 2,
                    leave_type_code: 'sick',
                    leave_type_name: 'Sick Leave',
                    employee_tier: 'junior',
                    days_entitlement: 14,
                    max_accumulation: 60
                },
                {
                    id: 3,
                    leave_type_code: 'annual',
                    leave_type_name: 'Annual Leave',
                    employee_tier: 'senior',
                    days_entitlement: 18,
                    max_accumulation: 54
                },
                {
                    id: 4,
                    leave_type_code: 'sick',
                    leave_type_name: 'Sick Leave',
                    employee_tier: 'senior',
                    days_entitlement: 14,
                    max_accumulation: 60
                },
                {
                    id: 5,
                    leave_type_code: 'annual',
                    leave_type_name: 'Annual Leave',
                    employee_tier: 'manager',
                    days_entitlement: 21,
                    max_accumulation: 63
                }
            ];
        }
        
        renderEntitlementsTable();
        
    } catch (error) {
        console.error('Error loading entitlements:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: red;">Error loading entitlements</td></tr>';
    }
}

/**
 * Render entitlements table
 */
function renderEntitlementsTable() {
    const tbody = document.getElementById('entitlementsTableBody');
    if (!tbody) return;
    
    if (currentEntitlements.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No entitlements found. Click "Add Entitlement" to create one.</td></tr>';
        return;
    }
    
    let html = '';
    currentEntitlements.forEach(ent => {
        // Use tier_label from API response, fallback to getTierLabel
        const tierLabel = ent.tier_label || getTierLabel(ent.employee_tier);
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px;"><strong>${ent.leave_type_name || ent.leave_type_code || '-'}</strong></td>
                <td style="padding: 8px;">${tierLabel}</td>
                <td style="padding: 8px; text-align: center;">${ent.days_entitlement || 0} days</td>
                <td style="padding: 8px; text-align: center;">${ent.max_accumulation || '-'} days</td>
                <td style="padding: 8px; text-align: center;">
                    <button class="btn-sm" style="background: #3498db; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; margin-right: 4px;" onclick="editEntitlement('${ent.leave_type_code}', '${ent.employee_tier}')">✏️ Edit</button>
                    <button class="btn-sm" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;" onclick="deleteEntitlement('${ent.leave_type_code}', '${ent.employee_tier}')">🗑️ Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Get tier label - includes both legacy and new tier IDs
 */
function getTierLabel(tier) {
    const labels = {
        // Legacy tier labels
        'junior': 'Junior Staff / Entry Level',
        'mid': 'Mid-Level Staff',
        'senior': 'Senior Staff',
        'manager': 'Manager / Team Lead',
        'director': 'Director / C-Level',
        // Years of service tier labels
        'lt2': '< 2 years',
        '2to5': '2 - 5 years',
        'gt5': '> 5 years'
    };
    return labels[tier] || tier || '-';
}

/**
 * Save leave type
 */
async function saveLeaveType() {
    const formData = {
        code: document.getElementById('leaveTypeCode').value.toLowerCase().trim(),
        name: document.getElementById('leaveTypeName').value.trim(),
        description: document.getElementById('leaveTypeDescription').value.trim(),
        deduct_from: document.getElementById('leaveTypeDeductFrom').value,
        requires_document: document.getElementById('leaveTypeRequiresDocument').checked,
        default_duration: parseFloat(document.getElementById('leaveTypeDefaultDuration').value),
        max_duration: parseFloat(document.getElementById('leaveTypeMaxDuration').value),
        is_active: document.getElementById('leaveTypeIsActive').checked
    };
    
    // Validation
    if (!formData.code || !formData.name) {
        alert('⚠️ Code and Name are required fields');
        return;
    }
    
    if (formData.default_duration <= 0 || formData.max_duration <= 0) {
        alert('⚠️ Duration values must be positive');
        return;
    }
    
    if (formData.default_duration > formData.max_duration) {
        alert('⚠️ Default Duration cannot exceed Max Duration');
        return;
    }
    
    try {
        const url = currentLeaveTypeId ? `/api/admin/leave-types/${currentLeaveTypeId}` : '/api/admin/leave-types';
        const method = currentLeaveTypeId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Leave type "${formData.name}" saved successfully!`);
            closeLeaveTypeModal();
            await loadLeaveTypes();
        } else {
            alert(`❌ Error: ${data.message || 'Failed to save leave type'}`);
        }
        
    } catch (error) {
        console.error('Error saving leave type:', error);
        alert('❌ Error saving leave type: ' + error.message);
    }
}

/**
 * Edit leave type
 */
function editLeaveType(leaveTypeId) {
    const leaveType = currentLeaveTypes.find(t => t.id === leaveTypeId);
    if (!leaveType) return;
    
    // Populate form
    currentLeaveTypeId = leaveType.id;
    document.getElementById('leaveTypeId').value = leaveType.id;
    document.getElementById('leaveTypeCode').value = leaveType.code || '';
    document.getElementById('leaveTypeName').value = leaveType.name || '';
    document.getElementById('leaveTypeDescription').value = leaveType.description || '';
    document.getElementById('leaveTypeDeductFrom').value = leaveType.deduct_from || 'none';
    document.getElementById('leaveTypeRequiresDocument').checked = leaveType.requires_document === true;
    document.getElementById('leaveTypeDefaultDuration').value = leaveType.default_duration || 1.0;
    document.getElementById('leaveTypeMaxDuration').value = leaveType.max_duration || 14.0;
    document.getElementById('leaveTypeIsActive').checked = leaveType.is_active !== false;
    
    document.getElementById('leaveTypeModalTitle').textContent = 'Edit Leave Type';
    document.getElementById('leaveTypeModal').style.display = 'block';
}

/**
 * Delete leave type
 */
async function deleteLeaveType(leaveTypeId) {
    const leaveType = currentLeaveTypes.find(t => t.id === leaveTypeId);
    if (!leaveType) return;
    
    if (!confirm(`⚠️ Are you sure you want to delete leave type "${leaveType.name}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/leave-types/${leaveTypeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Leave type "${leaveType.name}" deleted successfully!`);
            await loadLeaveTypes();
        } else {
            alert(`❌ Error: ${data.message || 'Failed to delete leave type'}`);
        }
    } catch (error) {
        console.error('Error deleting leave type:', error);
        alert('❌ Error deleting leave type: ' + error.message);
    }
}

/**
 * Populate leave type dropdown for entitlements
 */
function populateLeaveTypeDropdown() {
    const select = document.getElementById('entitlementLeaveType');
    if (!select) return;
    
    let html = '<option value="">Select Leave Type</option>';
    currentLeaveTypes.forEach(type => {
        if (type.is_active !== false) {  // Include if active or not specified
            html += `<option value="${type.code}">${type.name}</option>`;
        }
    });
    
    select.innerHTML = html;
}

/**
 * Populate tier dropdown for entitlements - fetches from API or uses defaults
 */
async function populateTierDropdown() {
    const select = document.getElementById('entitlementTier');
    if (!select) return;
    
    let html = '<option value="">Select Tier</option>';
    
    try {
        // Try to fetch tiers from API
        const response = await fetch('/api/admin/leave-tiers');
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            data.data.forEach(tier => {
                html += `<option value="${tier.id}">${tier.label}</option>`;
            });
        } else {
            // Fallback: use tiers from current entitlements
            const existingTiers = new Map();
            currentEntitlements.forEach(ent => {
                if (ent.employee_tier && !existingTiers.has(ent.employee_tier)) {
                    existingTiers.set(ent.employee_tier, ent.tier_label || getTierLabel(ent.employee_tier));
                }
            });
            
            if (existingTiers.size > 0) {
                existingTiers.forEach((label, id) => {
                    html += `<option value="${id}">${label}</option>`;
                });
            } else {
                // Default years-of-service tiers matching Python GUI
                html += `<option value="lt2">< 2 years</option>`;
                html += `<option value="2to5">2 - 5 years</option>`;
                html += `<option value="gt5">> 5 years</option>`;
            }
        }
    } catch (error) {
        console.error('Error fetching tiers:', error);
        // Default fallback
        html += `<option value="lt2">< 2 years</option>`;
        html += `<option value="2to5">2 - 5 years</option>`;
        html += `<option value="gt5">> 5 years</option>`;
    }
    
    select.innerHTML = html;
}

/**
 * Save entitlement
 */
async function saveEntitlement() {
    const formData = {
        leave_type_code: document.getElementById('entitlementLeaveType').value,
        employee_tier: document.getElementById('entitlementTier').value,
        days_entitlement: parseFloat(document.getElementById('entitlementDays').value),
        max_accumulation: parseFloat(document.getElementById('entitlementMaxAccumulation').value)
    };
    
    // Validation
    if (!formData.leave_type_code || !formData.employee_tier) {
        alert('⚠️ Leave Type and Employee Tier are required');
        return;
    }
    
    if (formData.days_entitlement <= 0) {
        alert('⚠️ Days entitlement must be positive');
        return;
    }
    
    try {
        const url = currentEntitlementId ? `/api/admin/leave-entitlements/${currentEntitlementId}` : '/api/admin/leave-entitlements';
        const method = currentEntitlementId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Entitlement saved successfully!`);
            closeEntitlementModal();
            await loadEntitlements();
        } else {
            alert(`❌ Error: ${data.message || 'Failed to save entitlement'}`);
        }
        
    } catch (error) {
        console.error('Error saving entitlement:', error);
        alert('❌ Error saving entitlement: ' + error.message);
    }
}

/**
 * Edit entitlement
 */
function editEntitlement(leaveTypeCode, employeeTier) {
    const entitlement = currentEntitlements.find(e => 
        e.leave_type_code === leaveTypeCode && e.employee_tier === employeeTier
    );
    if (!entitlement) {
        console.error('Entitlement not found:', leaveTypeCode, employeeTier);
        return;
    }
    
    // Store current identifiers for update - using JSON for safe composite key storage
    currentEntitlementId = entitlement.id;
    document.getElementById('entitlementId').value = JSON.stringify({
        leave_type_code: leaveTypeCode,
        employee_tier: employeeTier
    });
    
    // Populate dropdowns first
    populateLeaveTypeDropdown();
    populateTierDropdown();
    
    document.getElementById('entitlementLeaveType').value = entitlement.leave_type_code || '';
    document.getElementById('entitlementTier').value = entitlement.employee_tier || '';
    document.getElementById('entitlementDays').value = entitlement.days_entitlement || 0;
    document.getElementById('entitlementMaxAccumulation').value = entitlement.max_accumulation || 0;
    
    document.getElementById('entitlementModalTitle').textContent = 'Edit Entitlement';
    document.getElementById('entitlementModal').style.display = 'block';
}

/**
 * Delete entitlement
 */
async function deleteEntitlement(leaveTypeCode, employeeTier) {
    const entitlement = currentEntitlements.find(e => 
        e.leave_type_code === leaveTypeCode && e.employee_tier === employeeTier
    );
    if (!entitlement) {
        console.error('Entitlement not found for delete:', leaveTypeCode, employeeTier);
        return;
    }
    
    if (!confirm(`⚠️ Are you sure you want to delete this entitlement?\n\nLeave Type: ${entitlement.leave_type_name}\nTier: ${entitlement.tier_label || employeeTier}\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        // Build URL with query parameters using URLSearchParams for proper encoding
        const params = new URLSearchParams();
        params.append('leave_type_code', leaveTypeCode);
        params.append('employee_tier', employeeTier);
        
        const response = await fetch(`/api/admin/leave-entitlements/${entitlement.id}?${params.toString()}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Entitlement deleted successfully!`);
            await loadEntitlements();
        } else {
            alert(`❌ Error: ${data.message || 'Failed to delete entitlement'}`);
        }
    } catch (error) {
        console.error('Error deleting entitlement:', error);
        alert('❌ Error deleting entitlement: ' + error.message);
    }
}

// Export functions to window object for onclick handlers
window.showAddLeaveTypeModal = showAddLeaveTypeModal;
window.closeLeaveTypeModal = closeLeaveTypeModal;
window.showAddEntitlementModal = showAddEntitlementModal;
window.closeEntitlementModal = closeEntitlementModal;
window.editLeaveType = editLeaveType;
window.editEntitlement = editEntitlement;
window.deleteLeaveType = deleteLeaveType;
window.deleteEntitlement = deleteEntitlement;

/**
 * Leave Policies Configuration
 */
function openLeavePoliciesModal() {
    document.getElementById('leavePoliciesModal').style.display = 'block';
    loadLeavePolicies();
}

function closeLeavePoliciesModal() {
    document.getElementById('leavePoliciesModal').style.display = 'none';
}

async function loadLeavePolicies() {
    try {
        const response = await fetch('/api/admin/leave-policies');
        const data = await response.json();
        
        if (data.success && data.data) {
            const policies = data.data;
            document.getElementById('policyCarryForwardEnabled').value = policies.carry_forward_enabled || 'true';
            document.getElementById('policyMaxCarryForward').value = policies.max_carry_forward_days || 10;
            document.getElementById('policyExpiryMonths').value = policies.carry_forward_expiry_months || 6;
            document.getElementById('policyCarryForwardAppliesTo').value = policies.carry_forward_applies_to || 'all';
            document.getElementById('policyProRateEntitlement').value = policies.pro_rate_entitlement || 'true';
            
            updateLeavePoliciesSummary(policies);
            updateCarryForwardFieldsState();
        }
    } catch (error) {
        console.error('Error loading leave policies:', error);
    }
}

function updateCarryForwardFieldsState() {
    const enabled = document.getElementById('policyCarryForwardEnabled').value === 'true';
    document.getElementById('policyMaxCarryForward').disabled = !enabled;
    document.getElementById('policyExpiryMonths').disabled = !enabled;
    document.getElementById('policyCarryForwardAppliesTo').disabled = !enabled;
}

function updateLeavePoliciesSummary(policies) {
    const summary = document.getElementById('leavePoliciesSummary');
    if (!summary) return;
    
    const cfEnabled = policies.carry_forward_enabled === 'true' || policies.carry_forward_enabled === true;
    const maxDays = policies.max_carry_forward_days || 10;
    const expiryMonths = policies.carry_forward_expiry_months || 6;
    const proRate = policies.pro_rate_entitlement === 'true' || policies.pro_rate_entitlement === true;
    
    summary.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            <div>
                <strong>Carry Forward:</strong><br>
                <span style="color: ${cfEnabled ? '#059669' : '#dc2626'};">${cfEnabled ? 'Enabled' : 'Disabled'}</span>
            </div>
            ${cfEnabled ? `
                <div>
                    <strong>Max Carry Forward:</strong><br>
                    <span style="color: #667eea;">${maxDays} days</span>
                </div>
                <div>
                    <strong>Expires After:</strong><br>
                    <span style="color: #667eea;">${expiryMonths} months</span>
                </div>
            ` : ''}
            <div>
                <strong>Pro-rate Entitlement:</strong><br>
                <span style="color: ${proRate ? '#059669' : '#dc2626'};">${proRate ? 'Enabled' : 'Disabled'}</span>
            </div>
        </div>
    `;
}

function resetLeavePolicies() {
    document.getElementById('policyCarryForwardEnabled').value = 'true';
    document.getElementById('policyMaxCarryForward').value = 10;
    document.getElementById('policyExpiryMonths').value = 6;
    document.getElementById('policyCarryForwardAppliesTo').value = 'all';
    document.getElementById('policyProRateEntitlement').value = 'true';
    updateCarryForwardFieldsState();
}

// Initialize leave policies
function initLeavePolicies() {
    const configurePoliciesBtn = document.getElementById('configureLeavePoliciesBtn');
    if (configurePoliciesBtn) {
        configurePoliciesBtn.addEventListener('click', openLeavePoliciesModal);
    }
    
    const policyCarryForwardEnabled = document.getElementById('policyCarryForwardEnabled');
    if (policyCarryForwardEnabled) {
        policyCarryForwardEnabled.addEventListener('change', updateCarryForwardFieldsState);
    }
    
    const leavePoliciesForm = document.getElementById('leavePoliciesForm');
    if (leavePoliciesForm) {
        leavePoliciesForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const policies = {
                carry_forward_enabled: document.getElementById('policyCarryForwardEnabled').value,
                max_carry_forward_days: parseInt(document.getElementById('policyMaxCarryForward').value),
                carry_forward_expiry_months: parseInt(document.getElementById('policyExpiryMonths').value),
                carry_forward_applies_to: document.getElementById('policyCarryForwardAppliesTo').value,
                pro_rate_entitlement: document.getElementById('policyProRateEntitlement').value
            };
            
            try {
                const response = await fetch('/api/admin/leave-policies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(policies)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Leave policies updated successfully!\n\nChanges will take effect immediately for new balance calculations.');
                    closeLeavePoliciesModal();
                    updateLeavePoliciesSummary(policies);
                } else {
                    alert('Error: ' + (result.message || 'Failed to update policies'));
                }
            } catch (error) {
                console.error('Error saving leave policies:', error);
                alert('Error saving leave policies');
            }
        });
    }
    
    // Load policies summary on page load
    console.log('Loading leave policies...');
    loadLeavePolicies();
}

// Initialize leave policies when ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLeavePolicies);
} else {
    initLeavePolicies();
}

window.openLeavePoliciesModal = openLeavePoliciesModal;
window.closeLeavePoliciesModal = closeLeavePoliciesModal;
window.resetLeavePolicies = resetLeavePolicies;
