/**
 * Help Overlay Component
 * Provides contextual help and keyboard shortcuts
 */

class HelpOverlay {
    constructor() {
        this.overlay = null;
        this.shortcuts = [];
        this.tips = [];
    }

    addShortcut(key, description) {
        this.shortcuts.push({ key, description });
    }

    addTip(title, description) {
        this.tips.push({ title, description });
    }

    show() {
        if (this.overlay) {
            this.overlay.style.display = 'flex';
            return;
        }

        this.overlay = document.createElement('div');
        this.overlay.className = 'help-overlay';
        this.overlay.innerHTML = `
            <div class="help-modal">
                <div class="help-header">
                    <h2>💡 Help & Shortcuts</h2>
                    <button class="help-close" onclick="helpOverlay.hide()">&times;</button>
                </div>
                <div class="help-content">
                    ${this.shortcuts.length > 0 ? this.renderShortcuts() : ''}
                    ${this.tips.length > 0 ? this.renderTips() : ''}
                </div>
            </div>
        `;

        document.body.appendChild(this.overlay);

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.overlay.style.display === 'flex') {
                this.hide();
            }
        });

        // Close on background click
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.hide();
            }
        });
    }

    hide() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
        }
    }

    renderShortcuts() {
        return `
            <div class="help-section">
                <h3>⌨️ Keyboard Shortcuts</h3>
                <div class="shortcuts-grid">
                    ${this.shortcuts.map(s => `
                        <div class="shortcut-item">
                            <kbd>${s.key}</kbd>
                            <span>${s.description}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderTips() {
        return `
            <div class="help-section">
                <h3>💡 Quick Tips</h3>
                <div class="tips-list">
                    ${this.tips.map(t => `
                        <div class="tip-item">
                            <strong>${t.title}:</strong> ${t.description}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
}

// Add CSS for help overlay
const helpStyles = document.createElement('style');
helpStyles.textContent = `
    .help-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease-out;
    }

    .help-modal {
        background: white;
        border-radius: 12px;
        max-width: 800px;
        max-height: 90vh;
        width: 90%;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        animation: slideUp 0.3s ease-out;
    }

    .help-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .help-header h2 {
        margin: 0;
        font-size: 24px;
    }

    .help-close {
        background: none;
        border: none;
        color: white;
        font-size: 32px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
        transition: transform 0.2s;
    }

    .help-close:hover {
        transform: scale(1.2);
    }

    .help-content {
        padding: 30px;
        overflow-y: auto;
        max-height: calc(90vh - 80px);
    }

    .help-section {
        margin-bottom: 30px;
    }

    .help-section:last-child {
        margin-bottom: 0;
    }

    .help-section h3 {
        color: #2c3e50;
        margin-bottom: 15px;
        font-size: 18px;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 8px;
    }

    .shortcuts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
    }

    .shortcut-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 6px;
        border: 1px solid #e9ecef;
    }

    .shortcut-item kbd {
        background: linear-gradient(to bottom, #fff, #e9ecef);
        border: 1px solid #adb5bd;
        border-radius: 4px;
        padding: 4px 8px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        font-weight: 600;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
        min-width: 60px;
        text-align: center;
        color: #495057;
    }

    .shortcut-item span {
        color: #495057;
        font-size: 14px;
    }

    .tips-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .tip-item {
        padding: 12px 16px;
        background: #e3f2fd;
        border-radius: 6px;
        border-left: 4px solid #2196f3;
        font-size: 14px;
        line-height: 1.5;
        color: #1565c0;
    }

    .tip-item strong {
        color: #0d47a1;
    }

    @keyframes slideUp {
        from {
            transform: translateY(50px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    /* Help Button */
    .help-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        transition: transform 0.2s, box-shadow 0.2s;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .help-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }

    .help-button:active {
        transform: translateY(0);
    }

    @media (max-width: 768px) {
        .help-modal {
            width: 95%;
            max-height: 95vh;
        }

        .shortcuts-grid {
            grid-template-columns: 1fr;
        }

        .help-button {
            bottom: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            font-size: 20px;
        }
    }
`;
document.head.appendChild(helpStyles);

// Create global instance
window.helpOverlay = new HelpOverlay();

// Add default shortcuts
helpOverlay.addShortcut('?', 'Show this help dialog');
helpOverlay.addShortcut('Ctrl + S', 'Save current form');
helpOverlay.addShortcut('Esc', 'Close modals and dialogs');
helpOverlay.addShortcut('Tab', 'Navigate between form fields');
helpOverlay.addShortcut('Enter', 'Submit forms');

// Add default tips
helpOverlay.addTip('Navigation', 'Use the tabs at the top to navigate between different sections of the dashboard');
helpOverlay.addTip('Search', 'Most tables have search functionality - look for the search box above tables');
helpOverlay.addTip('Filters', 'Use filters to narrow down data and find what you need quickly');
helpOverlay.addTip('Export', 'Click the "Export CSV" button to download table data for offline use');
helpOverlay.addTip('Tooltips', 'Hover over elements with dotted underlines to see helpful tooltips');
helpOverlay.addTip('Forms', 'Required fields are marked with an asterisk (*). Fill them out before submitting');

// Add help button to page
document.addEventListener('DOMContentLoaded', () => {
    const helpButton = document.createElement('button');
    helpButton.className = 'help-button';
    helpButton.innerHTML = '?';
    helpButton.title = 'Help & Shortcuts (?)';
    helpButton.onclick = () => helpOverlay.show();
    document.body.appendChild(helpButton);

    // Register ? shortcut
    document.addEventListener('keydown', (e) => {
        if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
            // Only trigger if not in an input field
            if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                helpOverlay.show();
            }
        }
    });
});

console.log('💡 Help overlay loaded - Press ? for help');
