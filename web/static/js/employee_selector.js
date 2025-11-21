/**
 * Employee Selector Component
 * Reusable modal for selecting employees with search functionality
 * Similar to Python GUI's EmployeeSelectorDialog
 */

class EmployeeSelector {
    constructor() {
        this.selectedEmployee = null;
        this.onSelectCallback = null;
        this.employees = [];
        this.filteredEmployees = [];
        this.createModal();
    }

    createModal() {
        // Create modal HTML
        const modalHTML = `
            <div id="employeeSelectorModal" class="modal" style="display: none;">
                <div class="modal-content" style="max-width: 800px;">
                    <div class="modal-header">
                        <h3>Select Employee</h3>
                        <span class="modal-close" onclick="employeeSelector.close()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <!-- Search Bar -->
                        <div style="margin-bottom: 20px;">
                            <input type="text" 
                                   id="empSelectorSearch" 
                                   placeholder="🔍 Search by name, email, or department..." 
                                   style="width: 100%; padding: 10px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>

                        <!-- Filters -->
                        <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                            <div style="flex: 1; min-width: 200px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Department:</label>
                                <select id="empSelectorDept" style="width: 100%; padding: 8px;">
                                    <option value="">All Departments</option>
                                </select>
                            </div>
                            <div style="flex: 1; min-width: 200px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 500;">Status:</label>
                                <select id="empSelectorStatus" style="width: 100%; padding: 8px;">
                                    <option value="">All Status</option>
                                    <option value="Active">Active</option>
                                    <option value="Inactive">Inactive</option>
                                    <option value="On Leave">On Leave</option>
                                </select>
                            </div>
                        </div>

                        <!-- Employee Table -->
                        <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead style="position: sticky; top: 0; background: #f5f5f5; z-index: 1;">
                                    <tr>
                                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Name</th>
                                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Employee ID</th>
                                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Email</th>
                                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Department</th>
                                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">Action</th>
                                    </tr>
                                </thead>
                                <tbody id="empSelectorTableBody">
                                    <tr>
                                        <td colspan="5" style="text-align: center; padding: 40px; color: #999;">
                                            Loading employees...
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <!-- Summary -->
                        <div id="empSelectorSummary" style="margin-top: 15px; padding: 10px; background: #f0f7ff; border-radius: 4px; color: #1976d2; font-size: 14px;">
                            <strong>0</strong> employees found
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page if not exists
        if (!document.getElementById('employeeSelectorModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('empSelectorSearch');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterEmployees());
        }

        // Department filter
        const deptFilter = document.getElementById('empSelectorDept');
        if (deptFilter) {
            deptFilter.addEventListener('change', () => this.filterEmployees());
        }

        // Status filter
        const statusFilter = document.getElementById('empSelectorStatus');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterEmployees());
        }

        // Close on outside click
        const modal = document.getElementById('employeeSelectorModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close();
                }
            });
        }
    }

    async open(callback) {
        this.onSelectCallback = callback;
        this.selectedEmployee = null;

        // Show modal
        const modal = document.getElementById('employeeSelectorModal');
        if (modal) {
            modal.style.display = 'block';
        }

        // Load employees
        await this.loadEmployees();

        // Focus on search
        setTimeout(() => {
            const searchInput = document.getElementById('empSelectorSearch');
            if (searchInput) searchInput.focus();
        }, 100);
    }

    close() {
        const modal = document.getElementById('employeeSelectorModal');
        if (modal) {
            modal.style.display = 'none';
        }
        
        // Clear search
        const searchInput = document.getElementById('empSelectorSearch');
        if (searchInput) searchInput.value = '';
        
        // Reset filters
        const deptFilter = document.getElementById('empSelectorDept');
        if (deptFilter) deptFilter.value = '';
        
        const statusFilter = document.getElementById('empSelectorStatus');
        if (statusFilter) statusFilter.value = '';
    }

    async loadEmployees() {
        try {
            const response = await fetch('/api/admin/employees');
            if (response.ok) {
                this.employees = await response.json();
                this.populateDepartments();
                this.filterEmployees();
            } else {
                this.showError('Failed to load employees');
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            this.showError('Error loading employees');
        }
    }

    populateDepartments() {
        const deptFilter = document.getElementById('empSelectorDept');
        if (!deptFilter) return;

        // Get unique departments
        const departments = [...new Set(this.employees
            .map(emp => emp.department)
            .filter(dept => dept)
        )].sort();

        // Clear and repopulate
        deptFilter.innerHTML = '<option value="">All Departments</option>';
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            deptFilter.appendChild(option);
        });
    }

    filterEmployees() {
        const searchTerm = document.getElementById('empSelectorSearch')?.value.toLowerCase() || '';
        const deptFilter = document.getElementById('empSelectorDept')?.value || '';
        const statusFilter = document.getElementById('empSelectorStatus')?.value || '';

        this.filteredEmployees = this.employees.filter(emp => {
            // Search filter
            const matchesSearch = !searchTerm || 
                (emp.full_name && emp.full_name.toLowerCase().includes(searchTerm)) ||
                (emp.email && emp.email.toLowerCase().includes(searchTerm)) ||
                (emp.department && emp.department.toLowerCase().includes(searchTerm)) ||
                (emp.employee_id && emp.employee_id.toString().toLowerCase().includes(searchTerm));

            // Department filter
            const matchesDept = !deptFilter || emp.department === deptFilter;

            // Status filter
            const matchesStatus = !statusFilter || emp.status === statusFilter;

            return matchesSearch && matchesDept && matchesStatus;
        });

        this.renderEmployeeTable();
    }

    renderEmployeeTable() {
        const tbody = document.getElementById('empSelectorTableBody');
        const summary = document.getElementById('empSelectorSummary');

        if (!tbody) return;

        if (this.filteredEmployees.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: #999;">
                        No employees found matching your criteria
                    </td>
                </tr>
            `;
            if (summary) {
                summary.innerHTML = '<strong>0</strong> employees found';
            }
            return;
        }

