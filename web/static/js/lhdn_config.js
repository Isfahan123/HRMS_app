/**
 * LHDN Tax Configuration Management - Complete Implementation
 * Matching Python GUI functionality with full CRUD operations
 */

// Malaysian Tax Rates for Residents (LHDN 2025 rates - matching Python GUI)
const RESIDENT_TAX_RATES = [
    { from: 0, to: 5000, rate: 0, taxOnBand: 0, onFirst: 0, next: 0, taxFirst: 0, taxNext: 0 },
    { from: 5001, to: 20000, rate: 1, taxOnBand: 150, onFirst: 5000, next: 15000, taxFirst: 0, taxNext: 150 },
    { from: 20001, to: 35000, rate: 3, taxOnBand: 450, onFirst: 20000, next: 15000, taxFirst: 150, taxNext: 450 },
    { from: 35001, to: 50000, rate: 6, taxOnBand: 900, onFirst: 35000, next: 15000, taxFirst: 600, taxNext: 900 },
    { from: 50001, to: 70000, rate: 11, taxOnBand: 2200, onFirst: 50000, next: 20000, taxFirst: 1500, taxNext: 2200 },
    { from: 70001, to: 100000, rate: 19, taxOnBand: 5700, onFirst: 70000, next: 30000, taxFirst: 3700, taxNext: 5700 },
    { from: 100001, to: 400000, rate: 25, taxOnBand: 75000, onFirst: 100000, next: 300000, taxFirst: 9400, taxNext: 75000 },
    { from: 400001, to: 600000, rate: 26, taxOnBand: 52000, onFirst: 400000, next: 200000, taxFirst: 84400, taxNext: 52000 },
    { from: 600001, to: 2000000, rate: 28, taxOnBand: 392000, onFirst: 600000, next: 1400000, taxFirst: 136400, taxNext: 392000 },
    { from: 2000001, to: 999999999, rate: 30, taxOnBand: 0, onFirst: 2000000, next: 0, taxFirst: 528400, taxNext: 0 }
];

// Special tax provisions (matching Python GUI)
const TAX_PROVISIONS = {
    individualTaxRebate: 400.0,       // LHDN 2025: RM 400
    rebateThreshold: 35000,           // Annual chargeable income threshold
    nonResidentRate: 30.0             // Flat 30% for non-residents
};

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

// Initialize LHDN configuration
function initLHDNConfig() {
    // Check if LHDN tab exists
    const lhdnTab = document.getElementById('payrollLHDNSubtab');
    if (!lhdnTab) {
        console.warn('LHDN tab not found, scheduling retry...');
        setTimeout(initLHDNConfig, 100);
        return;
    }
    
    console.log('Initializing LHDN Configuration...');
    
    // Load tax rates from API
    loadTaxRatesFromAPI();
    
    // Load relief maximums from API
    loadReliefMaximumsFromAPI();
    
    // Load relief overrides from API
    loadReliefOverridesFromAPI();
}

// Initialize immediately since script loads at bottom of page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLHDNConfig);
} else {
    // DOM already loaded
    initLHDNConfig();
}

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
 * Relief Item & Group Overrides (matches Python GUI)
 * Allows overriding item caps, pcb_only flags, cycle_years, and group caps
 */

// Store original data and current overrides
let reliefItemsData = [];
let reliefGroupsData = [];
let itemOverrides = {};
let groupOverrides = {};

