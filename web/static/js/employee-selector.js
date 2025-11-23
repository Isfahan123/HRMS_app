/**
 * Employee Selector Modal Component
 * Provides a reusable modal dialog for searching and selecting employees
 * Usage: const selector = new EmployeeSelector({ onSelect: (employee) => {...} });
 */

class EmployeeSelector {
    constructor(options = {}) {
        this.options = {
            title: options.title || 'Select Employee',
            onSelect: options.onSelect || null,
            filters: options.filters || {}, // e.g., { status: 'active' }
            multiSelect: options.multiSelect || false,
            ...options
        };
        
        this.employees = [];
        this.filteredEmployees = [];
        this.selectedEmployees = [];
        this.modal = null;
        this.searchInput = null;
        this.tableBody = null;
        
        this.createModal();
    }
    
    createModal() {
        // Create modal structure
        this.modal = document.createElement('div');
        this.modal.className = 'modal';
        this.modal.style.cssText = 'display: none;';
        this.modal.id = 'employeeSelectorModal';
        
        this.modal.innerHTML = `
            <div class="modal-content" style="max-width: 900px; max-height: 80vh;">
                <div class="modal-header">
                    <h3>👥 ${this.options.title}</h3>
                    <span class="modal-close" onclick="this.closest('.modal').style.display='none'">&times;</span>
                </div>
                
                <div class="modal-body">
                    <!-- Search Bar -->
                    <div style="margin-bottom: 15px;">
                        <input type="text" 
                               id="employeeSelectorSearch" 
                               placeholder="🔍 Search by name, email, or employee ID..." 
                               style="width: 100%; padding: 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 4px;">
                    </div>
                    
                    <!-- Filters -->
                    <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
                        <select id="employeeSelectorDepartment" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">All Departments</option>
                        </select>
                        <select id="employeeSelectorPosition" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">All Positions</option>
                        </select>
                        <select id="employeeSelectorStatus" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="on_leave">On Leave</option>
                        </select>
                        <button type="button" id="employeeSelectorClearFilters" class="btn-secondary" style="padding: 8px 15px;">
                            🔄 Clear Filters
                        </button>
                    </div>
                    
                    <!-- Results count -->
                    <div style="margin-bottom: 10px; color: #666; font-size: 13px;">
                        Showing <strong id="employeeSelectorCount">0</strong> employees
                    </div>
                    
                    <!-- Employee Table -->
                    <div style="max-height: 400px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 4px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead style="background: #667eea; color: white; position: sticky; top: 0;">
                                <tr>
                                    ${this.options.multiSelect ? '<th style="padding: 10px; text-align: center; width: 50px;">Select</th>' : ''}
                                    <th style="padding: 10px; text-align: left;">Name</th>
                                    <th style="padding: 10px; text-align: left;">Employee ID</th>
                                    <th style="padding: 10px; text-align: left;">Email</th>
                                    <th style="padding: 10px; text-align: left;">Department</th>
                                    <th style="padding: 10px; text-align: left;">Position</th>
                                    ${!this.options.multiSelect ? '<th style="padding: 10px; text-align: center; width: 100px;">Action</th>' : ''}
                                </tr>
                            </thead>
                            <tbody id="employeeSelectorTableBody">
                                <tr><td colspan="6" style="text-align: center; padding: 20px;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
                    <div id="employeeSelectorSelectedInfo" style="color: #666; font-size: 13px;"></div>
                    <div>
                        ${this.options.multiSelect ? '<button type="button" id="employeeSelectorConfirm" class="btn-primary">✓ Confirm Selection</button>' : ''}
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').style.display='none'">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Get references
        this.searchInput = document.getElementById('employeeSelectorSearch');
        this.tableBody = document.getElementById('employeeSelectorTableBody');
        
        // Add event listeners
        this.searchInput.addEventListener('input', () => this.filterEmployees());
        document.getElementById('employeeSelectorDepartment').addEventListener('change', () => this.filterEmployees());
        document.getElementById('employeeSelectorPosition').addEventListener('change', () => this.filterEmployees());
        document.getElementById('employeeSelectorStatus').addEventListener('change', () => this.filterEmployees());
        document.getElementById('employeeSelectorClearFilters').addEventListener('click', () => this.clearFilters());
        
        if (this.options.multiSelect) {
            document.getElementById('employeeSelectorConfirm').addEventListener('click', () => this.confirmSelection());
        }
    }
    
    async show() {
        this.modal.style.display = 'block';
        await this.loadEmployees();
    }
    
    hide() {
        this.modal.style.display = 'none';
    }
    
    async loadEmployees() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            if (data.success && data.data) {
                this.employees = data.data;
                this.filteredEmployees = [...this.employees];
                
                // Populate filter dropdowns
                this.populateFilters();
                
                // Apply initial filters if provided
                this.filterEmployees();
            } else {
                this.tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">No employees found</td></tr>';
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            this.tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #d32f2f;">Error loading employees</td></tr>';
        }
    }
    
    populateFilters() {
        // Get unique departments
        const departments = [...new Set(this.employees.map(e => e.department).filter(d => d))];
        const deptSelect = document.getElementById('employeeSelectorDepartment');
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            deptSelect.appendChild(option);
        });
        
        // Get unique positions
        const positions = [...new Set(this.employees.map(e => e.position).filter(p => p))];
        const posSelect = document.getElementById('employeeSelectorPosition');
        positions.forEach(pos => {
            const option = document.createElement('option');
            option.value = pos;
            option.textContent = pos;
            posSelect.appendChild(option);
        });
    }
    
    filterEmployees() {
        const searchTerm = this.searchInput.value.toLowerCase();
        const department = document.getElementById('employeeSelectorDepartment').value;
        const position = document.getElementById('employeeSelectorPosition').value;
        const status = document.getElementById('employeeSelectorStatus').value;
        
        this.filteredEmployees = this.employees.filter(emp => {
            // Search filter
            const matchesSearch = !searchTerm || 
                (emp.full_name && emp.full_name.toLowerCase().includes(searchTerm)) ||
                (emp.email && emp.email.toLowerCase().includes(searchTerm)) ||
                (emp.employee_id && emp.employee_id.toLowerCase().includes(searchTerm));
            
            // Department filter
            const matchesDepartment = !department || emp.department === department;
            
            // Position filter
            const matchesPosition = !position || emp.position === position;
            
            // Status filter
            const matchesStatus = !status || emp.status === status;
            
            return matchesSearch && matchesDepartment && matchesPosition && matchesStatus;
        });
        
        this.renderEmployees();
    }
    
    renderEmployees() {
        const colspanCount = this.options.multiSelect ? 6 : 6;
        
        if (this.filteredEmployees.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="${colspanCount}" style="text-align: center; padding: 20px; color: #999;">No employees match your search criteria</td></tr>`;
            document.getElementById('employeeSelectorCount').textContent = '0';
            return;
        }
        
