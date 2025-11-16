/**
 * Leave Configuration Management
 * Handles leave types and entitlements configuration
 */

// Global functions for leave type management
function showAddLeaveTypeModal() {
    document.getElementById('leaveTypeModalTitle').textContent = 'Add Leave Type';
    document.getElementById('leaveTypeForm').reset();
    document.getElementById('leaveTypeId').value = '';
    document.getElementById('leaveTypeModal').style.display = 'block';
}

function closeLeaveTypeModal() {
    document.getElementById('leaveTypeModal').style.display = 'none';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Setup leave configuration if tab exists
    const leaveConfigTab = document.getElementById('leaveConfigSubtab');
    if (!leaveConfigTab) return;
    
    // Add Leave Type button
    const addLeaveTypeBtn = document.getElementById('addLeaveTypeBtn');
    if (addLeaveTypeBtn) {
        addLeaveTypeBtn.addEventListener('click', showAddLeaveTypeModal);
    }
    
    // Leave Type Form submission
    const leaveTypeForm = document.getElementById('leaveTypeForm');
    if (leaveTypeForm) {
        leaveTypeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveLeaveType();
        });
    }
    
    // Load initial data
    loadLeaveTypes();
    loadEntitlements();
});

/**
 * Load leave types from database
 */
async function loadLeaveTypes() {
    const tbody = document.getElementById('leaveTypesTableBody');
    if (!tbody) return;
    
    try {
        // For now, show default leave types
        // In production, this would call an API endpoint
        const defaultTypes = [
            {
                id: 1,
                name: 'Annual Leave',
                description: 'Regular annual leave entitlement',
                requires_approval: true,
                max_days: 0
            },
            {
                id: 2,
                name: 'Sick Leave',
                description: 'Medical leave with certificate',
                requires_approval: true,
                max_days: 14
            },
            {
                id: 3,
                name: 'Emergency Leave',
                description: 'Urgent personal matters',
                requires_approval: true,
                max_days: 5
            },
            {
                id: 4,
                name: 'Unpaid Leave',
                description: 'Leave without pay',
                requires_approval: true,
                max_days: 0
            },
            {
                id: 5,
                name: 'Maternity Leave',
                description: 'Maternity leave (as per law)',
                requires_approval: false,
                max_days: 90
            },
            {
                id: 6,
                name: 'Paternity Leave',
                description: 'Paternity leave (as per law)',
                requires_approval: false,
                max_days: 7
            }
        ];
        
        let html = '';
        defaultTypes.forEach(type => {
            html += `
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 12px;"><strong>${type.name}</strong></td>
                    <td style="padding: 12px;">${type.description}</td>
                    <td style="padding: 12px; text-align: center;">
                        ${type.requires_approval ? '✅ Yes' : '❌ No'}
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        ${type.max_days === 0 ? 'Unlimited' : type.max_days + ' days'}
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        <button class="btn-sm btn-secondary" onclick="editLeaveType(${type.id})">Edit</button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading leave types:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: red;">Error loading leave types</td></tr>';
    }
}

/**
 * Load entitlements configuration
 */
async function loadEntitlements() {
    const tbody = document.getElementById('entitlementsTableBody');
    if (!tbody) return;
    
    try {
        // For now, show default entitlements
        // In production, this would call an API endpoint
        const defaultEntitlements = [
            {
                id: 1,
                position: 'Junior Staff / Entry Level',
                annual_days: 14,
                sick_days: 14,
                carry_forward_max: 5
            },
            {
                id: 2,
                position: 'Senior Staff',
                annual_days: 18,
                sick_days: 14,
                carry_forward_max: 7
            },
            {
                id: 3,
                position: 'Manager / Team Lead',
                annual_days: 21,
                sick_days: 14,
                carry_forward_max: 10
            },
            {
                id: 4,
                position: 'Senior Manager',
                annual_days: 24,
                sick_days: 14,
                carry_forward_max: 12
            },
            {
                id: 5,
                position: 'Director / C-Level',
                annual_days: 28,
                sick_days: 14,
                carry_forward_max: 15
            }
        ];
        
        let html = '';
        defaultEntitlements.forEach(ent => {
            html += `
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 12px;"><strong>${ent.position}</strong></td>
                    <td style="padding: 12px; text-align: center;">${ent.annual_days} days</td>
                    <td style="padding: 12px; text-align: center;">${ent.sick_days} days</td>
                    <td style="padding: 12px; text-align: center;">${ent.carry_forward_max} days</td>
                    <td style="padding: 12px; text-align: center;">
                        <button class="btn-sm btn-secondary" onclick="editEntitlement(${ent.id})">Edit</button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading entitlements:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: red;">Error loading entitlements</td></tr>';
    }
}

/**
 * Save leave type
 */
async function saveLeaveType() {
    const leaveTypeId = document.getElementById('leaveTypeId').value;
    const formData = {
        name: document.getElementById('leaveTypeName').value,
        description: document.getElementById('leaveTypeDescription').value,
        requires_approval: document.getElementById('leaveTypeRequiresApproval').checked,
        max_days: parseInt(document.getElementById('leaveTypeMaxDays').value),
        color: document.getElementById('leaveTypeColor').value
    };
    
    try {
        // In production, this would call an API endpoint
        // const url = leaveTypeId ? `/api/admin/leave-types/${leaveTypeId}` : '/api/admin/leave-types';
        // const method = leaveTypeId ? 'PUT' : 'POST';
        // const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
        
        alert(`Leave type "${formData.name}" saved successfully!\n\nNote: This is a demo. In production, this would save to the database.`);
        closeLeaveTypeModal();
        loadLeaveTypes();
        
    } catch (error) {
        console.error('Error saving leave type:', error);
        alert('Error saving leave type: ' + error.message);
    }
}

/**
 * Edit leave type
 */
function editLeaveType(leaveTypeId) {
    alert(`Edit leave type ID: ${leaveTypeId}\n\nThis would open the modal with existing data for editing.`);
    // In production, fetch the leave type data and populate the modal
}

/**
 * Edit entitlement
 */
function editEntitlement(entitlementId) {
    alert(`Edit entitlement ID: ${entitlementId}\n\nThis would open a modal to edit entitlement settings.`);
    // In production, fetch the entitlement data and show edit modal
}