// Load relief overrides (both items and groups)
async function loadReliefOverridesFromAPI() {
    try {
        // Load item overrides
        const itemResponse = await fetch('/api/admin/lhdn/relief-item-overrides');
        const itemData = await itemResponse.json();
        
        if (itemData.success) {
            itemOverrides = {};
            (itemData.data || []).forEach(item => {
                itemOverrides[item.item_key] = item;
            });
        }
        
        // Load group overrides
        const groupResponse = await fetch('/api/admin/lhdn/relief-group-overrides');
        const groupData = await groupResponse.json();
        
        if (groupData.success) {
            groupOverrides = {};
            (groupData.data || []).forEach(grp => {
                groupOverrides[grp.group_id] = grp;
            });
        }
        
        // Load relief catalog and populate tables
        await loadReliefCatalog();
        populateReliefGroupTable();
        populateReliefItemTable();
        
        document.getElementById('reliefOverrideStatus').textContent = 
            `Loaded ${Object.keys(itemOverrides).length} item overrides, ${Object.keys(groupOverrides).length} group overrides.`;
    } catch (error) {
        console.error('Error loading relief overrides:', error);
        document.getElementById('reliefOverrideStatus').textContent = '⚠ Unable to load overrides: ' + error.message;
    }
}

// Load relief catalog from the tp1-reliefs.js data
async function loadReliefCatalog() {
    // Use the TP1_ITEMS and RELIEF_GROUPS from tp1-reliefs.js if available
    if (typeof TP1_ITEMS !== 'undefined') {
        reliefItemsData = TP1_ITEMS;
    }
    if (typeof RELIEF_GROUPS !== 'undefined') {
        reliefGroupsData = Object.values(RELIEF_GROUPS);
    }
}

