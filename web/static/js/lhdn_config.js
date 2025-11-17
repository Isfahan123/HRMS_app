/**
 * LHDN Tax Configuration Management - Complete Implementation
 * Matching Python GUI functionality with full CRUD operations
 */

// Malaysian Tax Rates for Residents (2024 rates - fallback)
const RESIDENT_TAX_RATES = [
    { from: 0, to: 5000, rate: 0, taxOnBand: 0 },
    { from: 5001, to: 20000, rate: 1, taxOnBand: 150 },
    { from: 20001, to: 35000, rate: 3, taxOnBand: 450 },
    { from: 35001, to: 50000, rate: 8, taxOnBand: 1200 },
    { from: 50001, to: 70000, rate: 13, taxOnBand: 2600 },
    { from: 70001, to: 100000, rate: 21, taxOnBand: 6300 },
    { from: 100001, to: 250000, rate: 24, taxOnBand: 36000 },
    { from: 250001, to: 400000, rate: 24.5, taxOnBand: 36750 },
    { from: 400001, to: 600000, rate: 25, taxOnBand: 50000 },
    { from: 600001, to: 1000000, rate: 26, taxOnBand: 104000 },
    { from: 1000001, to: 2000000, rate: 28, taxOnBand: 280000 },
    { from: 2000001, to: 999999999, rate: 30, taxOnBand: 0 }
];

// Tax Relief Categories and Maximum Amounts (2024)
const TAX_RELIEF_CATEGORIES = [
    { id: 'self', name: 'Self Relief', max: 9000, description: 'Individual relief' },
    { id: 'spouse', name: 'Spouse Relief', max: 4000, description: 'Married with non-working spouse' },
    { id: 'child_under18', name: 'Child Relief (Under 18)', max: 2000, description: 'Per child under 18' },
    { id: 'child_over18', name: 'Child Relief (18+ Full-time Education)', max: 8000, description: 'Per child 18+ in full-time education' },
    { id: 'child_disabled', name: 'Disabled Child', max: 6000, description: 'Per disabled child' },
    { id: 'life_insurance', name: 'Life Insurance & EPF', max: 7000, description: 'Life insurance premiums and EPF' },
    { id: 'education', name: 'Education & Medical Insurance', max: 3000, description: 'Self, spouse, child education' },
    { id: 'medical_parents', name: 'Medical for Parents', max: 8000, description: 'Medical expenses for parents' },
    { id: 'medical_self', name: 'Medical for Self/Spouse/Child', max: 8000, description: 'Serious diseases' },
    { id: 'basic_equipment', name: 'Basic Supporting Equipment', max: 6000, description: 'For self, spouse, child or parents' },
    { id: 'lifestyle', name: 'Lifestyle', max: 2500, description: 'Books, computers, gym, internet' },
    { id: 'domestic_travel', name: 'Domestic Tourism', max: 1000, description: 'Hotel accommodation in Malaysia' },
    { id: 'sports_equipment', name: 'Sports Equipment', max: 500, description: 'Purchase of sports equipment' },
    { id: 'eis_socso', name: 'EIS & SOCSO', max: 250, description: 'Self EIS and SOCSO contributions' }
];

// Global state
let currentTaxRates = [];
let currentReliefMaximums = [];
let currentOverrides = [];
let employeesList = [];

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Load tax rates from API
    loadTaxRatesFromAPI();
    
    // Load relief maximums from API
    loadReliefMaximumsFromAPI();
    
    // Load relief overrides from API
    loadReliefOverridesFromAPI();
    
    // Load employees list for override selection
    loadEmployeesForOverrides();
});

/**
 * Load tax rates from API
 */
async function loadTaxRatesFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/tax-rates');
        const data = await response.json();
        
        if (data.success) {
            currentTaxRates = data.data.resident.length > 0 ? data.data.resident : RESIDENT_TAX_RATES;
            loadResidentTaxRates(currentTaxRates);
            loadNonResidentTaxRates(data.data.non_resident || []);
        } else {
            currentTaxRates = RESIDENT_TAX_RATES;
            loadResidentTaxRates(RESIDENT_TAX_RATES);
            loadNonResidentTaxRates([]);
        }
    } catch (error) {
        console.error('Error loading tax rates from API:', error);
        currentTaxRates = RESIDENT_TAX_RATES;
        loadResidentTaxRates(RESIDENT_TAX_RATES);
        loadNonResidentTaxRates([]);
    }
}

