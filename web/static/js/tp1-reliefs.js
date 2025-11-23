/**
 * TP1 Tax Relief Management
 * Handles Malaysian tax relief items (Potongan Bulan Semasa)
 * Based on core/tax_relief_catalog.py
 */

// Relief Groups with caps
const RELIEF_GROUPS = {
    'G1_PARENT': { id: 'G1_PARENT', description: 'Parent / grandparent expenses', cap: 8000.0 },
    'G3_SELF_EDU': { id: 'G3_SELF_EDU', description: 'Self education fees', cap: 7000.0 },
    'G4_MEDICAL': { id: 'G4_MEDICAL', description: 'Medical expenses', cap: 10000.0 },
    'G5_LIFESTYLE': { id: 'G5_LIFESTYLE', description: 'Lifestyle', cap: 2500.0 },
    'G6_SPORTS': { id: 'G6_SPORTS', description: 'Additional lifestyle sports', cap: 1000.0 },
    'G11_EPF_LIFE': { id: 'G11_EPF_LIFE', description: 'EPF + Life Insurance combined', cap: 7000.0 }
};

// All TP1 Relief Items (from tax_relief_catalog.py)
const TP1_ITEMS = [
    // 1. Parent / Grandparent (Group G1_PARENT, cap RM8,000)
    { code: '1a', key: 'parent_medical_care', description: 'Medical care/needs for parents/grandparents', group: 'G1_PARENT', groupCap: 8000.0 },
    { code: '1b', key: 'parent_dental', description: 'Dental treatment for parents/grandparents', group: 'G1_PARENT', groupCap: 8000.0 },
    { code: '1c', key: 'parent_full_exam_vaccine', description: 'Full medical examination & vaccination (max RM1,000)', cap: 1000.0, group: 'G1_PARENT', groupCap: 8000.0 },
    
    // 2. Basic support equipment
    { code: '2', key: 'support_equipment_disabled', description: 'Basic support equipment for disabled', cap: 6000.0 },
    
    // 3. Self education (Group G3_SELF_EDU, cap RM7,000)
    { code: '3a', key: 'self_edu_non_pg_professional', description: 'Professional course fees (non-Masters/PhD)', group: 'G3_SELF_EDU', groupCap: 7000.0 },
    { code: '3b', key: 'self_edu_masters_phd', description: 'Masters/PhD course fees', group: 'G3_SELF_EDU', groupCap: 7000.0 },
    { code: '3c', key: 'self_edu_skill_upgrading', description: 'Skills upgrading course (max RM2,000)', cap: 2000.0, group: 'G3_SELF_EDU', groupCap: 7000.0 },
    
    // 4. Medical expenses (Group G4_MEDICAL, cap RM10,000)
    { code: '4a', key: 'medical_serious_disease', description: 'Serious disease treatment (self/spouse/child)', group: 'G4_MEDICAL', groupCap: 10000.0 },
    { code: '4b', key: 'medical_fertility', description: 'Fertility treatment', group: 'G4_MEDICAL', groupCap: 10000.0 },
    { code: '4c', key: 'medical_vaccination', description: 'Vaccination (max RM1,000)', cap: 1000.0, group: 'G4_MEDICAL', groupCap: 10000.0 },
    { code: '4d', key: 'medical_dental', description: 'Dental examination & treatment (max RM1,000)', cap: 1000.0, group: 'G4_MEDICAL', groupCap: 10000.0 },
    { code: '4e', key: 'medical_check_covid_mental_devices', description: 'Check-up/COVID/Mental health/devices (max RM1,000)', cap: 1000.0, group: 'G4_MEDICAL', groupCap: 10000.0 },
    { code: '4f', key: 'medical_learning_disability_child', description: 'Learning disability intervention for child (max RM6,000)', cap: 6000.0, group: 'G4_MEDICAL', groupCap: 10000.0 },
    
    // 5. Lifestyle (Group G5_LIFESTYLE, cap RM2,500)
    { code: '5a', key: 'lifestyle_publications', description: 'Books/journals/magazines', group: 'G5_LIFESTYLE', groupCap: 2500.0 },
    { code: '5b', key: 'lifestyle_devices', description: 'Devices (PC/phone/tablet)', group: 'G5_LIFESTYLE', groupCap: 2500.0 },
    { code: '5c', key: 'lifestyle_internet', description: 'Internet subscription', group: 'G5_LIFESTYLE', groupCap: 2500.0 },
    { code: '5d', key: 'lifestyle_skill_course', description: 'Skills upgrading course fees', group: 'G5_LIFESTYLE', groupCap: 2500.0 },
    
    // 6. Sports (Group G6_SPORTS, cap RM1,000)
    { code: '6a', key: 'sports_equipment', description: 'Sports equipment', group: 'G6_SPORTS', groupCap: 1000.0 },
    { code: '6b', key: 'sports_facility_fees', description: 'Sports facility fees', group: 'G6_SPORTS', groupCap: 1000.0 },
    { code: '6c', key: 'sports_event_registration', description: 'Sports event registration fees', group: 'G6_SPORTS', groupCap: 1000.0 },
    { code: '6d', key: 'sports_gym_membership', description: 'Gym membership / training fees', group: 'G6_SPORTS', groupCap: 1000.0 },
    
    // 7. Breastfeeding equipment (biennial)
    { code: '7', key: 'breastfeeding_equipment', description: 'Breastfeeding equipment (once every 2 years)', cap: 1000.0, cycleYears: 2 },
    
    // 8. Childcare
    { code: '8', key: 'childcare_fees', description: 'Childcare/kindergarten fees (≤6 years)', cap: 3000.0 },
    
    // 9. SSPN (Education savings)
    { code: '9', key: 'sspn_net_savings', description: 'SSPN net savings', cap: 8000.0 },
    
    // 10. Alimony
    { code: '10', key: 'alimony_ex_wife', description: 'Alimony to ex-wife', cap: 4000.0 },
    
    // 11. EPF & Life Insurance (Group G11_EPF_LIFE, cap RM7,000)
    { code: '11a', key: 'epf_voluntary', description: 'Voluntary EPF contributions', group: 'G11_EPF_LIFE', groupCap: 7000.0 },
    { code: '11b', key: 'life_insurance_premium', description: 'Life insurance premiums', group: 'G11_EPF_LIFE', groupCap: 7000.0 },
    
    // 12. Education & Medical Insurance
    { code: '12', key: 'education_medical_insurance', description: 'Education & medical insurance', cap: 3000.0 },
    
    // 13. PRS (Private Retirement Scheme)
    { code: '13', key: 'prs_contributions', description: 'Private Retirement Scheme contributions', cap: 3000.0 },
    
    // 14. SOCSO & EIS (PCB only - doesn't reduce net pay)
    { code: '14', key: 'socso_eis_employee', description: 'SOCSO & EIS employee contributions', pcbOnly: true },
    
    // 15. Domestic tourism
    { code: '15', key: 'domestic_tourism', description: 'Domestic tourism expenses', cap: 1000.0 },
    
    // 16. EV charging facilities
    { code: '16', key: 'ev_charging_facilities', description: 'EV charging facilities (once every 3 years)', cap: 2500.0, cycleYears: 3 }
];