        document.getElementById('employeeSelectorCount').textContent = this.filteredEmployees.length;
        
        // Clear tbody
        this.tableBody.innerHTML = '';
        
        // Create rows using DOM methods to avoid XSS
        this.filteredEmployees.forEach((emp, index) => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid #e0e0e0';
            row.onmouseover = () => row.style.background = '#f5f5f5';
            row.onmouseout = () => row.style.background = 'white';
            
            if (this.options.multiSelect) {
                // Checkbox cell
                const checkCell = document.createElement('td');
                checkCell.style.cssText = 'padding: 10px; text-align: center;';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'employee-checkbox';
                checkbox.dataset.employeeId = emp.id;
                checkbox.checked = this.selectedEmployees.some(e => e.id === emp.id);
                checkbox.addEventListener('change', () => {
                    const event = new CustomEvent('employeeToggled', { detail: emp });
                    document.querySelector('#employeeSelectorModal').dispatchEvent(event);
                });
                checkCell.appendChild(checkbox);
                row.appendChild(checkCell);
            } else {
                // Double-click to select
                row.ondblclick = () => {
                    const event = new CustomEvent('employeeSelected', { detail: emp });
                    document.querySelector('#employeeSelectorModal').dispatchEvent(event);
                };
            }
            
            // Name cell
            const nameCell = document.createElement('td');
            nameCell.style.padding = '10px';
            nameCell.textContent = emp.full_name || '-';
            row.appendChild(nameCell);
            
            // Employee ID cell
            const idCell = document.createElement('td');
            idCell.style.padding = '10px';
            idCell.textContent = emp.employee_id || '-';
            row.appendChild(idCell);
            
            // Email cell
            const emailCell = document.createElement('td');
            emailCell.style.padding = '10px';
            const emailSmall = document.createElement('small');
            emailSmall.textContent = emp.email || '-';
            emailCell.appendChild(emailSmall);
            row.appendChild(emailCell);
            
            // Department cell
            const deptCell = document.createElement('td');
            deptCell.style.padding = '10px';
            deptCell.textContent = emp.department || '-';
            row.appendChild(deptCell);
            
            // Position cell
            const posCell = document.createElement('td');
            posCell.style.padding = '10px';
            posCell.textContent = emp.position || '-';
            row.appendChild(posCell);
            
            if (!this.options.multiSelect) {
                // Action button cell
                const actionCell = document.createElement('td');
                actionCell.style.cssText = 'padding: 10px; text-align: center;';
                const selectBtn = document.createElement('button');
                selectBtn.type = 'button';
                selectBtn.className = 'btn-primary btn-sm';
                selectBtn.textContent = 'Select';
                selectBtn.addEventListener('click', () => {
                    const event = new CustomEvent('employeeSelected', { detail: emp });
                    document.querySelector('#employeeSelectorModal').dispatchEvent(event);
                });
                actionCell.appendChild(selectBtn);
                row.appendChild(actionCell);
            }
            
            this.tableBody.appendChild(row);
        });
        
        // Update selected info
        if (this.options.multiSelect) {
            this.updateSelectedInfo();
        }
    }
    
    clearFilters() {
        this.searchInput.value = '';
        document.getElementById('employeeSelectorDepartment').value = '';
        document.getElementById('employeeSelectorPosition').value = '';
        document.getElementById('employeeSelectorStatus').value = '';
        this.filterEmployees();
    }
    
    updateSelectedInfo() {
        const count = this.selectedEmployees.length;
        const info = document.getElementById('employeeSelectorSelectedInfo');
        info.textContent = count > 0 ? `${count} employee(s) selected` : '';
    }
    
    confirmSelection() {
        if (this.selectedEmployees.length > 0 && this.options.onSelect) {
            this.options.onSelect(this.selectedEmployees);
            this.hide();
        }
    }
}

// Add global event listeners for employee selection
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('employeeSelectorModal');
    if (modal) {
        modal.addEventListener('employeeSelected', function(e) {
            const selector = window.currentEmployeeSelector;
            if (selector && selector.options.onSelect) {
                selector.options.onSelect(e.detail);
                selector.hide();
            }
        });
        
        modal.addEventListener('employeeToggled', function(e) {
            const selector = window.currentEmployeeSelector;
            if (selector && selector.options.multiSelect) {
                const emp = e.detail;
                const index = selector.selectedEmployees.findIndex(e => e.id === emp.id);
                if (index === -1) {
                    selector.selectedEmployees.push(emp);
                } else {
                    selector.selectedEmployees.splice(index, 1);
                }
                selector.updateSelectedInfo();
            }
        });
    }
});

// Helper function to create and show employee selector
function showEmployeeSelector(options) {
    if (!window.currentEmployeeSelector) {
        window.currentEmployeeSelector = new EmployeeSelector(options);
    } else {
        window.currentEmployeeSelector.options = { ...window.currentEmployeeSelector.options, ...options };
    }
    window.currentEmployeeSelector.show();
}