/**
 * Load resident tax rates into table
 */
function loadResidentTaxRates(rates) {
    const tbody = document.getElementById('residentTaxRatesBody');
    if (!tbody) return;
    
    let html = '';
    
    rates.forEach((bracket, index) => {
        const from = bracket.income_from || bracket.from;
        const to = bracket.income_to || bracket.to;
        const rate = bracket.rate_percent || bracket.rate;
        const taxOnBand = bracket.tax_on_band || bracket.taxOnBand || 0;
        
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">${formatMoney(from)}</td>
                <td style="padding: 10px;">${to > 900000000 ? 'Above' : formatMoney(to)}</td>
                <td style="padding: 10px; text-align: center;"><strong>${rate}%</strong></td>
                <td style="padding: 10px; text-align: right;">${formatMoney(parseFloat(taxOnBand))}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editTaxBracket('resident', ${index})">✏️ Edit</button>
                    <button class="btn-sm btn-danger" onclick="deleteTaxBracket('resident', ${index})">🗑️</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="5" style="padding: 15px; text-align: center;">No tax rates configured</td></tr>';
}

/**
 * Load non-resident tax rates into table
 */
function loadNonResidentTaxRates(rates) {
    const tbody = document.getElementById('nonResidentTaxRatesBody');
    if (!tbody) return;
    
    if (rates.length === 0) {
        // Default flat 30% for non-residents
        tbody.innerHTML = `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">0</td>
                <td style="padding: 10px;">Above</td>
                <td style="padding: 10px; text-align: center;"><strong>30%</strong></td>
                <td style="padding: 10px; text-align: right;">Flat rate</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editTaxBracket('non-resident', 0)">✏️ Edit</button>
                </td>
            </tr>
        `;
    } else {
        let html = '';
        rates.forEach((bracket, index) => {
            html += `
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px;">${formatMoney(bracket.income_from || 0)}</td>
                    <td style="padding: 10px;">${bracket.income_to > 900000000 ? 'Above' : formatMoney(bracket.income_to)}</td>
                    <td style="padding: 10px; text-align: center;"><strong>${bracket.rate_percent}%</strong></td>
                    <td style="padding: 10px; text-align: right;">${formatMoney(bracket.tax_on_band || 0)}</td>
                    <td style="padding: 10px; text-align: center;">
                        <button class="btn-sm btn-secondary" onclick="editTaxBracket('non-resident', ${index})">✏️ Edit</button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }
}

/**
 * Add new tax bracket - show modal
 */
function addTaxBracket(type) {
    document.getElementById('taxBracketModalTitle').textContent = `Add ${type === 'resident' ? 'Resident' : 'Non-Resident'} Tax Bracket`;
    document.getElementById('taxBracketType').value = type;
    document.getElementById('taxBracketIndex').value = '';
    document.getElementById('taxBracketId').value = '';
    document.getElementById('taxBracketForm').reset();
    showModal('taxBracketModal');
}

/**
 * Edit tax bracket - show modal with data
 */
function editTaxBracket(type, index) {
    const rates = type === 'resident' ? currentTaxRates : [];
    const bracket = rates[index];
    
    if (!bracket) {
        alert('Tax bracket not found');
        return;
    }
    
    document.getElementById('taxBracketModalTitle').textContent = `Edit ${type === 'resident' ? 'Resident' : 'Non-Resident'} Tax Bracket`;
    document.getElementById('taxBracketType').value = type;
    document.getElementById('taxBracketIndex').value = index;
    document.getElementById('taxBracketId').value = bracket.id || '';
    document.getElementById('taxBracketFrom').value = bracket.income_from || bracket.from;
    document.getElementById('taxBracketTo').value = bracket.income_to || bracket.to;
    document.getElementById('taxBracketRate').value = bracket.rate_percent || bracket.rate;
    document.getElementById('taxBracketAmount').value = bracket.tax_on_band || bracket.taxOnBand || '';
    
    showModal('taxBracketModal');
}

/**
 * Delete tax bracket
 */
async function deleteTaxBracket(type, index) {
    if (!confirm('Are you sure you want to delete this tax bracket?')) {
        return;
    }
    
    const rates = type === 'resident' ? currentTaxRates : [];
    const bracket = rates[index];
    
    if (!bracket.id) {
        // If no ID, just remove from local array
        rates.splice(index, 1);
        loadResidentTaxRates(currentTaxRates);
        showMessage('Tax bracket deleted successfully', 'success');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/lhdn/tax-rates/${bracket.id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Tax bracket deleted successfully', 'success');
            loadTaxRatesFromAPI();
        } else {
            showMessage('Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error deleting tax bracket:', error);
        showMessage('Error deleting tax bracket', 'error');
    }
}

/**
 * Save tax bracket (add or update)
 */
document.getElementById('taxBracketForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const type = document.getElementById('taxBracketType').value;
    const index = document.getElementById('taxBracketIndex').value;
    const id = document.getElementById('taxBracketId').value;
    const from = parseFloat(document.getElementById('taxBracketFrom').value);
    const to = parseFloat(document.getElementById('taxBracketTo').value);
    const rate = parseFloat(document.getElementById('taxBracketRate').value);
    const taxAmount = parseFloat(document.getElementById('taxBracketAmount').value) || 0;
    
    // Validation
    if (from >= to && to <= 900000000) {
        showMessageInModal('taxBracketMessage', '"Income From" must be less than "Income To"', 'error');
        return;
    }
    
    const bracketData = {
        resident_type: type,
        income_from: from,
        income_to: to,
        rate_percent: rate,
        tax_on_band: taxAmount
    };
    
    try {
        const response = await fetch('/api/admin/lhdn/tax-rates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bracketData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessageInModal('taxBracketMessage', 'Tax bracket saved successfully!', 'success');
            setTimeout(() => {
                closeTaxBracketModal();
                loadTaxRatesFromAPI();
            }, 1500);
        } else {
            showMessageInModal('taxBracketMessage', 'Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error saving tax bracket:', error);
        showMessageInModal('taxBracketMessage', 'Error saving tax bracket', 'error');
    }
});

/**
 * Close tax bracket modal
 */
function closeTaxBracketModal() {
    hideModal('taxBracketModal');
    document.getElementById('taxBracketForm').reset();
    document.getElementById('taxBracketMessage').style.display = 'none';
}

/**
 * Load relief maximums from API
 */
async function loadReliefMaximumsFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/relief-max');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            currentReliefMaximums = data.data;
            loadReliefMaximums(data.data);
        } else {
            // Fall back to hardcoded relief categories
            const fallbackReliefs = TAX_RELIEF_CATEGORIES.map(r => ({
                relief_code: r.id,
                relief_name: r.name,
                max_amount: r.max,
                description: r.description
            }));
            currentReliefMaximums = fallbackReliefs;
            loadReliefMaximums(fallbackReliefs);
        }
    } catch (error) {
        console.error('Error loading relief maximums from API:', error);
        const fallbackReliefs = TAX_RELIEF_CATEGORIES.map(r => ({
            relief_code: r.id,
            relief_name: r.name,
            max_amount: r.max,
            description: r.description
        }));
        currentReliefMaximums = fallbackReliefs;
        loadReliefMaximums(fallbackReliefs);
    }
}

/**
 * Load relief maximums into table
 */
function loadReliefMaximums(reliefs) {
    const tbody = document.getElementById('reliefMaxBody');
    if (!tbody) return;
    
    let html = '';
    
    reliefs.forEach((relief, index) => {
        const code = relief.relief_code || relief.id;
        const name = relief.relief_name || relief.name;
        const maxAmount = relief.max_amount || relief.max;
        const description = relief.description || '';
        
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">
                    <strong>${name}</strong>
                    <br>
                    <small style="color: #666;">${description}</small>
                </td>
                <td style="padding: 10px; text-align: right;">
                    <strong style="color: #667eea;">RM ${formatMoney(maxAmount)}</strong>
                </td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editRelief('${code}', ${index})">✏️ Edit</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="3" style="padding: 15px; text-align: center;">No relief maximums configured</td></tr>';
}

/**
 * Edit relief maximum - show modal
 */
function editRelief(reliefCode, index) {
    const relief = currentReliefMaximums[index];
    
    if (!relief) {
        alert('Relief category not found');
        return;
    }
    
    document.getElementById('reliefCode').value = reliefCode;
    document.getElementById('reliefIndex').value = index;
    document.getElementById('reliefName').value = relief.relief_name || relief.name;
    document.getElementById('reliefDescription').value = relief.description || '';
    document.getElementById('reliefMaxAmount').value = relief.max_amount || relief.max;
    
    showModal('reliefEditModal');
}

/**
 * Save relief maximum
 */
document.getElementById('reliefEditForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const code = document.getElementById('reliefCode').value;
    const maxAmount = parseFloat(document.getElementById('reliefMaxAmount').value);
    
    const reliefData = {
        relief_code: code,
        max_amount: maxAmount
    };
    
    try {
        const response = await fetch('/api/admin/lhdn/relief-max', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reliefData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessageInModal('reliefEditMessage', 'Relief maximum updated successfully!', 'success');
            setTimeout(() => {
                closeReliefEditModal();
                loadReliefMaximumsFromAPI();
            }, 1500);
        } else {
            showMessageInModal('reliefEditMessage', 'Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error saving relief maximum:', error);
        showMessageInModal('reliefEditMessage', 'Error saving relief maximum', 'error');
    }
});

/**
 * Close relief edit modal
 */
function closeReliefEditModal() {
    hideModal('reliefEditModal');
    document.getElementById('reliefEditForm').reset();
    document.getElementById('reliefEditMessage').style.display = 'none';
}

/**
 * Edit all reliefs (batch mode)
 */
function editAllReliefs() {
    alert('Batch Relief Editor\n\nThis feature allows editing all relief categories at once. It would typically be used when LHDN updates all relief amounts for a new tax year.\n\nImplement a comprehensive form with all 14 relief categories for efficient batch updates.');
}

/**
 * Load relief overrides from API
 */
async function loadReliefOverridesFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/relief-overrides');
        const data = await response.json();
        
        if (data.success) {
            currentOverrides = data.data || [];
            loadReliefOverrides(data.data || []);
        } else {
            currentOverrides = [];
            loadReliefOverrides([]);
        }
    } catch (error) {
        console.error('Error loading relief overrides from API:', error);
        currentOverrides = [];
        loadReliefOverrides([]);
    }
}

/**
 * Load relief overrides into table
 */
function loadReliefOverrides(overrides) {
    const tbody = document.getElementById('reliefOverridesBody');
    if (!tbody) return;
    
    if (overrides.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 15px; text-align: center;">No relief overrides configured</td></tr>';
        return;
    }
    
    let html = '';
    
    overrides.forEach(override => {
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">
                    <strong>${override.employee_name || override.employee_id}</strong>
                    <br>
                    <small style="color: #666;">${override.employee_id}</small>
                </td>
                <td style="padding: 10px;">${override.relief_category || override.relief_code}</td>
                <td style="padding: 10px; text-align: right;">RM ${formatMoney(override.override_amount)}</td>
                <td style="padding: 10px; text-align: center;">${override.effective_year || override.effective_period || '-'}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editReliefOverride(${override.id})">✏️ Edit</button>
                    <button class="btn-sm btn-danger" onclick="deleteReliefOverride(${override.id})">🗑️</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Load employees for override selection
 */
async function loadEmployeesForOverrides() {
    try {
        const response = await fetch('/api/employees');
        const data = await response.json();
        
        if (data.success && data.data) {
            employeesList = data.data;
            populateEmployeeDropdown();
        }
    } catch (error) {
        console.error('Error loading employees:', error);
    }
}

/**
 * Populate employee dropdown in override modal
 */
function populateEmployeeDropdown() {
    const select = document.getElementById('overrideEmployeeId');
    if (!select) return;
    
    let html = '<option value="">Select Employee</option>';
    employeesList.forEach(emp => {
        html += `<option value="${emp.employee_id || emp.id}">${emp.full_name} (${emp.employee_id || emp.email})</option>`;
    });
    select.innerHTML = html;
    
    // Also populate relief categories
    const catSelect = document.getElementById('overrideReliefCategory');
    if (catSelect) {
        let catHtml = '<option value="">Select Relief Category</option>';
        TAX_RELIEF_CATEGORIES.forEach(cat => {
            catHtml += `<option value="${cat.id}">${cat.name}</option>`;
        });
        catSelect.innerHTML = catHtml;
    }
}

/**
 * Add relief override - show modal
 */
function addReliefOverride() {
    document.getElementById('reliefOverrideModalTitle').textContent = 'Add Relief Override';
    document.getElementById('reliefOverrideId').value = '';
    document.getElementById('reliefOverrideForm').reset();
    document.getElementById('overrideYear').value = new Date().getFullYear();
    populateEmployeeDropdown();
    showModal('reliefOverrideModal');
}

/**
 * Edit relief override - show modal with data
 */
async function editReliefOverride(overrideId) {
    const override = currentOverrides.find(o => o.id === overrideId);
    
    if (!override) {
        alert('Override not found');
        return;
    }
    
    document.getElementById('reliefOverrideModalTitle').textContent = 'Edit Relief Override';
    document.getElementById('reliefOverrideId').value = overrideId;
    populateEmployeeDropdown();
    
    // Set form values
    document.getElementById('overrideEmployeeId').value = override.employee_id;
    document.getElementById('overrideReliefCategory').value = override.relief_code || override.relief_category;
    document.getElementById('overrideAmount').value = override.override_amount;
    document.getElementById('overrideYear').value = override.effective_year || new Date().getFullYear();
    document.getElementById('overrideReason').value = override.reason || '';
    
    showModal('reliefOverrideModal');
}

/**
 * Delete relief override
 */
async function deleteReliefOverride(overrideId) {
    if (!confirm('Are you sure you want to delete this relief override?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/lhdn/relief-overrides/${overrideId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Relief override deleted successfully', 'success');
            loadReliefOverridesFromAPI();
        } else {
            showMessage('Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error deleting relief override:', error);
        showMessage('Error deleting relief override', 'error');
    }
}

/**
 * Save relief override (add or update)
 */
document.getElementById('reliefOverrideForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const overrideId = document.getElementById('reliefOverrideId').value;
    const employeeId = document.getElementById('overrideEmployeeId').value;
    const reliefCategory = document.getElementById('overrideReliefCategory').value;
    const amount = parseFloat(document.getElementById('overrideAmount').value);
    const year = parseInt(document.getElementById('overrideYear').value);
    const reason = document.getElementById('overrideReason').value;
    
    const overrideData = {
        employee_id: employeeId,
        relief_code: reliefCategory,
        override_amount: amount,
        effective_year: year,
        reason: reason
    };
    
    try {
        let response;
        if (overrideId) {
            // Update existing
            response = await fetch(`/api/admin/lhdn/relief-overrides/${overrideId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(overrideData)
            });
        } else {
            // Create new
            response = await fetch('/api/admin/lhdn/relief-overrides', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(overrideData)
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            showMessageInModal('reliefOverrideMessage', 'Relief override saved successfully!', 'success');
            setTimeout(() => {
                closeReliefOverrideModal();
                loadReliefOverridesFromAPI();
            }, 1500);
        } else {
            showMessageInModal('reliefOverrideMessage', 'Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error saving relief override:', error);
        showMessageInModal('reliefOverrideMessage', 'Error saving relief override', 'error');
    }
});

/**
 * Close relief override modal
 */
function closeReliefOverrideModal() {
    hideModal('reliefOverrideModal');
    document.getElementById('reliefOverrideForm').reset();
    document.getElementById('reliefOverrideMessage').style.display = 'none';
}

/**
 * Utility Functions
 */

function formatMoney(value) {
    return parseFloat(value).toLocaleString('en-MY', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function showMessage(message, type) {
    // Show toast or alert message
    alert(message);
}

function showMessageInModal(messageId, message, type) {
    const msgDiv = document.getElementById(messageId);
    if (msgDiv) {
        msgDiv.textContent = message;
        msgDiv.style.display = 'block';
        msgDiv.style.padding = '10px';
        msgDiv.style.borderRadius = '5px';
        msgDiv.style.background = type === 'success' ? '#d4edda' : '#f8d7da';
        msgDiv.style.color = type === 'success' ? '#155724' : '#721c24';
        msgDiv.style.border = type === 'success' ? '1px solid #c3e6cb' : '1px solid #f5c6cb';
    }
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Make functions globally available
window.loadTaxRatesFromAPI = loadTaxRatesFromAPI;
window.loadReliefMaximumsFromAPI = loadReliefMaximumsFromAPI;
window.loadReliefOverridesFromAPI = loadReliefOverridesFromAPI;
window.addTaxBracket = addTaxBracket;
window.editTaxBracket = editTaxBracket;
window.deleteTaxBracket = deleteTaxBracket;
window.closeTaxBracketModal = closeTaxBracketModal;
window.editRelief = editRelief;
window.editAllReliefs = editAllReliefs;
window.closeReliefEditModal = closeReliefEditModal;
window.addReliefOverride = addReliefOverride;
window.editReliefOverride = editReliefOverride;
window.deleteReliefOverride = deleteReliefOverride;
window.closeReliefOverrideModal = closeReliefOverrideModal;
window.formatMoney = formatMoney;
