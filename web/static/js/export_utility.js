/**
 * Export Utility Component
 * Advanced export functionality for data tables with multiple formats
 */

class ExportUtility {
    constructor() {
        this.supportedFormats = ['csv', 'json', 'excel'];
    }

    /**
     * Export data to CSV format
     */
    exportToCSV(data, filename = 'export.csv', columns = null) {
        if (!data || data.length === 0) {
            alert('No data to export');
            return;
        }

        try {
            // Determine columns
            const headers = columns || Object.keys(data[0]);
            
            // Build CSV content
            let csv = headers.map(h => this.escapeCSVField(h)).join(',') + '\n';
            
            data.forEach(row => {
                const values = headers.map(header => {
                    const value = row[header];
                    return this.escapeCSVField(value);
                });
                csv += values.join(',') + '\n';
            });

            // Create and download file
            this.downloadFile(csv, filename, 'text/csv');
            return true;
        } catch (error) {
            console.error('Error exporting to CSV:', error);
            alert('Failed to export to CSV');
            return false;
        }
    }

    /**
     * Export data to JSON format
     */
    exportToJSON(data, filename = 'export.json', pretty = true) {
        if (!data) {
            alert('No data to export');
            return;
        }

        try {
            const json = pretty ? 
                JSON.stringify(data, null, 2) : 
                JSON.stringify(data);
            
            this.downloadFile(json, filename, 'application/json');
            return true;
        } catch (error) {
            console.error('Error exporting to JSON:', error);
            alert('Failed to export to JSON');
            return false;
        }
    }

    /**
     * Export data to Excel-compatible CSV (with UTF-8 BOM)
     */
    exportToExcel(data, filename = 'export.csv', columns = null) {
        if (!data || data.length === 0) {
            alert('No data to export');
            return;
        }

        try {
            // Determine columns
            const headers = columns || Object.keys(data[0]);
            
            // Build CSV with UTF-8 BOM for Excel
            const BOM = '\uFEFF';
            let csv = BOM + headers.map(h => this.escapeCSVField(h)).join(',') + '\n';
            
            data.forEach(row => {
                const values = headers.map(header => {
                    const value = row[header];
                    return this.escapeCSVField(value);
                });
                csv += values.join(',') + '\n';
            });

            // Create and download file
            this.downloadFile(csv, filename, 'text/csv;charset=utf-8');
            return true;
        } catch (error) {
            console.error('Error exporting to Excel:', error);
            alert('Failed to export to Excel format');
            return false;
        }
    }

    /**
     * Export HTML table to CSV
     */
    exportTableToCSV(tableId, filename = 'table_export.csv') {
        const table = document.getElementById(tableId);
        if (!table) {
            alert('Table not found');
            return;
        }

        try {
            let csv = '';
            const rows = table.querySelectorAll('tr');

            rows.forEach((row, index) => {
                const cells = row.querySelectorAll('th, td');
                const values = [];
                
                cells.forEach(cell => {
                    // Skip columns marked as non-exportable or action columns
                    if (cell.hasAttribute('data-export-exclude') || 
                        cell.textContent.toLowerCase().includes('action')) {
                        return;
                    }
                    
                    let text = cell.textContent.trim();
                    // Remove extra whitespace
                    text = text.replace(/\s+/g, ' ');
                    values.push(this.escapeCSVField(text));
                });
                
                if (values.length > 0) {
                    csv += values.join(',') + '\n';
                }
            });

            this.downloadFile(csv, filename, 'text/csv');
            return true;
        } catch (error) {
            console.error('Error exporting table:', error);
            alert('Failed to export table');
            return false;
        }
    }