/**
 * TP1 Relief Manager Class
 */
class TP1ReliefManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.employeeId = null;
        this.year = new Date().getFullYear();
        this.month = new Date().getMonth() + 1;
        this.reliefData = {};
        
        if (this.container) {
            this.init();
        }
    }
    
    init() {
        this.render();
        this.attachEventListeners();
    }
    
    setEmployee(employeeId) {
        this.employeeId = employeeId;
        this.loadReliefData();
    }
    
    setYearMonth(year, month) {
        this.year = year;
        this.month = month;
        if (this.employeeId) {
            this.loadReliefData();
        }
    }
    
    render() {
        this.container.innerHTML = `
            <div class="tp1-reliefs-container" style="padding: 20px; background: #f9f9f9; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #667eea;">📋 TP1 Tax Relief Items</h3>
                    <div>
                        <button id="saveTP1Button" class="btn-primary">💾 Save All</button>
                        <button id="clearTP1Button" class="btn-secondary">🗑️ Clear All</button>
                    </div>
                </div>
                
                <div id="tp1GroupSummary" style="margin-bottom: 20px; display: none;">
                    <!-- Group summaries will be displayed here -->
                </div>
                
                <div id="tp1ItemsContainer">
                    <!-- Relief items will be rendered here -->
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 5px; border-left: 4px solid #2196f3;">
                    <strong>💡 Tip:</strong> Enter amounts for applicable relief items. Group caps will be automatically enforced.
                </div>
            </div>
        `;
        
        this.renderItems();
    }
    
    renderItems() {
        const container = document.getElementById('tp1ItemsContainer');
        if (!container) return;
        
        let currentGroup = null;
        let html = '';
        
        TP1_ITEMS.forEach((item, index) => {
            // Check if we need to start a new group
            if (item.group && item.group !== currentGroup) {
                if (currentGroup !== null) {
                    html += '</div></div>'; // Close previous group
                }
                
                const group = RELIEF_GROUPS[item.group];
                currentGroup = item.group;
                
                html += `
                    <div class="relief-group" style="margin-bottom: 20px; border: 2px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                        <div class="relief-group-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 15px;">
                            <strong>${group.description}</strong>
                            <span style="float: right;">Maximum: RM ${group.cap.toLocaleString()}</span>
                            <div style="font-size: 12px; margin-top: 5px; opacity: 0.9;">
                                Used: RM <span id="group_used_${item.group}">0.00</span> | 
                                Remaining: RM <span id="group_remaining_${item.group}">${group.cap.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="relief-group-items" style="padding: 15px;">
                `;
            } else if (!item.group && currentGroup !== null) {
                html += '</div></div>'; // Close previous group
                currentGroup = null;
            }
            
            // Render individual item
            const capInfo = item.cap ? ` (max RM${item.cap.toLocaleString()})` : '';
            const cycleInfo = item.cycleYears ? ` <span style="color: #ff9800; font-size: 11px;">[Once every ${item.cycleYears} years]</span>` : '';
            const pcbOnlyInfo = item.pcbOnly ? ' <span style="color: #2196f3; font-size: 11px;">[PCB only]</span>' : '';
            
            html += `
                <div class="relief-item" style="display: flex; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #f0f0f0;">
                    <div style="min-width: 40px; font-weight: bold; color: #667eea;">${item.code}</div>
                    <div style="flex: 1;">
                        <label for="tp1_${item.key}" style="margin: 0; font-size: 14px;">
                            ${item.description}${capInfo}${cycleInfo}${pcbOnlyInfo}
                        </label>
                    </div>
                    <div style="min-width: 150px;">
                        <input type="number" 
                               id="tp1_${item.key}" 
                               class="tp1-relief-input" 
                               data-key="${item.key}"
                               data-code="${item.code}"
                               data-group="${item.group || ''}"
                               data-cap="${item.cap || 0}"
                               data-group-cap="${item.groupCap || 0}"
                               step="0.01" 
                               min="0"
                               ${item.cap ? `max="${item.cap}"` : ''}
                               placeholder="0.00"
                               value="${this.reliefData[item.key] || ''}"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div style="min-width: 80px; text-align: right; font-size: 13px; color: #666;">
                        RM <span id="display_${item.key}">0.00</span>
                    </div>
                </div>
            `;
        });
        
        // Close last group if exists
        if (currentGroup !== null) {
            html += '</div></div>';
        }
        
        container.innerHTML = html;
        
        // Update displays with loaded data
        this.updateGroupSummaries();
    }
    
    attachEventListeners() {
        // Save button
        const saveBtn = document.getElementById('saveTP1Button');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveReliefData());
        }
        
        // Clear button
        const clearBtn = document.getElementById('clearTP1Button');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearReliefData());
        }
        
        // Input change listeners
        document.querySelectorAll('.tp1-relief-input').forEach(input => {
            input.addEventListener('input', () => {
                this.handleInputChange(input);
            });
        });
    }
    
    handleInputChange(input) {
        const key = input.dataset.key;
        const value = parseFloat(input.value) || 0;
        const cap = parseFloat(input.dataset.cap) || 0;
        const group = input.dataset.group;
        
        // Validate individual cap
        if (cap > 0 && value > cap) {
            input.value = cap;
            showMessage(`Maximum for this item is RM${cap.toLocaleString()}`, 'warning');
        }
        
        // Update display
        const display = document.getElementById(`display_${key}`);
        if (display) {
            display.textContent = (parseFloat(input.value) || 0).toFixed(2);
        }
        
        // Update group summary if applicable
        if (group) {
            this.updateGroupSummary(group);
        }
    }
    
    updateGroupSummary(groupId) {
        const group = RELIEF_GROUPS[groupId];
        if (!group) return;
        
        // Calculate total for this group
        let total = 0;
        document.querySelectorAll(`.tp1-relief-input[data-group="${groupId}"]`).forEach(input => {
            total += parseFloat(input.value) || 0;
        });
        
        // Update display
        const usedSpan = document.getElementById(`group_used_${groupId}`);
        const remainingSpan = document.getElementById(`group_remaining_${groupId}`);
        
        if (usedSpan && remainingSpan) {
            usedSpan.textContent = total.toFixed(2);
            const remaining = Math.max(0, group.cap - total);
            remainingSpan.textContent = remaining.toFixed(2);
            
            // Add warning if over cap
            if (total > group.cap) {
                usedSpan.style.color = '#d32f2f';
                remainingSpan.style.color = '#d32f2f';
                remainingSpan.parentElement.innerHTML += ' <span style="color: #d32f2f; font-size: 11px;">⚠️ OVER CAP</span>';
            } else {
                usedSpan.style.color = 'white';
                remainingSpan.style.color = 'white';
            }
        }
    }
    
    updateGroupSummaries() {
        // Update all groups
        Object.keys(RELIEF_GROUPS).forEach(groupId => {
            this.updateGroupSummary(groupId);
        });
    }
    
    async loadReliefData() {
        if (!this.employeeId) return;
        
        try {
            const response = await fetch(`/api/admin/tp1-reliefs/${this.employeeId}/${this.year}/${this.month}`);
            const result = await response.json();
            
            if (result.success && result.data) {
                this.reliefData = result.data;
                
                // Populate inputs
                Object.keys(this.reliefData).forEach(key => {
                    const input = document.getElementById(`tp1_${key}`);
                    if (input) {
                        input.value = this.reliefData[key];
                        this.handleInputChange(input);
                    }
                });
            }
        } catch (error) {
            console.error('Error loading TP1 relief data:', error);
        }
    }
    
    async saveReliefData() {
        if (!this.employeeId) {
            showMessage('No employee selected', 'error');
            return;
        }
        
        // Collect all relief data
        const data = {};
        document.querySelectorAll('.tp1-relief-input').forEach(input => {
            const value = parseFloat(input.value) || 0;
            if (value > 0) {
                data[input.dataset.key] = value;
            }
        });
        
        try {
            const response = await fetch('/api/admin/tp1-reliefs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    employee_id: this.employeeId,
                    year: this.year,
                    month: this.month,
                    relief_data: data
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showMessage('TP1 relief data saved successfully', 'success');
                this.reliefData = data;
            } else {
                showMessage(result.message || 'Error saving TP1 relief data', 'error');
            }
        } catch (error) {
            console.error('Error saving TP1 relief data:', error);
            showMessage('Error saving TP1 relief data', 'error');
        }
    }
    
    clearReliefData() {
        if (!confirm('Clear all TP1 relief entries?')) return;
        
        document.querySelectorAll('.tp1-relief-input').forEach(input => {
            input.value = '';
            this.handleInputChange(input);
        });
        
        this.reliefData = {};
    }
}

// Global instance
let tp1ReliefManager = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize if container exists
    if (document.getElementById('tp1ReliefsContainer')) {
        tp1ReliefManager = new TP1ReliefManager('tp1ReliefsContainer');
    }
});

// Helper function to show TP1 reliefs modal
function showTP1ReliefsModal(employeeId, year, month) {
    if (!tp1ReliefManager) {
        tp1ReliefManager = new TP1ReliefManager('tp1ReliefsContainer');
    }
    
    tp1ReliefManager.setYearMonth(year || new Date().getFullYear(), month || new Date().getMonth() + 1);
    tp1ReliefManager.setEmployee(employeeId);
    
    document.getElementById('tp1ReliefsModal').style.display = 'block';
}

function closeTP1ReliefsModal() {
    document.getElementById('tp1ReliefsModal').style.display = 'none';
}