// Populate relief group table
function populateReliefGroupTable() {
    const tbody = document.getElementById('reliefGroupBody');
    if (!tbody) return;
    
    let html = '';
    reliefGroupsData.forEach(group => {
        const defaultCap = group.cap || '';
        const override = groupOverrides[group.id];
        const overrideCap = override ? override.cap : '';
        const effectiveCap = overrideCap || defaultCap;
        
        // Color coding
        let bgColor = '#e0e0e0'; // inherit
        if (overrideCap) {
            if (defaultCap && parseFloat(overrideCap) > parseFloat(defaultCap)) {
                bgColor = '#d0f5d0'; // higher
            } else if (defaultCap && parseFloat(overrideCap) < parseFloat(defaultCap)) {
                bgColor = '#ffe9b3'; // lower
            }
        }
        
        html += `
            <tr>
                <td style="padding: 8px;">${group.id}</td>
                <td style="padding: 8px;">${group.description}</td>
                <td style="padding: 8px; text-align: right;">${defaultCap ? formatMoney(defaultCap) : '-'}</td>
                <td style="padding: 8px;">
                    <input type="number" 
                           id="group_${group.id}" 
                           value="${overrideCap}" 
                           placeholder="(inherit)"
                           step="0.01" 
                           min="0"
                           style="width: 120px; padding: 4px;"
                           onchange="updateGroupEffective('${group.id}')">
                </td>
                <td style="padding: 8px; text-align: right; background: ${bgColor};" id="eff_group_${group.id}">
                    ${effectiveCap ? formatMoney(effectiveCap) : '-'}
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="5" style="padding: 15px; text-align: center;">No groups defined</td></tr>';
}

// Populate relief item table
function populateReliefItemTable() {
    const tbody = document.getElementById('reliefItemBody');
    if (!tbody) return;
    
    let html = '';
    reliefItemsData.forEach(item => {
        const override = itemOverrides[item.key];
        const defaultCap = item.cap || '';
        const overrideCap = override && override.cap !== null ? override.cap : '';
        const effectiveCap = overrideCap || defaultCap;
        
        const defaultCycle = item.cycleYears || '';
        const overrideCycle = override && override.cycle_years !== null ? override.cycle_years : '';
        
        const pcbOnly = override && override.pcb_only !== null ? override.pcb_only : (item.pcbOnly ? true : null);
        const pcbChecked = pcbOnly === true ? 'checked' : '';
        const pcbIndeterminate = pcbOnly === null ? 'indeterminate' : '';
        
        // Color coding
        let bgColor = '#e0e0e0'; // inherit
        if (overrideCap) {
            if (defaultCap && parseFloat(overrideCap) > parseFloat(defaultCap)) {
                bgColor = '#d0f5d0'; // higher
            } else if (defaultCap && parseFloat(overrideCap) < parseFloat(defaultCap)) {
                bgColor = '#ffe9b3'; // lower
            }
        }
        if (pcbOnly === true) {
            // Mix with PCB blue
            bgColor = '#d0e8ff';
        }
        
        html += `
            <tr class="relief-item-row" data-key="${item.key}" data-code="${item.code}" data-desc="${item.description.toLowerCase()}" onclick="selectReliefRow(this)">
                <td style="padding: 8px;">${item.code}</td>
                <td style="padding: 8px;">${item.key}</td>
                <td style="padding: 8px;">${item.description}</td>
                <td style="padding: 8px; text-align: right;">${defaultCap ? formatMoney(defaultCap) : '-'}</td>
                <td style="padding: 8px;">
                    <input type="number" 
                           id="cap_${item.key}" 
                           value="${overrideCap}" 
                           placeholder="(inherit)"
                           step="0.01" 
                           min="0"
                           style="width: 100px; padding: 4px;"
                           onchange="updateItemEffective('${item.key}')"
                           onfocus="selectReliefRow(this.closest('tr'))">
                </td>
                <td style="padding: 8px; text-align: right; background: ${bgColor};" id="eff_${item.key}">
                    ${effectiveCap ? formatMoney(effectiveCap) : '-'}
                </td>
                <td style="padding: 8px; text-align: center;">
                    <input type="checkbox" 
                           id="pcb_${item.key}" 
                           ${pcbChecked}
                           ${pcbIndeterminate}
                           onchange="updateItemEffective('${item.key}')"
                           onfocus="selectReliefRow(this.closest('tr'))">
                </td>
                <td style="padding: 8px; text-align: right;">${defaultCycle || '-'}</td>
                <td style="padding: 8px;">
                    <input type="number" 
                           id="cycle_${item.key}" 
                           value="${overrideCycle}" 
                           placeholder="(inherit)"
                           step="1" 
                           min="0"
                           style="width: 80px; padding: 4px;"
                           onfocus="selectReliefRow(this.closest('tr'))">
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="9" style="padding: 15px; text-align: center;">No items defined</td></tr>';
    
    // Setup filter
    setupReliefFilter();
}

// Update group effective cap when override changes
function updateGroupEffective(groupId) {
    const input = document.getElementById(`group_${groupId}`);
    const effCell = document.getElementById(`eff_group_${groupId}`);
    if (!input || !effCell) return;
    
    const group = reliefGroupsData.find(g => g.id === groupId);
    const defaultCap = group ? group.cap : null;
    const overrideVal = input.value.trim();
    const effective = overrideVal || defaultCap;
    
    effCell.textContent = effective ? formatMoney(effective) : '-';
    
    // Color coding
    let bgColor = '#e0e0e0';
    if (overrideVal) {
        if (defaultCap && parseFloat(overrideVal) > parseFloat(defaultCap)) {
            bgColor = '#d0f5d0';
        } else if (defaultCap && parseFloat(overrideVal) < parseFloat(defaultCap)) {
            bgColor = '#ffe9b3';
        }
    }
    effCell.style.background = bgColor;
}

// Update item effective cap when override changes
function updateItemEffective(itemKey) {
    const capInput = document.getElementById(`cap_${itemKey}`);
    const pcbInput = document.getElementById(`pcb_${itemKey}`);
    const effCell = document.getElementById(`eff_${itemKey}`);
    if (!capInput || !effCell) return;
    
    const item = reliefItemsData.find(i => i.key === itemKey);
    const defaultCap = item ? item.cap : null;
    const overrideVal = capInput.value.trim();
    const effective = overrideVal || defaultCap;
    
    effCell.textContent = effective ? formatMoney(effective) : '-';
    
    // Color coding
    let bgColor = '#e0e0e0';
    if (overrideVal) {
        if (defaultCap && parseFloat(overrideVal) > parseFloat(defaultCap)) {
            bgColor = '#d0f5d0';
        } else if (defaultCap && parseFloat(overrideVal) < parseFloat(defaultCap)) {
            bgColor = '#ffe9b3';
        }
    }
    if (pcbInput && pcbInput.checked) {
        bgColor = '#d0e8ff';
    }
    effCell.style.background = bgColor;
}

// Setup filter functionality
function setupReliefFilter() {
    const filterInput = document.getElementById('reliefOverrideFilter');
    const onlyOverriddenCheckbox = document.getElementById('reliefOverrideOnlyOverridden');
    
    if (filterInput) {
        filterInput.addEventListener('input', applyReliefFilter);
    }
    if (onlyOverriddenCheckbox) {
        onlyOverriddenCheckbox.addEventListener('change', applyReliefFilter);
    }
}

// Apply filter to relief items
function applyReliefFilter() {
    const filterText = document.getElementById('reliefOverrideFilter')?.value.toLowerCase() || '';
    const onlyOverridden = document.getElementById('reliefOverrideOnlyOverridden')?.checked || false;
    
    document.querySelectorAll('.relief-item-row').forEach(row => {
        const code = row.dataset.code.toLowerCase();
        const key = row.dataset.key.toLowerCase();
        const desc = row.dataset.desc;
        
        const matchesFilter = !filterText || code.includes(filterText) || key.includes(filterText) || desc.includes(filterText);
        
        let matchesOverridden = true;
        if (onlyOverridden) {
            const itemKey = row.dataset.key;
            const capInput = document.getElementById(`cap_${itemKey}`);
            const pcbInput = document.getElementById(`pcb_${itemKey}`);
            const cycleInput = document.getElementById(`cycle_${itemKey}`);
            
            matchesOverridden = (capInput && capInput.value.trim()) || 
                               (pcbInput && (pcbInput.checked || pcbInput.indeterminate === false)) || 
                               (cycleInput && cycleInput.value.trim());
        }
        
        row.style.display = (matchesFilter && matchesOverridden) ? '' : 'none';
    });
}

// Save all relief overrides
async function saveReliefOverrides() {
    try {
        let saved = 0;
        
        // Save group overrides
        for (const group of reliefGroupsData) {
            const input = document.getElementById(`group_${group.id}`);
            if (!input) continue;
            
            const value = input.value.trim();
            if (value) {
                const response = await fetch('/api/admin/lhdn/relief-group-overrides', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        group_id: group.id,
                        cap: parseFloat(value)
                    })
                });
                if (response.ok) saved++;
            } else if (groupOverrides[group.id]) {
                // Delete if cleared
                await fetch(`/api/admin/lhdn/relief-group-overrides/${group.id}`, {
                    method: 'DELETE'
                });
                saved++;
            }
        }
        
        // Save item overrides
        for (const item of reliefItemsData) {
            const capInput = document.getElementById(`cap_${item.key}`);
            const pcbInput = document.getElementById(`pcb_${item.key}`);
            const cycleInput = document.getElementById(`cycle_${item.key}`);
            
            const capValue = capInput?.value.trim();
            const pcbValue = pcbInput ? (pcbInput.checked ? true : (pcbInput.indeterminate === true ? null : false)) : null;
            const cycleValue = cycleInput?.value.trim();
            
            // Check if there are actual overrides to save
            const hasCapOverride = capValue && !isNaN(parseFloat(capValue));
            const hasPcbOverride = pcbValue !== null && pcbValue !== false;
            const hasCycleOverride = cycleValue && !isNaN(parseInt(cycleValue));
            
            if (hasCapOverride || hasPcbOverride || hasCycleOverride) {
                const payload = { item_key: item.key };
                if (hasCapOverride) {
                    const parsedCap = parseFloat(capValue);
                    if (!isNaN(parsedCap) && parsedCap >= 0) {
                        payload.cap = parsedCap;
                    }
                }
                if (hasPcbOverride) {
                    payload.pcb_only = pcbValue;
                }
                if (hasCycleOverride) {
                    const parsedCycle = parseInt(cycleValue);
                    if (!isNaN(parsedCycle) && parsedCycle > 0) {
                        payload.cycle_years = parsedCycle;
                    }
                }
                
                const response = await fetch('/api/admin/lhdn/relief-item-overrides', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) saved++;
            } else if (itemOverrides[item.key]) {
                // Delete if all cleared
                await fetch(`/api/admin/lhdn/relief-item-overrides/${item.key}`, {
                    method: 'DELETE'
                });
                saved++;
            }
        }
        
        showMessage(`Saved ${saved} override(s) successfully`, 'success');
        await loadReliefOverridesFromAPI();
    } catch (error) {
        console.error('Error saving relief overrides:', error);
        showMessage('Error saving overrides: ' + error.message, 'error');
    }
}