    /**
     * Export data with custom formatting
     */
    exportWithTemplate(data, template, filename = 'export.csv') {
        if (!data || data.length === 0) {
            alert('No data to export');
            return;
        }

        try {
            // Template should be an object: { columnName: { label, format } }
            const headers = Object.keys(template);
            
            // Build CSV with custom labels
            let csv = headers.map(h => this.escapeCSVField(template[h].label || h)).join(',') + '\n';
            
            data.forEach(row => {
                const values = headers.map(header => {
                    let value = row[header];
                    
                    // Apply custom formatting
                    if (template[header].format) {
                        value = template[header].format(value, row);
                    }
                    
                    return this.escapeCSVField(value);
                });
                csv += values.join(',') + '\n';
            });

            this.downloadFile(csv, filename, 'text/csv');
            return true;
        } catch (error) {
            console.error('Error exporting with template:', error);
            alert('Failed to export with template');
            return false;
        }
    }

    /**
     * Escape CSV field value
     */
    escapeCSVField(value) {
        if (value === null || value === undefined) {
            return '';
        }

        // Convert to string
        let str = String(value);

        // If field contains comma, quote, or newline, wrap in quotes
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            // Escape quotes by doubling them
            str = str.replace(/"/g, '""');
            return `"${str}"`;
        }

        return str;
    }

    /**
     * Download file
     */
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Format currency for export
     */
    formatCurrency(value) {
        if (value === null || value === undefined || value === '') {
            return '0.00';
        }
        const num = parseFloat(value);
        return isNaN(num) ? '0.00' : num.toFixed(2);
    }

    /**
     * Format date for export
     */
    formatDate(value) {
        if (!value) return '';
        try {
            const date = new Date(value);
            return date.toISOString().split('T')[0]; // YYYY-MM-DD
        } catch (error) {
            return value;
        }
    }

    /**
     * Show export options modal
     */
    showExportModal(data, defaultFilename = 'export', options = {}) {
        // Create modal if doesn't exist
        if (!document.getElementById('exportModal')) {
            this.createExportModal();
        }

        // Store data for export
        this.currentExportData = data;
        this.currentExportOptions = options;

        // Set default filename
        const filenameInput = document.getElementById('exportFilename');
        if (filenameInput) {
            filenameInput.value = defaultFilename;
        }

        // Show modal
        const modal = document.getElementById('exportModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    createExportModal() {
        const modalHTML = `
            <div id="exportModal" class="modal" style="display: none;">
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h3>📤 Export Data</h3>
                        <span class="modal-close" onclick="exportUtility.closeExportModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="exportFilename">Filename:</label>
                            <input type="text" id="exportFilename" value="export" 
                                   style="width: 100%; padding: 8px;">
                        </div>

                        <div class="form-group">
                            <label>Format:</label>
                            <div style="display: flex; gap: 10px; margin-top: 10px;">
                                <button onclick="exportUtility.doExport('csv')" class="btn-primary">
                                    📊 CSV
                                </button>
                                <button onclick="exportUtility.doExport('excel')" class="btn-primary">
                                    📗 Excel
                                </button>
                                <button onclick="exportUtility.doExport('json')" class="btn-secondary">
                                    🔧 JSON
                                </button>
                            </div>
                        </div>

                        <div style="margin-top: 20px; padding: 12px; background: #f0f7ff; border-radius: 4px; font-size: 13px; color: #1976d2;">
                            <strong>Tip:</strong> CSV and Excel formats are best for spreadsheet applications. JSON is useful for data processing.
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Close on outside click
        const modal = document.getElementById('exportModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeExportModal();
                }
            });
        }
    }

    doExport(format) {
        const filename = document.getElementById('exportFilename')?.value || 'export';
        const fullFilename = format === 'json' ? `${filename}.json` : `${filename}.csv`;

        let success = false;
        switch (format) {
            case 'csv':
                success = this.exportToCSV(this.currentExportData, fullFilename, this.currentExportOptions.columns);
                break;
            case 'excel':
                success = this.exportToExcel(this.currentExportData, fullFilename, this.currentExportOptions.columns);
                break;
            case 'json':
                success = this.exportToJSON(this.currentExportData, fullFilename);
                break;
        }

        if (success) {
            this.closeExportModal();
        }
    }

    closeExportModal() {
        const modal = document.getElementById('exportModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentExportData = null;
        this.currentExportOptions = null;
    }
}

// Create global instance
const exportUtility = new ExportUtility();