        // Render employees
        tbody.innerHTML = this.filteredEmployees.map(emp => `
            <tr style="border-bottom: 1px solid #eee; cursor: pointer;" 
                onmouseover="this.style.background='#f5f5f5'" 
                onmouseout="this.style.background='white'">
                <td style="padding: 12px;">
                    <strong>${emp.full_name || 'N/A'}</strong>
                    ${emp.position ? `<br><small style="color: #666;">${emp.position}</small>` : ''}
                </td>
                <td style="padding: 12px;">${emp.employee_id || emp.id || 'N/A'}</td>
                <td style="padding: 12px;">${emp.email || 'N/A'}</td>
                <td style="padding: 12px;">${emp.department || 'N/A'}</td>
                <td style="padding: 12px; text-align: center;">
                    <button onclick="employeeSelector.selectEmployee('${emp.id}')" 
                            class="btn-primary" 
                            style="padding: 6px 16px; font-size: 13px;">
                        Select
                    </button>
                </td>
            </tr>
        `).join('');

        // Update summary
        if (summary) {
            summary.innerHTML = `<strong>${this.filteredEmployees.length}</strong> employee${this.filteredEmployees.length !== 1 ? 's' : ''} found`;
        }
    }

    selectEmployee(employeeId) {
        const employee = this.employees.find(emp => emp.id === employeeId);
        if (employee && this.onSelectCallback) {
            this.selectedEmployee = employee;
            this.onSelectCallback(employee);
            this.close();
        }
    }

    showError(message) {
        const tbody = document.getElementById('empSelectorTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: #d32f2f;">
                        ⚠️ ${message}
                    </td>
                </tr>
            `;
        }
    }
}

// Create global instance
const employeeSelector = new EmployeeSelector();