// Select a relief row (for visual feedback like Python GUI)
let selectedReliefRow = null;
const SELECTED_ROW_BG_COLOR = '#e3f2fd';

function selectReliefRow(row) {
    // Remove previous selection
    if (selectedReliefRow) {
        selectedReliefRow.style.backgroundColor = '';
    }
    // Highlight new selection
    if (row) {
        row.style.backgroundColor = SELECTED_ROW_BG_COLOR;
        selectedReliefRow = row;
    }
}

// Reload relief overrides
function reloadReliefOverrides() {
    loadReliefOverridesFromAPI();
}

// Clear selected relief override (matches Python GUI)
async function clearSelectedReliefOverride() {
    let itemKey = null;
    
    // Try to get item key from selected row
    if (selectedReliefRow) {
        itemKey = selectedReliefRow.dataset.key;
    }
    
    // If no selected row, try focused element
    if (!itemKey) {
        const focusedElement = document.activeElement;
        if (focusedElement && focusedElement.id) {
            const match = focusedElement.id.match(/^(cap|pcb|cycle)_(.+)$/);
            if (match) {
                itemKey = match[2];
            }
        }
    }
    
    // If still no item key, show error
    if (!itemKey) {
        showMessage('Please select a row first by clicking on it', 'warning');
        return;
    }
    
    // Check if this item has an override
    if (!itemOverrides || !itemOverrides[itemKey]) {
        showMessage(`No override found for item: ${itemKey}`, 'warning');
        return;
    }
    
    if (!confirm(`Clear override for item "${itemKey}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/lhdn/relief-item-overrides/${itemKey}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage(`Cleared override for ${itemKey}`, 'success');
            await loadReliefOverridesFromAPI();
        } else {
            showMessage('Error clearing override', 'error');
        }
    } catch (error) {
        console.error('Error clearing override:', error);
        showMessage('Error clearing override: ' + error.message, 'error');
    }
}

// Clear all relief overrides
async function clearAllReliefOverrides() {
    if (!confirm('Are you sure you want to delete ALL relief overrides (items and groups)?')) {
        return;
    }
    
    try {
        let deleted = 0;
        
        // Delete all item overrides
        for (const itemKey in itemOverrides) {
            await fetch(`/api/admin/lhdn/relief-item-overrides/${itemKey}`, {
                method: 'DELETE'
            });
            deleted++;
        }
        
        // Delete all group overrides
        for (const groupId in groupOverrides) {
            await fetch(`/api/admin/lhdn/relief-group-overrides/${groupId}`, {
                method: 'DELETE'
            });
            deleted++;
        }
        
        showMessage(`Deleted ${deleted} override(s) successfully`, 'success');
        await loadReliefOverridesFromAPI();
    } catch (error) {
        console.error('Error clearing relief overrides:', error);
        showMessage('Error clearing overrides: ' + error.message, 'error');
    }
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
window.saveReliefOverrides = saveReliefOverrides;
window.reloadReliefOverrides = reloadReliefOverrides;
window.clearSelectedReliefOverride = clearSelectedReliefOverride;
window.clearAllReliefOverrides = clearAllReliefOverrides;
window.formatMoney = formatMoney;
