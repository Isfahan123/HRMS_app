/**
 * LHDN Tax Configuration Management
 * Handles Malaysian tax rates, relief maximums, and employee-specific overrides
 */

// Malaysian Tax Rates for Residents (2024 rates)
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Load tax rates from API
    loadTaxRatesFromAPI();
    
    // Load relief maximums from API
    loadReliefMaximumsFromAPI();
    
    // Load relief overrides from API
    loadReliefOverridesFromAPI();
});

/**
 * Load tax rates from API
 */
async function loadTaxRatesFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/tax-rates');
        const data = await response.json();
        
        if (data.success) {
            // Use API data if available, otherwise fall back to hardcoded
            const residentRates = data.data.resident.length > 0 ? data.data.resident : RESIDENT_TAX_RATES;
            const nonResidentRates = data.data.non_resident.length > 0 ? data.data.non_resident : [];
            
            loadResidentTaxRates(residentRates);
            loadNonResidentTaxRates(nonResidentRates);
        } else {
            // Fall back to hardcoded rates
            loadResidentTaxRates(RESIDENT_TAX_RATES);
            loadNonResidentTaxRates([]);
        }
    } catch (error) {
        console.error('Error loading tax rates from API:', error);
        // Fall back to hardcoded rates
        loadResidentTaxRates(RESIDENT_TAX_RATES);
        loadNonResidentTaxRates([]);
    }
}

/**
 * Load resident tax rates
 */
function loadResidentTaxRates(rates) {
    const tbody = document.getElementById('residentTaxRatesBody');
    if (!tbody) return;
    
    let html = '';
    
    // Handle both API format and hardcoded format
    rates.forEach((bracket, index) => {
        const from = bracket.income_from || bracket.from;
        const to = bracket.income_to || bracket.to;
        const rate = bracket.rate_percent || bracket.rate;
        const taxOnBand = bracket.tax_on_band || bracket.taxOnBand || 0;
        
        const bandAmount = to - from;
        const taxAmount = taxOnBand || (bandAmount * rate / 100).toFixed(2);
        
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">${formatMoney(from)}</td>
                <td style="padding: 10px;">${to > 900000000 ? 'Above' : formatMoney(to)}</td>
                <td style="padding: 10px; text-align: center;"><strong>${rate}%</strong></td>
                <td style="padding: 10px; text-align: right;">${formatMoney(parseFloat(taxAmount))}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editTaxBracket('resident', ${index})">Edit</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="5" style="padding: 15px; text-align: center;">No tax rates configured</td></tr>';
}

/**
 * Load non-resident tax rates
 */
function loadNonResidentTaxRates() {
    const tbody = document.getElementById('nonResidentTaxRatesBody');
    if (!tbody) return;
    
    // Non-residents typically pay flat 30% on employment income
    tbody.innerHTML = `
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px;">0</td>
            <td style="padding: 10px;">Above</td>
            <td style="padding: 10px; text-align: center;"><strong>30%</strong></td>
            <td style="padding: 10px; text-align: right;">Flat rate</td>
            <td style="padding: 10px; text-align: center;">
                <button class="btn-sm btn-secondary" onclick="editTaxBracket('non-resident', 0)">Edit</button>
            </td>
        </tr>
    `;
}

/**
 * Load relief maximums from API
 */
async function loadReliefMaximumsFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/relief-max');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            loadReliefMaximums(data.data);
        } else {
            // Fall back to hardcoded relief categories
            loadReliefMaximums(TAX_RELIEF_CATEGORIES.map(r => ({
                relief_code: r.id,
                relief_name: r.name,
                max_amount: r.max,
                description: r.description
            })));
        }
    } catch (error) {
        console.error('Error loading relief maximums from API:', error);
        // Fall back to hardcoded relief categories
        loadReliefMaximums(TAX_RELIEF_CATEGORIES.map(r => ({
            relief_code: r.id,
            relief_name: r.name,
            max_amount: r.max,
            description: r.description
        })));
    }
}

/**
 * Load relief maximums
 */
