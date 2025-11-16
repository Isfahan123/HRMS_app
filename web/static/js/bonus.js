/**
 * Bonus Management Component for Web Interface
 * Provides bonus management functionality
 */

class BonusManager {
    constructor() {
        this.bonuses = [];
        this.employees = [];
    }

    /**
     * Initialize the bonus manager
     */
    async init() {
        await this.loadEmployees();
        await this.loadBonuses();
        this.renderBonusTable();
        this.setupEventListeners();
    }

    /**
     * Load employees from API
     */
    async loadEmployees() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            if (data.success) {
                this.employees = data.data || [];
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            this.showError('Failed to load employees');
        }
    }

    /**
     * Load bonuses from API
     */
    async loadBonuses() {
        try {
            const response = await fetch('/api/admin/bonuses');
            const data = await response.json();
            
            if (data.success) {
                this.bonuses = data.data || [];
            }
        } catch (error) {
            console.error('Error loading bonuses:', error);
            this.showError('Failed to load bonuses');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add bonus button
        const addBtn = document.getElementById('addBonusBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddBonusModal());
        }

        // Modal close buttons
        const closeModalBtns = document.querySelectorAll('.modal-close');
        closeModalBtns.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Form submission
        const bonusForm = document.getElementById('bonusForm');
        if (bonusForm) {
            bonusForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitBonus();
            });
        }
    }

    /**
     * Render bonus table
     */
    renderBonusTable() {
        const tableBody = document.getElementById('bonusTableBody');
        if (!tableBody) return;

        if (this.bonuses.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 20px;">
                        No bonuses found. Click "Add Bonus" to create one.
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';
        this.bonuses.forEach(bonus => {
            const statusBadge = this.getStatusBadge(bonus.status);
            html += `
                <tr>
                    <td>${bonus.employee_name || '-'}</td>
                    <td>${bonus.bonus_type || '-'}</td>
                    <td>RM ${parseFloat(bonus.amount || 0).toFixed(2)}</td>
                    <td>${bonus.description || '-'}</td>
                    <td>${bonus.pay_period || '-'}</td>
                    <td><span class="badge badge-${statusBadge}">${bonus.status}</span></td>
                    <td>${bonus.approved_by || '-'}</td>
                    <td>
                        <button onclick="bonusManager.editBonus('${bonus.id}')" class="btn-sm btn-secondary">Edit</button>
                        ${bonus.status === 'pending' ? `
                            <button onclick="bonusManager.approveBonus('${bonus.id}')" class="btn-sm btn-success">Approve</button>
                            <button onclick="bonusManager.deleteBonus('${bonus.id}')" class="btn-sm btn-danger">Delete</button>
                        ` : ''}
                    </td>
                </tr>
            `;
        });

        tableBody.innerHTML = html;
        this.renderBonusSummary();
    }

    /**
     * Render bonus summary
     */
    renderBonusSummary() {
        const summary = this.calculateSummary();
        const summaryDiv = document.getElementById('bonusSummary');
        
        if (summaryDiv) {
            summaryDiv.innerHTML = `
                <div class="summary-grid">
                    <div class="summary-card">
                        <h4>Total Bonuses</h4>
                        <p class="summary-value">${summary.total}</p>
                    </div>
                    <div class="summary-card">
                        <h4>Total Amount</h4>
                        <p class="summary-value">RM ${summary.totalAmount.toFixed(2)}</p>
                    </div>
                    <div class="summary-card">
                        <h4>Pending</h4>
                        <p class="summary-value">${summary.pending} (RM ${summary.pendingAmount.toFixed(2)})</p>
                    </div>
                    <div class="summary-card">
                        <h4>Approved</h4>
                        <p class="summary-value">${summary.approved} (RM ${summary.approvedAmount.toFixed(2)})</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Calculate bonus summary
     */
    calculateSummary() {
        const pending = this.bonuses.filter(b => b.status === 'pending');
        const approved = this.bonuses.filter(b => b.status === 'approved');
        
        return {
            total: this.bonuses.length,
            totalAmount: this.bonuses.reduce((sum, b) => sum + parseFloat(b.amount || 0), 0),
            pending: pending.length,
            pendingAmount: pending.reduce((sum, b) => sum + parseFloat(b.amount || 0), 0),
            approved: approved.length,
            approvedAmount: approved.reduce((sum, b) => sum + parseFloat(b.amount || 0), 0)
        };
    }

    /**
     * Get status badge class
     */
    getStatusBadge(status) {
        const badges = {
            'pending': 'warning',
            'approved': 'success',
            'paid': 'info',
            'cancelled': 'danger'
        };
        return badges[status] || 'secondary';
    }

    /**
     * Show add bonus modal
     */
    showAddBonusModal() {
        const modal = document.getElementById('bonusModal');
        if (!modal) return;

        // Reset form
        document.getElementById('bonusForm').reset();
        document.getElementById('bonusId').value = '';
        document.getElementById('modalTitle').textContent = 'Add Bonus';

        // Populate employee dropdown
        this.populateEmployeeDropdown();

        modal.style.display = 'block';
    }

    /**
     * Populate employee dropdown
     */
    populateEmployeeDropdown() {
        const select = document.getElementById('bonusEmployeeId');
        if (!select) return;

        let html = '<option value="">Select Employee</option>';
        this.employees.forEach(emp => {
            html += `<option value="${emp.id}">${emp.full_name} (${emp.employee_id})</option>`;
        });

        select.innerHTML = html;
    }

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('bonusModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Submit bonus
     */
    async submitBonus() {
        const bonusId = document.getElementById('bonusId').value;
        const formData = {
            employee_id: document.getElementById('bonusEmployeeId').value,
            bonus_type: document.getElementById('bonusType').value,
            amount: document.getElementById('bonusAmount').value,
            description: document.getElementById('bonusDescription').value,
            pay_period: document.getElementById('bonusPayPeriod').value
        };

        // Validation
        if (!formData.employee_id || !formData.amount) {
            this.showError('Please fill in all required fields');
            return;
        }

        if (parseFloat(formData.amount) <= 0) {
            this.showError('Bonus amount must be greater than zero');
            return;
        }

        try {
            const url = bonusId ? `/api/admin/bonuses/${bonusId}` : '/api/admin/bonuses';
            const method = bonusId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(bonusId ? 'Bonus updated successfully' : 'Bonus added successfully');
                this.closeModal();
                await this.loadBonuses();
                this.renderBonusTable();
            } else {
                this.showError(data.message || 'Failed to save bonus');
            }
        } catch (error) {
            console.error('Error saving bonus:', error);
            this.showError('Failed to save bonus');
        }
    }

    /**
     * Edit bonus
     */
    async editBonus(bonusId) {
        const bonus = this.bonuses.find(b => b.id === bonusId);
        if (!bonus) return;

        // Populate form
        document.getElementById('bonusId').value = bonus.id;
        document.getElementById('bonusEmployeeId').value = bonus.employee_id;
        document.getElementById('bonusType').value = bonus.bonus_type;
        document.getElementById('bonusAmount').value = bonus.amount;
        document.getElementById('bonusDescription').value = bonus.description;
        document.getElementById('bonusPayPeriod').value = bonus.pay_period;

        document.getElementById('modalTitle').textContent = 'Edit Bonus';
        this.populateEmployeeDropdown();
        
        const modal = document.getElementById('bonusModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    /**
     * Approve bonus
     */
    async approveBonus(bonusId) {
        if (!confirm('Are you sure you want to approve this bonus?')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/bonuses/${bonusId}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Bonus approved successfully');
                await this.loadBonuses();
                this.renderBonusTable();
            } else {
                this.showError(data.message || 'Failed to approve bonus');
            }
        } catch (error) {
            console.error('Error approving bonus:', error);
            this.showError('Failed to approve bonus');
        }
    }

    /**
     * Delete bonus
     */
    async deleteBonus(bonusId) {
        if (!confirm('Are you sure you want to delete this bonus?')) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/bonuses/${bonusId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Bonus deleted successfully');
                await this.loadBonuses();
                this.renderBonusTable();
            } else {
                this.showError(data.message || 'Failed to delete bonus');
            }
        } catch (error) {
            console.error('Error deleting bonus:', error);
            this.showError('Failed to delete bonus');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        alert('Error: ' + message);
        // TODO: Implement better error notification
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        alert(message);
        // TODO: Implement better success notification
    }
}

// Global instance
let bonusManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const bonusContainer = document.getElementById('bonusManagement');
    if (bonusContainer) {
        bonusManager = new BonusManager();
        bonusManager.init();
    }
});
