/**
 * Table Enhancement Utilities
 * Provides sorting, filtering, and search capabilities for tables
 */

class TableEnhancer {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        if (!this.table) {
            console.warn(`Table ${tableId} not found`);
            return;
        }

        this.options = {
            searchable: true,
            sortable: true,
            paginate: false,
            pageSize: 10,
            highlightRows: true,
            ...options
        };

        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';

        this.init();
    }

    init() {
        if (this.options.searchable) {
            this.addSearchBox();
        }

        if (this.options.sortable) {
            this.makeSortable();
        }

        if (this.options.highlightRows) {
            this.addRowHighlight();
        }

        if (this.options.paginate) {
            this.addPagination();
        }
    }

    addSearchBox() {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'table-search-container';
        searchContainer.innerHTML = `
            <input type="text" 
                   class="table-search-input" 
                   placeholder="🔍 Search table..." 
                   id="${this.table.id}_search">
            <span class="table-search-results"></span>
        `;

        this.table.parentNode.insertBefore(searchContainer, this.table);

        const searchInput = document.getElementById(`${this.table.id}_search`);
        const resultsSpan = searchContainer.querySelector('.table-search-results');

        searchInput.addEventListener('input', debounce((e) => {
            this.filterTable(e.target.value, resultsSpan);
        }, 300));
    }

    filterTable(query, resultsSpan) {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        const searchTerm = query.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
                visibleCount++;
                
                // Highlight matching text
                if (searchTerm && this.options.highlightRows) {
                    row.classList.add('table-row-match');
                } else {
                    row.classList.remove('table-row-match');
                }
            } else {
                row.style.display = 'none';
                row.classList.remove('table-row-match');
            }
        });

        // Update results count
        if (resultsSpan) {
            if (searchTerm) {
                resultsSpan.textContent = `${visibleCount} of ${rows.length} results`;
                resultsSpan.style.display = 'inline';
            } else {
                resultsSpan.style.display = 'none';
            }
        }
    }

    makeSortable() {
        const headers = this.table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            // Skip if marked as non-sortable
            if (header.classList.contains('no-sort')) return;

            header.style.cursor = 'pointer';
            header.classList.add('sortable-header');
            
            header.addEventListener('click', () => {
                this.sortTable(index, header);
            });

            // Add sort indicator
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.innerHTML = ' ↕';
            header.appendChild(indicator);
        });
    }

    sortTable(columnIndex, header) {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr:not([style*="display: none"])'));
        
        // Determine sort direction
        if (this.sortColumn === columnIndex) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortDirection = 'asc';
            this.sortColumn = columnIndex;
        }

        // Sort rows
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex]?.textContent.trim() || '';
            const bVal = b.cells[columnIndex]?.textContent.trim() || '';

            // Try to parse as number
            const aNum = parseFloat(aVal.replace(/[^\d.-]/g, ''));
            const bNum = parseFloat(bVal.replace(/[^\d.-]/g, ''));

            let comparison = 0;
            if (!isNaN(aNum) && !isNaN(bNum)) {
                comparison = aNum - bNum;
            } else {
                comparison = aVal.localeCompare(bVal);
            }

            return this.sortDirection === 'asc' ? comparison : -comparison;
        });

        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));

        // Update sort indicators
        this.table.querySelectorAll('.sort-indicator').forEach(indicator => {
            indicator.innerHTML = ' ↕';
            indicator.style.opacity = '0.3';
        });

        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.innerHTML = this.sortDirection === 'asc' ? ' ↑' : ' ↓';
            indicator.style.opacity = '1';
        }

        Toast.info(`Sorted by ${header.textContent.trim()} (${this.sortDirection})`);
    }

    addRowHighlight() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;

        tbody.addEventListener('mouseenter', (e) => {
            if (e.target.tagName === 'TR' || e.target.closest('tr')) {
                const row = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
                row.classList.add('table-row-hover');
            }
        }, true);

        tbody.addEventListener('mouseleave', (e) => {
            if (e.target.tagName === 'TR' || e.target.closest('tr')) {
                const row = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
                row.classList.remove('table-row-hover');
            }
        }, true);
    }

    addPagination() {
        // Future implementation for pagination
        console.log('Pagination not yet implemented');
    }
}

// Add CSS for table enhancements
const tableStyles = document.createElement('style');
tableStyles.textContent = `
    .table-search-container {
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 15px;
        flex-wrap: wrap;
    }

    .table-search-input {
        flex: 1;
        min-width: 250px;
        padding: 10px 15px;
        border: 2px solid #e0e0e0;
        border-radius: 6px;
        font-size: 14px;
        transition: border-color 0.2s;
    }

    .table-search-input:focus {
        outline: none;
        border-color: #3498db;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }

    .table-search-results {
        color: #7f8c8d;
        font-size: 13px;
        display: none;
    }

    .sortable-header {
        -webkit-user-select: none;
        user-select: none;
        transition: background-color 0.2s;
    }

    .sortable-header:hover {
        background-color: rgba(52, 152, 219, 0.1) !important;
    }

    .sort-indicator {
        opacity: 0.3;
        font-size: 12px;
        margin-left: 5px;
        transition: opacity 0.2s;
    }

    .table-row-hover {
        background-color: rgba(52, 152, 219, 0.05) !important;
    }

    .table-row-match {
        background-color: rgba(255, 235, 59, 0.2) !important;
    }

    /* Responsive table wrapper */
    .table-responsive {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    .table-responsive table {
        min-width: 600px;
    }

    /* Better table styling */
    table.enhanced-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
    }

    table.enhanced-table thead {
        background: #f8f9fa;
        border-bottom: 2px solid #dee2e6;
    }

    table.enhanced-table th {
        padding: 12px;
        text-align: left;
        font-weight: 600;
        color: #495057;
        border-bottom: 1px solid #dee2e6;
    }

    table.enhanced-table td {
        padding: 12px;
        border-bottom: 1px solid #f1f3f5;
    }

    table.enhanced-table tbody tr {
        transition: background-color 0.15s;
    }

    table.enhanced-table tbody tr:hover {
        background-color: #f8f9fa;
    }

    /* Zebra striping */
    table.enhanced-table.striped tbody tr:nth-child(even) {
        background-color: #f8f9fa;
    }

    /* Compact table variant */
    table.enhanced-table.compact th,
    table.enhanced-table.compact td {
        padding: 8px;
        font-size: 13px;
    }
`;
document.head.appendChild(tableStyles);

// Auto-enhance tables with data-enhance attribute
document.addEventListener('DOMContentLoaded', () => {
    const tables = document.querySelectorAll('table[data-enhance="true"]');
    tables.forEach(table => {
        new TableEnhancer(table.id, {
            searchable: table.dataset.searchable !== 'false',
            sortable: table.dataset.sortable !== 'false',
            highlightRows: table.dataset.highlight !== 'false'
        });
    });
});

// Export for manual use
window.TableEnhancer = TableEnhancer;

console.log('📊 Table enhancements loaded');