function loadReliefMaximums(reliefs) {
    const tbody = document.getElementById('reliefMaxBody');
    if (!tbody) return;
    
    let html = '';
    
    reliefs.forEach(relief => {
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
                    <button class="btn-sm btn-secondary" onclick="editRelief('${code}')">Edit</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html || '<tr><td colspan="3" style="padding: 15px; text-align: center;">No relief maximums configured</td></tr>';
}

/**
 * Load relief overrides from API
 */
async function loadReliefOverridesFromAPI() {
    try {
        const response = await fetch('/api/admin/lhdn/relief-overrides');
        const data = await response.json();
        
        if (data.success) {
            loadReliefOverrides(data.data || []);
        } else {
            loadReliefOverrides([]);
        }
    } catch (error) {
        console.error('Error loading relief overrides from API:', error);
        loadReliefOverrides([]);
    }
}

/**
 * Load relief overrides
 */
function loadReliefOverrides(overrides) {
    const tbody = document.getElementById('reliefOverridesBody');
    if (!tbody) return;
    
    if (overrides.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding: 15px; text-align: center;">No relief overrides configured</td></tr>';
        return;
    }
    
    let html = '';
    
    overrides.forEach(override => {
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">${override.employee_name || override.employee_id}</td>
                <td style="padding: 10px;">${override.employee_id}</td>
                <td style="padding: 10px;">${override.relief_category || override.relief_code}</td>
                <td style="padding: 10px; text-align: right;">RM ${formatMoney(override.override_amount)}</td>
                <td style="padding: 10px;">${override.effective_period}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editReliefOverride(${override.id})">Edit</button>
                    <button class="btn-sm btn-danger" onclick="deleteReliefOverride(${override.id})">Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Sample data for backward compatibility (if needed)
const sampleOverrides = [
        {
            id: 1,
            employee_name: 'John Doe',
            employee_id: 'EMP001',
            relief_category: 'Medical for Parents',
            override_amount: 10000,
            effective_period: '2024',
            reason: 'Special medical expenses'
        }
    ];
    
    if (sampleOverrides.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 15px; text-align: center;">No overrides configured</td></tr>';
        return;
    }
    
    let html = '';
    sampleOverrides.forEach(override => {
        html += `
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">
                    <strong>${override.employee_name}</strong>
                    <br>
                    <small style="color: #666;">${override.employee_id}</small>
                </td>
                <td style="padding: 10px;">${override.relief_category}</td>
                <td style="padding: 10px; text-align: right;"><strong>RM ${formatMoney(override.override_amount)}</strong></td>
                <td style="padding: 10px; text-align: center;">${override.effective_period}</td>
                <td style="padding: 10px; text-align: center;">
                    <button class="btn-sm btn-secondary" onclick="editReliefOverride(${override.id})">Edit</button>
                    <button class="btn-sm btn-danger" onclick="deleteReliefOverride(${override.id})">Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Format money value
 */
function formatMoney(value) {
    return parseFloat(value).toLocaleString('en-MY', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Add tax bracket
 */
function addTaxBracket(type) {
    alert(`Add new ${type} tax bracket\n\nThis would open a modal to add a new tax bracket.`);
}

/**
 * Edit tax bracket
 */
function editTaxBracket(type, index) {
    if (type === 'resident') {
        const bracket = RESIDENT_TAX_RATES[index];
        alert(`Edit Resident Tax Bracket\n\nFrom: RM ${formatMoney(bracket.from)}\nTo: RM ${bracket.to === 999999999 ? 'Above' : formatMoney(bracket.to)}\nRate: ${bracket.rate}%\n\nThis would open a modal to edit the bracket.`);
    } else {
        alert(`Edit Non-Resident Tax Rate\n\nFlat rate: 30%\n\nThis would open a modal to edit the rate.`);
    }
}

/**
 * Edit relief category
 */
function editRelief(reliefId) {
    const relief = TAX_RELIEF_CATEGORIES.find(r => r.id === reliefId);
    if (relief) {
        alert(`Edit Relief: ${relief.name}\n\nCurrent Maximum: RM ${formatMoney(relief.max)}\nDescription: ${relief.description}\n\nThis would open a modal to edit the relief maximum.`);
    }
}

/**
 * Edit all reliefs at once
 */
function editAllReliefs() {
    alert('Edit All Relief Maximums\n\nThis would open a comprehensive form to edit all relief categories at once, useful when tax year changes.');
}

/**
 * Add relief override
 */
function addReliefOverride() {
    alert('Add Relief Override\n\nThis would open a modal to:\n1. Select an employee\n2. Select relief category\n3. Enter override amount\n4. Specify effective period\n5. Add reason/notes');
}

/**
 * Edit relief override
 */
function editReliefOverride(overrideId) {
    alert(`Edit Relief Override ID: ${overrideId}\n\nThis would open a modal with the current override details for editing.`);
}

/**
 * Delete relief override
 */
function deleteReliefOverride(overrideId) {
    if (confirm('Are you sure you want to delete this relief override?')) {
        alert(`Relief override ${overrideId} deleted.\n\nIn production, this would delete from the database and refresh the list.`);
        loadReliefOverrides();
    }
}

/**
 * Calculate PCB tax for a given monthly income
 */
function calculatePCB(monthlyIncome, totalReliefs = 0) {
    const annualIncome = monthlyIncome * 12;
    const chargeableIncome = Math.max(0, annualIncome - totalReliefs);
    
    let totalTax = 0;
    let remainingIncome = chargeableIncome;
    
    for (const bracket of RESIDENT_TAX_RATES) {
        if (remainingIncome <= 0) break;
        
        const bandWidth = bracket.to - bracket.from;
        const taxableInBand = Math.min(remainingIncome, bandWidth);
        const taxOnBand = taxableInBand * bracket.rate / 100;
        
        totalTax += taxOnBand;
        remainingIncome -= taxableInBand;
    }
    
    // Monthly PCB (simplified - actual PCB uses more complex calculations)
    const monthlyPCB = totalTax / 12;
    
    return {
        annualIncome,
        totalReliefs,
        chargeableIncome,
        annualTax: totalTax,
        monthlyPCB: Math.round(monthlyPCB * 100) / 100,
        effectiveRate: (totalTax / annualIncome * 100).toFixed(2)
    };
}

// Make calculation function available globally for testing
window.calculatePCB = calculatePCB;
